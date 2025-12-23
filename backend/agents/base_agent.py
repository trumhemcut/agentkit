from typing import TypedDict, List, Dict
from abc import ABC, abstractmethod


class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    thread_id: str
    run_id: str


class BaseAgent(ABC):
    @abstractmethod
    async def run(self, state: AgentState):
        """Execute agent logic"""
        pass
