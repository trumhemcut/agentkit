from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings


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
