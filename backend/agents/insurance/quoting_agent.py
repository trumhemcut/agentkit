"""
Quoting Agent

Handles insurance quotes, pricing calculations, and premium estimates.
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


class QuotingAgent(BaseAgent):
    """Agent specialized in insurance quotes and pricing"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Quoting Agent
        
        Args:
            model: Optional model name
            provider: Optional provider name
        """
        self.provider = provider or "ollama"
        self.model = model or "qwen:7b"
        provider_instance = LLMProviderFactory.get_provider(self.provider, self.model)
        self.llm = provider_instance.get_model()
        self.name = "Insurance Quoting Expert"
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute quoting agent logic with streaming"""
        logger.info(f"Quoting Agent processing with model={self.model}, provider={self.provider}")
        
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
                delta="Analyzing insurance quote request..."
            )
            yield ThinkingEndEvent(
                type=EventType.THINKING_END,
                message_id=message_id
            )
            
            # Prepare system prompt for quoting expertise
            system_prompt = """You are an insurance quoting expert. You help customers with:
            - Insurance premium calculations and estimates
            - Pricing based on customer information (age, occupation, coverage needs)
            - Comparing different insurance packages and their costs
            - Explaining factors that affect insurance premiums
            - Providing quote breakdowns and cost analysis
            - Recommending suitable insurance packages based on budget
            
            Ask relevant questions to provide accurate quotes. Use Vietnamese if the question is in Vietnamese.
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
            logger.error(f"Error in Quoting Agent: {str(e)}")
            raise
