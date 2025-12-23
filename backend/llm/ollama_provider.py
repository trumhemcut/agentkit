from langchain_ollama import ChatOllama
from config import settings


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
