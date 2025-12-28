"""
Customer Support Agent

Handles general customer support, account management, and basic inquiries.
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


class CustomerSupportAgent(BaseAgent):
    """Agent specialized in customer support"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Customer Support Agent
        
        Args:
            model: Optional model name
            provider: Optional provider name
        """
        self.provider = provider or "ollama"
        self.model = model or "qwen:7b"
        provider_instance = LLMProviderFactory.get_provider(self.provider, self.model)
        self.llm = provider_instance.get_model()
        self.name = "Customer Support Specialist"
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute customer support agent logic with streaming"""
        logger.info(f"Customer Support Agent processing with model={self.model}, provider={self.provider}")
        
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
                delta="Processing customer support request..."
            )
            yield ThinkingEndEvent(
                type=EventType.THINKING_END,
                message_id=message_id
            )
            
            # Prepare system prompt for customer support
            system_prompt = """You are a customer support specialist for an insurance company. You help customers with:
            - General inquiries about insurance services
            - Account management and updates
            - Contact information and office locations
            - Appointment scheduling
            - Frequently asked questions
            - Directing customers to specialized agents when needed
            
            Be friendly, helpful, and professional. Use Vietnamese if the question is in Vietnamese.
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
            logger.error(f"Error in Customer Support Agent: {str(e)}")
            raise
