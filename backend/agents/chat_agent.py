import uuid
from typing import AsyncGenerator
from ag_ui.core import EventType, TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent, BaseEvent
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory


class ChatAgent(BaseAgent):
    def __init__(self):
        provider = LLMProviderFactory.get_provider("ollama")
        self.llm = provider.get_model()
    
    async def run(self, state: AgentState) -> AsyncGenerator[BaseEvent, None]:
        messages = state["messages"]
        message_id = str(uuid.uuid4())
        
        # Start message event using official AG-UI event class
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant"
        )
        
        # Stream LLM response
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content:
                # Content event using official AG-UI event class
                yield TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=content
                )
        
        # End message event using official AG-UI event class
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
