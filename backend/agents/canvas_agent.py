import uuid
import json
import logging
from typing import AsyncGenerator, List
from ag_ui.core import EventType, BaseEvent, CustomEvent
from agents.base_agent import BaseAgent
from graphs.canvas_graph import CanvasGraphState, ArtifactV3, ArtifactContentCode, ArtifactContentText
from llm.provider_factory import LLMProviderFactory

logger = logging.getLogger(__name__)


class CanvasAgent(BaseAgent):
    """Agent that generates and modifies artifacts"""
    
    def __init__(self, model: str = None):
        """
        Initialize CanvasAgent with optional model parameter
        
        Args:
            model: Model name to use (e.g., "qwen:7b", "qwen:4b")
                   Falls back to default if not provided
        """
        logger.info(f"Initializing CanvasAgent with model: {model or 'default'}")
        provider = LLMProviderFactory.get_provider("ollama", model=model)
        self.llm = provider.get_model()
        logger.debug(f"CanvasAgent initialized successfully with LLM provider")
    
    async def run(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """
        Stream events for artifact creation/modification.
        This is called directly from the API route for proper streaming.
        """
        
        action = state.get("artifactAction", "create")
        logger.info(f"CanvasAgent.run started with action: {action}")
        logger.debug(f"State keys: {list(state.keys())}")
        
        # Emit THINKING event
        yield CustomEvent(
            type=EventType.CUSTOM,
            name="thinking",
            value={"message": f"Processing {action} request..."}
        )
        
        if action == "create":
            async for event in self._create_artifact(state):
                yield event
        elif action == "update":
            async for event in self._update_artifact(state):
                yield event
        elif action == "rewrite":
            async for event in self._rewrite_artifact(state):
                yield event
    
    async def process_sync(self, state: CanvasGraphState) -> CanvasGraphState:
        """
        Synchronous version for LangGraph node execution.
        Returns updated state without streaming events.
        """
        action = state.get("artifactAction", "create")
        logger.info(f"CanvasAgent.process_sync started with action: {action}")
        
        if action == "create":
            result = await self._create_artifact_sync(state)
            logger.debug(f"Artifact created successfully (sync mode)")
            return result
        elif action == "update":
            result = await self._update_artifact_sync(state)
            logger.debug(f"Artifact updated successfully (sync mode)")
            return result
        elif action == "rewrite":
            result = await self._rewrite_artifact_sync(state)
            logger.debug(f"Artifact rewritten successfully (sync mode)")
            return result
        
        logger.warning(f"Unknown action '{action}', returning state unchanged")
        return state
    
    async def _create_artifact(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Generate new artifact from scratch"""
        messages = state["messages"]
        last_message = messages[-1]["content"]
        logger.info(f"Creating new artifact, message length: {len(last_message)}")
        
        # Determine artifact type from context
        artifact_type = self._detect_artifact_type(last_message)
        logger.info(f"Detected artifact type: {artifact_type}")
        
        # Create system prompt for artifact generation
        system_prompt = self._get_creation_prompt(artifact_type)
        
        # Prepare messages for LLM
        llm_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        
        # Stream artifact content
        artifact_content = ""
        artifact_title = "Untitled"
        
        # Emit artifact streaming start
        yield CustomEvent(
            type=EventType.CUSTOM,
            name="artifact_streaming_start",
            value={"artifactType": artifact_type}
        )
        
        async for chunk in self.llm.astream(llm_messages):
            content = chunk.content
            if content:
                artifact_content += content
                # Emit streaming delta
                yield CustomEvent(
                    type=EventType.CUSTOM,
                    name="artifact_streaming",
                    value={
                        "contentDelta": content,
                        "artifactIndex": 1
                    }
                )
        
        # Extract title from content if possible
        artifact_title = self._extract_title(artifact_content, artifact_type)
        logger.debug(f"Artifact title extracted: {artifact_title}")
        
        # Create artifact structure
        if artifact_type == "code":
            language = self._detect_language(last_message, artifact_content)
            logger.info(f"Code artifact created - language: {language}, title: {artifact_title}")
            artifact_content_obj: ArtifactContentCode = {
                "index": 1,
                "type": "code",
                "title": artifact_title,
                "code": artifact_content,
                "language": language
            }
        else:
            artifact_content_obj: ArtifactContentText = {
                "index": 1,
                "type": "text",
                "title": artifact_title,
                "fullMarkdown": artifact_content
            }
        
        artifact: ArtifactV3 = {
            "currentIndex": 1,
            "contents": [artifact_content_obj]
        }
        
        # Update state
        state["artifact"] = artifact
        logger.info(f"Artifact created successfully: {artifact_title} (index: {artifact['currentIndex']})")
        
        # Emit artifact created event
        yield CustomEvent(
            type=EventType.CUSTOM,
            name="artifact_created",
            value={"artifact": artifact}
        )
        
        # Step 2: Stream summary to chat
        async for event in self._stream_summary(artifact_type, artifact_title, "created"):
            yield event
    
    async def _update_artifact(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Update specific parts of existing artifact"""
        messages = state["messages"]
        current_artifact = state.get("artifact")
        logger.info(f"Updating artifact, has existing: {current_artifact is not None}")
        
        if not current_artifact:
            # No artifact to update, create new one
            logger.warning("No existing artifact found, creating new one instead")
            async for event in self._create_artifact(state):
                yield event
            return
        
        last_message = messages[-1]["content"]
        current_content = current_artifact["contents"][-1]
        
        # Get current artifact content
        if current_content["type"] == "code":
            current_text = current_content["code"]
        else:
            current_text = current_content["fullMarkdown"]
        
        # Create system prompt for updating
        system_prompt = self._get_update_prompt(current_content["type"], current_text)
        
        # Prepare messages for LLM
        llm_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        
        # Stream updated content
        updated_content = ""
        
        # Emit artifact streaming start
        yield CustomEvent(
            type=EventType.CUSTOM,
            name="artifact_streaming_start",
            value={"artifactType": current_content["type"], "action": "update"}
        )
        
        async for chunk in self.llm.astream(llm_messages):
            content = chunk.content
            if content:
                updated_content += content
                yield CustomEvent(
                    type=EventType.CUSTOM,
                    name="artifact_streaming",
                    value={
                        "contentDelta": content,
                        "artifactIndex": current_artifact["currentIndex"] + 1
                    }
                )
        
        # Create new version
        new_index = len(current_artifact["contents"]) + 1
        logger.debug(f"Creating new artifact version: {new_index}")
        
        if current_content["type"] == "code":
            new_content_obj: ArtifactContentCode = {
                "index": new_index,
                "type": "code",
                "title": current_content["title"],
                "code": updated_content,
                "language": current_content["language"]
            }
        else:
            new_content_obj: ArtifactContentText = {
                "index": new_index,
                "type": "text",
                "title": current_content["title"],
                "fullMarkdown": updated_content
            }
        
        # Update artifact
        updated_artifact: ArtifactV3 = {
            "currentIndex": new_index,
            "contents": [*current_artifact["contents"], new_content_obj]
        }
        
        state["artifact"] = updated_artifact
        logger.info(f"Artifact updated successfully: {current_content['title']} (version: {new_index})")
        
        # Emit artifact updated event
        yield CustomEvent(
            type=EventType.CUSTOM,
            name="artifact_updated",
            value={"artifact": updated_artifact, "action": "update"}
        )
        
        # Step 2: Stream summary to chat
        async for event in self._stream_summary(current_content["type"], current_content["title"], "updated"):
            yield event
    
    async def _rewrite_artifact(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Rewrite entire artifact with new approach"""
        logger.info("Rewriting artifact from scratch")
        # For rewrite, we treat it similar to create but with context from existing
        async for event in self._create_artifact(state):
            yield event
    
    async def _create_artifact_sync(self, state: CanvasGraphState) -> CanvasGraphState:
        """Create artifact without streaming - for LangGraph node"""
        messages = state["messages"]
        last_message = messages[-1]["content"]
        
        artifact_type = self._detect_artifact_type(last_message)
        system_prompt = self._get_creation_prompt(artifact_type)
        
        llm_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        
        # Get full response (non-streaming)
        response = await self.llm.ainvoke(llm_messages)
        artifact_content = response.content
        
        artifact_title = self._extract_title(artifact_content, artifact_type)
        
        if artifact_type == "code":
            language = self._detect_language(last_message, artifact_content)
            artifact_content_obj: ArtifactContentCode = {
                "index": 1,
                "type": "code",
                "title": artifact_title,
                "code": artifact_content,
                "language": language
            }
        else:
            artifact_content_obj: ArtifactContentText = {
                "index": 1,
                "type": "text",
                "title": artifact_title,
                "fullMarkdown": artifact_content
            }
        
        artifact: ArtifactV3 = {
            "currentIndex": 1,
            "contents": [artifact_content_obj]
        }
        
        state["artifact"] = artifact
        return state
    
    async def _update_artifact_sync(self, state: CanvasGraphState) -> CanvasGraphState:
        """Update artifact without streaming - for LangGraph node"""
        messages = state["messages"]
        current_artifact = state.get("artifact")
        
        if not current_artifact:
            return await self._create_artifact_sync(state)
        
        last_message = messages[-1]["content"]
        current_content = current_artifact["contents"][-1]
        
        if current_content["type"] == "code":
            current_text = current_content["code"]
        else:
            current_text = current_content["fullMarkdown"]
        
        system_prompt = self._get_update_prompt(current_content["type"], current_text)
        
        llm_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        
        response = await self.llm.ainvoke(llm_messages)
        updated_content = response.content
        
        new_index = len(current_artifact["contents"]) + 1
        
        if current_content["type"] == "code":
            new_content_obj: ArtifactContentCode = {
                "index": new_index,
                "type": "code",
                "title": current_content["title"],
                "code": updated_content,
                "language": current_content["language"]
            }
        else:
            new_content_obj: ArtifactContentText = {
                "index": new_index,
                "type": "text",
                "title": current_content["title"],
                "fullMarkdown": updated_content
            }
        
        updated_artifact: ArtifactV3 = {
            "currentIndex": new_index,
            "contents": [*current_artifact["contents"], new_content_obj]
        }
        
        state["artifact"] = updated_artifact
        return state
    
    async def _rewrite_artifact_sync(self, state: CanvasGraphState) -> CanvasGraphState:
        """Rewrite artifact without streaming - for LangGraph node"""
        return await self._create_artifact_sync(state)
    
    def _detect_artifact_type(self, message: str) -> str:
        """Determine if user wants code or text artifact"""
        code_keywords = ["code", "function", "class", "script", "program", "implementation"]
        
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in code_keywords):
            logger.debug(f"Artifact type detected as 'code' based on keywords")
            return "code"
        logger.debug(f"Artifact type detected as 'text' (default)")
        return "text"
    
    def _detect_language(self, message: str, code: str) -> str:
        """Detect programming language from context"""
        message_lower = message.lower()
        
        # Check message for language mentions
        language_map = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js"],
            "typescript": ["typescript", "ts"],
            "java": ["java"],
            "cpp": ["c++", "cpp"],
            "c": ["c"],
            "go": ["go", "golang"],
            "rust": ["rust"],
            "ruby": ["ruby"],
            "php": ["php"],
        }
        
        for lang, keywords in language_map.items():
            if any(keyword in message_lower for keyword in keywords):
                logger.debug(f"Language detected from message: {lang}")
                return lang
        
        # Try to detect from code syntax (basic heuristic)
        if "def " in code or "import " in code:
            logger.debug("Language detected from code syntax: python")
            return "python"
        elif "function" in code or "const" in code or "let" in code:
            logger.debug("Language detected from code syntax: javascript")
            return "javascript"
        elif "public class" in code or "private void" in code:
            logger.debug("Language detected from code syntax: java")
            return "java"
        
        logger.debug("Language detection defaulted to: python")
        return "python"  # Default
    
    def _extract_title(self, content: str, artifact_type: str) -> str:
        """Extract title from artifact content"""
        lines = content.strip().split("\n")
        
        if artifact_type == "code":
            # Look for class or function name
            for line in lines:
                if "class " in line:
                    parts = line.split("class ")
                    if len(parts) > 1:
                        class_name = parts[1].split("(")[0].split(":")[0].strip()
                        return f"Class: {class_name}"
                elif "def " in line:
                    parts = line.split("def ")
                    if len(parts) > 1:
                        func_name = parts[1].split("(")[0].strip()
                        return f"Function: {func_name}"
            return "Code Artifact"
        else:
            # For text, use first heading or first line
            for line in lines:
                if line.startswith("#"):
                    return line.replace("#", "").strip()
            # Use first non-empty line
            for line in lines:
                if line.strip():
                    return line.strip()[:50]
            return "Text Document"
    
    def _get_creation_prompt(self, artifact_type: str) -> str:
        """Get system prompt for artifact creation"""
        if artifact_type == "code":
            return """You are a code generation assistant. Generate clean, well-documented code based on the user's request.
- Write production-quality code with proper error handling
- Include helpful comments
- Follow best practices for the language
- Output ONLY the code, no explanations or markdown formatting"""
        else:
            return """You are a writing assistant. Generate clear, well-structured text based on the user's request.
- Use proper markdown formatting
- Organize content with headings and sections
- Be concise and clear
- Output ONLY the content in markdown format"""
    
    def _get_update_prompt(self, artifact_type: str, current_content: str) -> str:
        """Get system prompt for artifact updates"""
        if artifact_type == "code":
            return f"""You are a code modification assistant. Update the following code based on the user's request.

CURRENT CODE:
```
{current_content}
```

Instructions:
- Make only the requested changes
- Maintain code quality and consistency
- Keep the overall structure unless asked to change it
- Output ONLY the updated code, no explanations"""
        else:
            return f"""You are a text editing assistant. Update the following document based on the user's request.

CURRENT DOCUMENT:
{current_content}

Instructions:
- Make only the requested changes
- Maintain document structure and tone
- Keep existing formatting unless asked to change it
- Output ONLY the updated content in markdown format"""
    
    async def _stream_summary(self, artifact_type: str, artifact_title: str, action: str) -> AsyncGenerator[BaseEvent, None]:
        """Stream a summary message to the chat about the artifact action"""
        from ag_ui.core import TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent
        
        message_id = f"msg-{uuid.uuid4()}"
        
        # Start text message
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant"
        )
        
        # Create summary message
        if action == "created":
            if artifact_type == "code":
                summary = f"I've created a code artifact: **{artifact_title}**. You can see it on the right side. Feel free to ask me to modify it or create something else!"
            else:
                summary = f"I've created a text document: **{artifact_title}**. It's displayed on the right side. Let me know if you'd like any changes!"
        else:  # updated
            if artifact_type == "code":
                summary = f"I've updated the code artifact: **{artifact_title}**. The new version is now displayed. What else would you like me to change?"
            else:
                summary = f"I've updated the document: **{artifact_title}**. You can see the changes on the right side. Anything else?"
        
        # Stream summary in chunks (simulate natural streaming)
        chunk_size = 10
        for i in range(0, len(summary), chunk_size):
            chunk = summary[i:i + chunk_size]
            yield TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=chunk
            )
        
        # End text message
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
