"""
Claims Processing Agent

Handles insurance claims questions, status checks, and claims procedures.
"""

import uuid
import logging
from typing import AsyncGenerator
from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ThinkingStartEvent,
    ThinkingTextMessageContentEvent as ThinkingContentEvent,
    ThinkingEndEvent
)
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory

logger = logging.getLogger(__name__)


class ClaimsAgent(BaseAgent):
    """Agent specialized in insurance claims processing"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Claims Agent
        
        Args:
            model: Optional model name
            provider: Optional provider name
        """
        self.provider = provider or "ollama"
        self.model = model or "qwen:7b"
        provider_instance = LLMProviderFactory.get_provider(self.provider, self.model)
        self.llm = provider_instance.get_model()
        self.name = "Claims Processing Expert"
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute claims agent logic with streaming"""
        logger.info(f"Claims Agent processing with model={self.model}, provider={self.provider}")
        
        try:
            message_id = str(uuid.uuid4())
            
            # Emit thinking event
            yield ThinkingStartEvent(
                type=EventType.THINKING_START,
                message_id=message_id
            )
            yield ThinkingContentEvent(
                type=EventType.THINKING_TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta="Analyzing claims question..."
            )
            yield ThinkingEndEvent(
                type=EventType.THINKING_END,
                message_id=message_id
            )
            
            # Prepare system prompt for claims expertise
            system_prompt = """You are an insurance claims processing expert. You help customers with:
            - Filing insurance claims
            - Understanding claims procedures
            - Checking claims status
            - Required documentation for claims
            - Claims approval process
            - Claims rejection reasons and appeals
            
            Provide step-by-step guidance on claims processes. Use Vietnamese if the question is in Vietnamese.
            """
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(state.get("messages", []))
            
            # Stream response
            yield TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message_id,
                role="assistant"
            )
            
            async for chunk in self.llm.astream(messages):
                content = chunk.content
                if content:
                    yield TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=message_id,
                        delta=content
                    )
            
            yield TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END,
                message_id=message_id
            )
            
        except Exception as e:
            logger.error(f"Error in Claims Agent: {str(e)}")
            raise
