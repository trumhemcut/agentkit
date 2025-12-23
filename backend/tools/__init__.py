from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Base class for all tools"""
    name: str = ""
    description: str = ""
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute tool logic"""
        pass
