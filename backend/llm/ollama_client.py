"""
Ollama client for interacting with Ollama API
Provides functionality to list available models and check model availability
"""
import httpx
from typing import List, Dict, Optional
from config import settings


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.timeout = 10.0  # Timeout for API calls
    
    async def list_available_models(self) -> Dict[str, any]:
        """
        Query Ollama for available models
        Returns structured list of models with metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                # Parse Ollama response and structure it
                models = []
                if "models" in data:
                    for model_info in data["models"]:
                        model_name = model_info.get("name", "")
                        
                        # Extract model details
                        size_bytes = model_info.get("size", 0)
                        size_gb = size_bytes / (1024**3) if size_bytes > 0 else 0
                        
                        # Determine display name and size label
                        display_name = model_name
                        size_label = "Unknown"
                        
                        # Parse model name for better display
                        if "qwen" in model_name.lower():
                            if "4b" in model_name.lower():
                                display_name = "Qwen 4B"
                                size_label = "4B parameters"
                            elif "7b" in model_name.lower():
                                display_name = "Qwen 7B"
                                size_label = "7B parameters"
                            elif "14b" in model_name.lower():
                                display_name = "Qwen 14B"
                                size_label = "14B parameters"
                            elif "32b" in model_name.lower():
                                display_name = "Qwen 32B"
                                size_label = "32B parameters"
                            else:
                                display_name = f"Qwen ({size_gb:.1f}GB)"
                                size_label = f"{size_gb:.1f}GB"
                        
                        models.append({
                            "id": model_name,
                            "name": display_name,
                            "size": size_label,
                            "available": True,
                            "size_bytes": size_bytes
                        })
                
                # Sort models by name
                models.sort(key=lambda x: x["id"])
                
                return {
                    "models": models,
                    "default": settings.OLLAMA_MODEL
                }
                
        except httpx.ConnectError:
            # Ollama not running
            return {
                "models": [],
                "default": settings.OLLAMA_MODEL,
                "error": "Unable to connect to Ollama. Please ensure Ollama is running."
            }
        except httpx.TimeoutException:
            # Request timeout
            return {
                "models": [],
                "default": settings.OLLAMA_MODEL,
                "error": "Ollama request timed out."
            }
        except Exception as e:
            # Other errors
            return {
                "models": [],
                "default": settings.OLLAMA_MODEL,
                "error": f"Error fetching models: {str(e)}"
            }
    
    async def check_model_available(self, model_name: str) -> bool:
        """
        Check if a specific model is available
        """
        result = await self.list_available_models()
        if "error" in result:
            return False
        
        models = result.get("models", [])
        return any(model["id"] == model_name for model in models)
    
    def is_valid_model(self, model_name: str, allowed_models: List[str] = None) -> bool:
        """
        Validate if model name is in the allowed list
        """
        if allowed_models is None:
            # Default allowed models (can be extended)
            allowed_models = [
                "qwen:4b",
                "qwen:7b",
                "qwen:14b",
                "qwen:32b"
            ]
        
        return model_name in allowed_models


# Singleton instance
ollama_client = OllamaClient()
