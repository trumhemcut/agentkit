import httpx
from typing import Dict
from config import settings


class GeminiClient:
    """Client for interacting with Google AI API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = 10.0
    
    async def list_available_models(self) -> Dict[str, any]:
        """
        Query Gemini API for available models
        Returns structured list of models with metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/models?key={self.api_key}"
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse and structure models
                models = []
                for model_info in data.get("models", []):
                    model_name = model_info.get("name", "").replace("models/", "")
                    
                    # Filter to text generation models only
                    if "generateContent" in model_info.get("supportedGenerationMethods", []):
                        display_name = model_name.replace("-", " ").title()
                        
                        models.append({
                            "id": model_name,
                            "name": display_name,
                            "size": "Google Cloud",  # No local size
                            "available": True,
                            "provider": "gemini"
                        })
                
                return {
                    "models": models,
                    "default": settings.GEMINI_MODEL
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {
                    "models": [],
                    "default": settings.GEMINI_MODEL,
                    "error": "Invalid Gemini API key"
                }
            return {
                "models": [],
                "default": settings.GEMINI_MODEL,
                "error": f"Gemini API error: {str(e)}"
            }
        except Exception as e:
            return {
                "models": [],
                "default": settings.GEMINI_MODEL,
                "error": f"Error fetching Gemini models: {str(e)}"
            }
    
    async def check_model_available(self, model_name: str) -> bool:
        """Check if a specific Gemini model is available"""
        models_data = await self.list_available_models()
        return any(m["id"] == model_name for m in models_data.get("models", []))


# Global client instance
gemini_client = GeminiClient()
