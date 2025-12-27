from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from typing import List, Dict, Any


class GeminiProvider:
    def __init__(self, model: str = None):
        """
        Initialize Gemini provider with optional model parameter
        
        Args:
            model: Model name (e.g., "gemini-1.5-flash", "gemini-1.5-pro")
                   Falls back to settings.GEMINI_MODEL if not provided
        """
        self.model = ChatGoogleGenerativeAI(
            model=model or settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
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
