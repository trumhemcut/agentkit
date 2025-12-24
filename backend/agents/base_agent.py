from typing import TypedDict, List, Dict, AsyncGenerator
from abc import ABC, abstractmethod


class AgentState(TypedDict, total=False):
    """State schema for LangGraph agents"""
    messages: List[Dict[str, str]]
    thread_id: str
    run_id: str


class BaseAgent(ABC):
    @abstractmethod
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute agent logic and stream events"""
        pass
