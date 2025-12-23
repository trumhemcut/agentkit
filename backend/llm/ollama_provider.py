from langchain_ollama import ChatOllama
from config import settings


class OllamaProvider:
    def __init__(self):
        self.model = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            streaming=True
        )
    
    def get_model(self):
        return self.model
