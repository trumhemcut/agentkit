from langchain_ollama import ChatOllama
from config import settings
from typing import List, Dict, Any


class OllamaProvider:
    def __init__(self, model: str = None):
        """
        Initialize Ollama provider with optional model parameter
        
        Args:
            model: Model name to use (e.g., "qwen:7b", "qwen:4b")
                   Falls back to settings.OLLAMA_MODEL if not provided
        """
        self.model = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=model or settings.OLLAMA_MODEL,
            streaming=True
        )
    
    def get_model(self):
        return self.model
    
    def get_model_with_tools(self, tools: List[Dict[str, Any]]):
        """
        Get model with tools bound for tool calling.
        
        Args:
            tools: List of tool schemas in OpenAI function calling format
        
        Returns:
            LangChain model with tools bound
        """
        return self.model.bind_tools(tools)
