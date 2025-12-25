import uuid
import json
import logging
from typing import AsyncGenerator, List
from ag_ui.core import EventType, BaseEvent, CustomEvent, TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent
from agents.base_agent import BaseAgent
from graphs.canvas_graph import CanvasGraphState, ArtifactV3, ArtifactContentCode, ArtifactContentText
from llm.provider_factory import LLMProviderFactory
from protocols.event_types import CanvasEventType
from cache.artifact_cache import artifact_cache

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
        Stream events for artifact creation/modification or regular text response.
        This is called directly from the API route for proper streaming.
        """
        
        action = state.get("artifactAction", None)
        thread_id = state.get("thread_id")
        artifact_id = state.get("artifact_id")
        
        logger.info(f"CanvasAgent.run started with action: {action}, artifact_id: {artifact_id}")
        logger.debug(f"State keys: {list(state.keys())}")
        
        # Retrieve artifact from cache if artifact_id is provided
        if artifact_id:
            cached_artifact = artifact_cache.get(artifact_id)
            if cached_artifact:
                state["artifact"] = cached_artifact
                logger.info(f"Retrieved artifact from cache: {artifact_id}")
            else:
                logger.warning(f"Artifact ID provided but not found in cache: {artifact_id}")
                # Don't fail - may be creating new artifact
        
        # If no action specified, determine if we should create artifact or just chat
        if action is None:
            # Check if there's selected text - that's always a partial update
            selected_text = state.get("selectedText")
            if selected_text:
                action = "partial_update"
                state["artifactAction"] = "partial_update"
                logger.info("Detected partial update intent from selected text")
            else:
                # Analyze user's intent from message
                messages = state["messages"]
                last_message = messages[-1]["content"] if messages else ""
                
                # Simple heuristic: if user asks to create/generate/write something, treat as artifact
                artifact_intent_keywords = ["create", "generate", "write", "make", "build", "code", "script", "function", "document"]
                should_create_artifact = any(keyword in last_message.lower() for keyword in artifact_intent_keywords)
                
                if should_create_artifact:
                    action = "create"
                    state["artifactAction"] = "create"
                    logger.info("Detected artifact creation intent from user message")
                else:
                    # Respond with regular text message
                    logger.info("No artifact intent detected, responding with text")
                    async for event in self._respond_with_text(state):
                        yield event
                    return
        
        # Process artifact actions
        if action == "partial_update":
            async for event in self._stream_partial_update(state):
                yield event
        elif action == "create":
            async for event in self._create_artifact(state):
                yield event
        elif action == "update":
            async for event in self._update_artifact(state):
                yield event
        elif action == "rewrite":
            async for event in self._rewrite_artifact(state):
                yield event
        else:
            # Unknown action, respond with text
            async for event in self._respond_with_text(state):
                yield event
    
    async def _respond_with_text(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Respond with regular text message (no artifact)"""
        messages = state["messages"]
        message_id = str(uuid.uuid4())
        
        logger.info("Responding with text message (no artifact)")
        
        # Start text message
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text"}
        )
        
        # Stream LLM response
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content:
                yield TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=content
                )
        
        # End text message
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
    
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
        thread_id = state.get("thread_id")
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
        
        # Stream artifact content as TEXT_MESSAGE with artifact metadata
        artifact_content = ""
        artifact_title = "Untitled"
        message_id = str(uuid.uuid4())
        
        # Detect language early for code artifacts
        language = None
        if artifact_type == "code":
            language = self._detect_language(last_message, "")
        
        # Generate artifact_id for caching
        artifact_id = str(uuid.uuid4())
        
        # Emit TEXT_MESSAGE_START with artifact metadata including artifact_id
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={
                "message_type": "artifact",
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,  # Send artifact_id to frontend
                "language": language,
                "title": "Generating artifact..."  # Will update when complete
            }
        )
        
        # Stream artifact content using TEXT_MESSAGE_CONTENT
        async for chunk in self.llm.astream(llm_messages):
            content = chunk.content
            if content:
                artifact_content += content
                yield TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=content
                )
        
        # Extract title from content if possible
        artifact_title = self._extract_title(artifact_content, artifact_type)
        logger.debug(f"Artifact title extracted: {artifact_title}")
        
        # Update language detection for code artifacts with full content
        if artifact_type == "code":
            language = self._detect_language(last_message, artifact_content)
            logger.info(f"Code artifact created - language: {language}, title: {artifact_title}")
        
        # End TEXT_MESSAGE
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        
        # Create artifact structure for state (still needed for internal tracking)
        if artifact_type == "code":
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
        
        # Cache the artifact on server-side
        artifact_cache.store(artifact, thread_id, artifact_id)
        logger.info(f"Artifact cached with ID: {artifact_id}")
        
        # Update state
        state["artifact"] = artifact
        state["artifact_id"] = artifact_id  # Store artifact_id in state
        logger.info(f"Artifact created successfully: {artifact_title} (index: {artifact['currentIndex']})")
    
    async def _update_artifact(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Update specific parts of existing artifact"""
        messages = state["messages"]
        current_artifact = state.get("artifact")
        thread_id = state.get("thread_id")
        artifact_id = state.get("artifact_id")
        logger.info(f"Updating artifact, has existing: {current_artifact is not None}, artifact_id: {artifact_id}")
        
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
        
        # Stream updated content as TEXT_MESSAGE with artifact metadata
        updated_content = ""
        message_id = str(uuid.uuid4())
        
        # Emit TEXT_MESSAGE_START with artifact metadata including artifact_id
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={
                "message_type": "artifact",
                "artifact_type": current_content["type"],
                "artifact_id": artifact_id,  # Send artifact_id to frontend
                "language": current_content.get("language"),
                "title": current_content["title"]
            }
        )
        
        # Stream updated content using TEXT_MESSAGE_CONTENT
        async for chunk in self.llm.astream(llm_messages):
            content = chunk.content
            if content:
                updated_content += content
                yield TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=content
                )
        
        # End TEXT_MESSAGE
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        
        # Create new version for state tracking
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
        
        # Update cache
        if artifact_id:
            artifact_cache.update(artifact_id, updated_artifact)
            logger.info(f"Artifact cache updated: {artifact_id}")
        else:
            # If no artifact_id, create new one and cache
            artifact_id = artifact_cache.store(updated_artifact, thread_id)
            state["artifact_id"] = artifact_id
            logger.info(f"New artifact cached with ID: {artifact_id}")
        
        state["artifact"] = updated_artifact
        logger.info(f"Artifact updated successfully: {current_content['title']} (version: {new_index})")
    
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
    
    def _build_partial_update_prompt(self, state: CanvasGraphState) -> str:
        """Build context-aware prompt for partial content updates"""
        
        artifact = state["artifact"]
        selected_text = state["selectedText"]
        current_content = artifact["contents"][artifact["currentIndex"] - 1]
        
        # Get full content
        full_content = (current_content.get("code") or 
                        current_content.get("fullMarkdown") or "")
        
        selection_start = selected_text["start"]
        selection_end = selected_text["end"]
        
        # Extract context window (e.g., 200 chars before/after)
        context_window = 200
        context_before = full_content[max(0, selection_start - context_window):selection_start]
        context_after = full_content[selection_end:min(len(full_content), selection_end + context_window)]
        
        artifact_type = current_content["type"]
        language = current_content.get("language", "text")
        
        prompt = f"""You are editing a specific section of content in a canvas artifact.

**Task:** Modify ONLY the selected portion based on the user's request.

**Artifact Type:** {artifact_type}
**Language:** {language}

**Context Before Selection:**
```
{context_before}
```

**SELECTED TEXT (to be modified):**
```
{selected_text["text"]}
```

**Context After Selection:**
```
{context_after}
```

**User Request:** {state["messages"][-1]["content"]}

**CRITICAL Instructions:**
1. Return ONLY the modified version of the selected text
2. Maintain the same indentation and formatting style as the original
3. Do NOT include the surrounding context in your response
4. Do NOT regenerate the entire content
5. Focus solely on the user's requested change to the selected section
6. Preserve line breaks and whitespace patterns from the original selection

**Output Format:**
- For code: Return only the modified code block without any markdown code fences
- For text: Return only the modified paragraph/section without extra formatting
- NO explanations, NO surrounding context, ONLY the replacement text
"""
        
        return prompt
    
    async def _stream_partial_update(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Stream partial content update for selected region"""
        
        logger.info("Starting partial content update stream")
        selected_text = state["selectedText"]
        thread_id = state.get("thread_id")
        artifact_id = state.get("artifact_id")
        
        # Build specialized prompt
        system_prompt = self._build_partial_update_prompt(state)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state["messages"][-1]["content"]}
        ]
        
        # Emit start event with artifact_id
        yield CustomEvent(
            event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_START,
            data={
                "artifact_id": artifact_id,  # Include artifact_id
                "selection": {
                    "start": selected_text["start"],
                    "end": selected_text["end"]
                },
                "strategy": "replace"
            }
        )
        
        logger.info(f"Streaming partial update for selection {selected_text['start']}-{selected_text['end']}, artifact_id: {artifact_id}")
        
        # Stream the partial update
        updated_content = ""
        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                updated_content += chunk.content
                
                # Stream chunks to frontend
                yield CustomEvent(
                    event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_CHUNK,
                    data={
                        "chunk": chunk.content,
                        "artifact_id": artifact_id,  # Include artifact_id
                        "selection": {
                            "start": selected_text["start"],
                            "end": selected_text["end"]
                        }
                    }
                )
        
        logger.info(f"Partial update complete, generated {len(updated_content)} characters")
        
        # Emit completion event with full updated section
        yield CustomEvent(
            event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_COMPLETE,
            data={
                "artifact_id": artifact_id,  # Include artifact_id
                "selection": {
                    "start": selected_text["start"],
                    "end": selected_text["end"]
                },
                "updatedContent": updated_content,
                "strategy": "replace"
            }
        )
        
        # Update artifact in state with merged content
        self._merge_partial_update(state, updated_content)
        
        # Update cache
        updated_artifact = state.get("artifact")
        if artifact_id and updated_artifact:
            artifact_cache.update(artifact_id, updated_artifact)
            logger.info(f"Artifact cache updated after partial update: {artifact_id}")
        elif updated_artifact and thread_id:
            # If no artifact_id, create new one
            artifact_id = artifact_cache.store(updated_artifact, thread_id)
            state["artifact_id"] = artifact_id
            logger.info(f"New artifact cached after partial update: {artifact_id}")
        
        logger.info("Artifact state updated with partial change")
    
    def _merge_partial_update(self, state: CanvasGraphState, updated_content: str) -> None:
        """Merge partial update into artifact state"""
        
        artifact = state["artifact"]
        selected_text = state["selectedText"]
        current_content = artifact["contents"][artifact["currentIndex"] - 1]
        
        # Get full content
        full_content = (current_content.get("code") or 
                        current_content.get("fullMarkdown") or "")
        
        # Replace selected region with updated content
        new_content = (
            full_content[:selected_text["start"]] +
            updated_content +
            full_content[selected_text["end"]:]
        )
        
        # Create new version of artifact
        new_index = len(artifact["contents"]) + 1
        
        if current_content["type"] == "code":
            new_content_obj: ArtifactContentCode = {
                "index": new_index,
                "type": "code",
                "title": current_content["title"],
                "code": new_content,
                "language": current_content["language"]
            }
        else:
            new_content_obj: ArtifactContentText = {
                "index": new_index,
                "type": "text",
                "title": current_content["title"],
                "fullMarkdown": new_content
            }
        
        # Update artifact with new version
        updated_artifact: ArtifactV3 = {
            "currentIndex": new_index,
            "contents": [*artifact["contents"], new_content_obj]
        }
        
        state["artifact"] = updated_artifact
        logger.debug(f"Created artifact version {new_index} with partial update merged")
