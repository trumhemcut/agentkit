import uuid
import logging
from typing import AsyncGenerator
from ag_ui.core import EventType, TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent, BaseEvent
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory

logger = logging.getLogger(__name__)


class ChatAgent(BaseAgent):
    def __init__(self, model: str = None):
        """
        Initialize ChatAgent with optional model parameter
        
        Args:
            model: Model name to use (e.g., "qwen:7b", "qwen:4b")
                   Falls back to default if not provided
        """
        provider = LLMProviderFactory.get_provider("ollama", model=model)
        self.llm = provider.get_model()
    
    async def run(self, state: AgentState) -> AsyncGenerator[BaseEvent, None]:
        """Execute chat agent and stream events as they occur"""
        messages = state["messages"]
        message_id = str(uuid.uuid4())
        
        logger.info(f"Starting chat agent run")
        logger.debug(f"Message count: {len(messages)}")
        logger.debug(f"Message ID: {message_id}")
        
        # Start message event using official AG-UI event class with metadata
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text"}  # Explicitly mark as text message
        )
        
        # Stream LLM response - yield events immediately as chunks arrive
        chunk_count = 0
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content:
                chunk_count += 1
                # Content event using official AG-UI event class
                yield TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=content
                )
        
        logger.info(f"Completed streaming {chunk_count} chunks")
        
        # End message event using official AG-UI event class
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
