import uuid
import json
import logging
from typing import AsyncGenerator, List
from ag_ui.core import EventType, BaseEvent, CustomEvent, TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent
from agents.base_agent import BaseAgent
from graphs.canvas_graph import CanvasGraphState, Artifact
from llm.provider_factory import LLMProviderFactory
from protocols.event_types import CanvasEventType
from cache.artifact_cache import artifact_cache
from config import settings

logger = logging.getLogger(__name__)


class CanvasAgent(BaseAgent):
    """Agent that generates and modifies artifacts"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize CanvasAgent with optional model and provider parameters
        
        Args:
            model: Model name to use (e.g., "qwen:7b", "gemini-1.5-flash")
                   Falls back to default if not provided
            provider: Provider type ("ollama", "gemini")
                   Falls back to default if not provided
        """
        self.provider_type = provider or settings.DEFAULT_PROVIDER
        self.model_name = model or settings.DEFAULT_MODEL
        
        logger.info(f"Initializing CanvasAgent with provider: {self.provider_type}, model: {self.model_name}")
        
        provider_instance = LLMProviderFactory.get_provider(
            provider_type=self.provider_type,
            model=self.model_name
        )
        self.llm = provider_instance.get_model()
        logger.debug(f"CanvasAgent initialized successfully with LLM provider: {self.provider_type}, model: {self.model_name}")
    
    async def run(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """
        Stream events for artifact creation/modification or regular text response.
        This is called directly from the API route for proper streaming.
        """
        
        action = state.get("artifactAction", None)
        thread_id = state.get("thread_id")
        artifact_id = state.get("artifact_id")
        artifact = state.get("artifact")
        
        logger.info(f"CanvasAgent.run started with action: {action}, artifact_id: {artifact_id}")
        logger.debug(f"State keys: {list(state.keys())}")
        
        # Retrieve artifact from cache if artifact_id is provided
        if not artifact:
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
        
        logger.warning(f"Unknown action '{action}', returning state unchanged")
        return state
    
    async def _create_artifact(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Generate new artifact from scratch"""
        messages = state["messages"]
        last_message = messages[-1]["content"]
        thread_id = state.get("thread_id")
        logger.info(f"Creating new artifact, message length: {len(last_message)}")
        
        # Create system prompt for artifact generation
        system_prompt = self._get_creation_prompt()
        
        # Prepare messages for LLM
        llm_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        
        # Stream artifact content as TEXT_MESSAGE with artifact metadata
        artifact_content = ""
        message_id = str(uuid.uuid4())
        
        # Detect language early for code artifacts
        language = self._detect_language(last_message, "")
        
        # Generate title using LLM before streaming
        artifact_title = await self._generate_title_with_llm(last_message, language)
        logger.debug(f"LLM-generated title: {artifact_title}")
        
        # Generate artifact_id for caching
        artifact_id = str(uuid.uuid4())
        
        # Emit TEXT_MESSAGE_START with artifact metadata including artifact_id and inferred title
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={
                "message_type": "artifact",
                "artifact_id": artifact_id,  # Send artifact_id to frontend
                "language": language,
                "title": artifact_title  # Use inferred title from message
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
        artifact_title = self._extract_title(artifact_content)
        logger.debug(f"Artifact title extracted: {artifact_title}")
        
        # Update language detection with full content
        language = self._detect_language(last_message, artifact_content)
        logger.info(f"Artifact created - language: {language}, title: {artifact_title}")
        
        # End TEXT_MESSAGE
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        
        # Create simplified artifact structure
        artifact: Artifact = {
            "artifact_id": artifact_id,
            "title": artifact_title,
            "content": artifact_content,
            "language": language
        }
        
        # Cache the artifact on server-side
        artifact_cache.store(artifact, thread_id, artifact_id)
        logger.info(f"Artifact cached with ID: {artifact_id}")
        
        # Update state
        state["artifact"] = artifact
        state["artifact_id"] = artifact_id  # Store artifact_id in state
        logger.info(f"Artifact created successfully: {artifact_title}")
    
    async def _update_artifact(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Update existing artifact"""
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
        current_content = current_artifact["content"]
        
        # Create system prompt for updating
        system_prompt = self._get_update_prompt(current_content)
        
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
                "artifact_id": artifact_id,  # Send artifact_id to frontend
                "language": current_artifact.get("language"),
                "title": current_artifact["title"]
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
        
        # Update artifact with new content
        updated_artifact: Artifact = {
            "artifact_id": artifact_id or current_artifact["artifact_id"],
            "title": current_artifact["title"],
            "content": updated_content,
            "language": current_artifact.get("language")
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
        logger.info(f"Artifact updated successfully: {current_artifact['title']}")
    

    
    async def _create_artifact_sync(self, state: CanvasGraphState) -> CanvasGraphState:
        """Create artifact without streaming - for LangGraph node"""
        messages = state["messages"]
        last_message = messages[-1]["content"]
        
        system_prompt = self._get_creation_prompt()
        
        llm_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        
        # Get full response (non-streaming)
        response = await self.llm.ainvoke(llm_messages)
        artifact_content = response.content
        
        artifact_title = self._extract_title(artifact_content)
        language = self._detect_language(last_message, artifact_content)
        artifact_id = str(uuid.uuid4())
        
        artifact: Artifact = {
            "artifact_id": artifact_id,
            "title": artifact_title,
            "content": artifact_content,
            "language": language
        }
        
        state["artifact"] = artifact
        state["artifact_id"] = artifact_id
        return state
    
    async def _update_artifact_sync(self, state: CanvasGraphState) -> CanvasGraphState:
        """Update artifact without streaming - for LangGraph node"""
        messages = state["messages"]
        current_artifact = state.get("artifact")
        
        if not current_artifact:
            return await self._create_artifact_sync(state)
        
        last_message = messages[-1]["content"]
        current_content = current_artifact["content"]
        
        system_prompt = self._get_update_prompt(current_content)
        
        llm_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        
        response = await self.llm.ainvoke(llm_messages)
        updated_content = response.content
        
        updated_artifact: Artifact = {
            "artifact_id": current_artifact["artifact_id"],
            "title": current_artifact["title"],
            "content": updated_content,
            "language": current_artifact.get("language")
        }
        
        state["artifact"] = updated_artifact
        return state
    

    

    
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
    
    def _extract_title(self, content: str) -> str:
        """Extract title from artifact content"""
        lines = content.strip().split("\n")
        
        # Look for markdown heading
        for line in lines:
            if line.startswith("#"):
                return line.replace("#", "").strip()
        
        # Look for class or function name in code
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
        
        # Use first non-empty line
        for line in lines:
            if line.strip():
                return line.strip()[:50]
        
        return "Artifact"
    
    async def _generate_title_with_llm(self, message: str, language: str) -> str:
        """Generate a concise, meaningful title using LLM based on user's message"""
        try:
            title_prompt = f"""Generate a concise title (10 words max) for the content being requested. The title should be clear and descriptive.

User request: {message}
Language/Type: {language}

Return ONLY the title, nothing else. No quotes, no explanation.

Examples:
- "Create a Python function to calculate fibonacci" -> "Fibonacci Calculator"
- "Write a React component for todo list" -> "Todo List Component"
- "Generate markdown documentation for API" -> "API Documentation"

Title:"""
            
            response = await self.llm.ainvoke([{"role": "user", "content": title_prompt}])
            title = response.content.strip().strip('"\'')
            
            # Validate and limit length
            if title and len(title) > 0:
                return title[:60]  # Max 60 chars
            else:
                logger.warning("LLM returned empty title, using fallback")
                return self._fallback_title(message)
                
        except Exception as e:
            logger.error(f"Error generating title with LLM: {e}")
            return self._fallback_title(message)
    
    def _fallback_title(self, message: str) -> str:
        """Fallback title generation if LLM fails"""
        words = message.split()[:4]
        title = " ".join(words).capitalize()
        return title[:50] if title else "New Artifact"

    
    def _get_creation_prompt(self) -> str:
        """Get system prompt for artifact creation"""
        return """You are a content generation assistant. Generate high-quality content based on the user's request.

For code:
- Write production-quality code with proper error handling
- Include helpful comments
- Follow best practices for the language
- Output ONLY the code, no explanations or markdown formatting

For text/documentation:
- Use proper markdown formatting
- Organize content with headings and sections
- Be concise and clear
- Output ONLY the content

IMPORTANT: Output ONLY the requested content without any preamble, explanations, or markdown code fences."""
    
    def _get_update_prompt(self, current_content: str) -> str:
        """Get system prompt for artifact updates"""
        return f"""You are a content modification assistant. Update the following content based on the user's request.

CURRENT CONTENT:
```
{current_content}
```

Instructions:
- Make only the requested changes
- Maintain code quality and consistency for code content
- Maintain document structure and tone for text content
- Keep the overall structure unless asked to change it
- Output ONLY the updated content, no explanations or markdown formatting around it"""
    
    def _build_partial_update_prompt(self, state: CanvasGraphState) -> str:
        """Build context-aware prompt for partial content updates"""
        
        artifact = state["artifact"]
        selected_text = state["selectedText"]
        full_content = artifact["content"]
        
        selection_start = selected_text["start"]
        selection_end = selected_text["end"]
        
        # Extract context window (e.g., 200 chars before/after)
        context_window = 200
        context_before = full_content[max(0, selection_start - context_window):selection_start]
        context_after = full_content[selection_end:min(len(full_content), selection_end + context_window)]
        
        language = artifact.get("language", "text")
        
        prompt = f"""You are editing a specific section of content in a canvas artifact.

**Task:** Modify ONLY the selected portion based on the user's request.

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
- Return only the modified content block without any markdown code fences
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
            name=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_START,
            value={
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
                    name=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_CHUNK,
                    value={
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
            name=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_COMPLETE,
            value={
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
        full_content = artifact["content"]
        
        # Replace selected region with updated content
        new_content = (
            full_content[:selected_text["start"]] +
            updated_content +
            full_content[selected_text["end"]:]
        )
        
        # Update artifact with new content
        updated_artifact: Artifact = {
            "artifact_id": artifact["artifact_id"],
            "title": artifact["title"],
            "content": new_content,
            "language": artifact.get("language")
        }
        
        state["artifact"] = updated_artifact
        logger.debug(f"Artifact updated with partial update merged")
