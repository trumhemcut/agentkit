"""
Insurance Policy Agent

Handles questions about insurance policies, coverage details, premiums, and benefits.
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


class InsurancePolicyAgent(BaseAgent):
    """Agent specialized in insurance policy information"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Insurance Policy Agent
        
        Args:
            model: Optional model name (e.g., 'qwen:7b')
            provider: Optional provider name (e.g., 'ollama', 'gemini', 'azure-openai')
        """
        self.provider = provider or "ollama"
        self.model = model or "qwen:7b"
        provider_instance = LLMProviderFactory.get_provider(self.provider, self.model)
        self.llm = provider_instance.get_model()
        self.name = "Insurance Policy Expert"
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute policy agent logic with streaming"""
        logger.info(f"Insurance Policy Agent processing with model={self.model}, provider={self.provider}")
        
        try:
            # Generate message ID for tracking
            message_id = str(uuid.uuid4())
            
            # Emit thinking events
            yield ThinkingStartEvent(
                type=EventType.THINKING_START,
                message_id=message_id
            )
            yield ThinkingContentEvent(
                type=EventType.THINKING_TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta="Analyzing insurance policy question..."
            )
            yield ThinkingEndEvent(
                type=EventType.THINKING_END,
                message_id=message_id
            )
            
            # Prepare system prompt for policy expertise
            system_prompt = """You are an insurance policy expert. You help customers understand:
            - Different types of insurance policies (life, health, auto, home, etc.)
            - Coverage details and benefits
            - Premium calculations and payment options
            - Policy terms and conditions
            - Eligibility requirements
            
            Provide clear, accurate information about insurance policies. Use Vietnamese if the question is in Vietnamese.
            """
            
            # Prepare messages with system prompt
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
            logger.error(f"Error in Insurance Policy Agent: {str(e)}")
            raise
