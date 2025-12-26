from typing import Dict, List, Optional
from llm.ollama_client import ollama_client
from llm.gemini_client import gemini_client
from config import settings


class ProviderClient:
    """Unified client for all LLM providers"""
    
    async def list_all_models(self, provider_filter: Optional[str] = None) -> Dict:
        """
        List models from all providers or specific provider
        
        Args:
            provider_filter: Optional provider name to filter by ("ollama", "gemini")
        
        Returns:
            Dict with providers, models, and defaults
        """
        providers = []
        all_models = []
        errors = []
        
        # Fetch Ollama models
        if not provider_filter or provider_filter == "ollama":
            ollama_data = await ollama_client.list_available_models()
            has_ollama_models = "error" not in ollama_data and len(ollama_data.get("models", [])) > 0
            
            if "error" in ollama_data:
                errors.append({"provider": "ollama", "error": ollama_data["error"]})
            else:
                for model in ollama_data.get("models", []):
                    model["provider"] = "ollama"
                    all_models.append(model)
            
            # Always add Ollama to providers list (even if unavailable)
            providers.append({
                "id": "ollama",
                "name": "Ollama",
                "available": has_ollama_models
            })
        
        # Fetch Gemini models
        if not provider_filter or provider_filter == "gemini":
            gemini_data = await gemini_client.list_available_models()
            has_gemini_models = "error" not in gemini_data and len(gemini_data.get("models", [])) > 0
            
            if "error" in gemini_data:
                errors.append({"provider": "gemini", "error": gemini_data["error"]})
            else:
                for model in gemini_data.get("models", []):
                    model["provider"] = "gemini"
                    all_models.append(model)
            
            # Always add Gemini to providers list (even if unavailable)
            providers.append({
                "id": "gemini",
                "name": "Gemini",
                "available": has_gemini_models
            })
        
        return {
            "providers": providers,
            "models": all_models,
            "default_provider": settings.DEFAULT_PROVIDER,
            "default_model": settings.DEFAULT_MODEL,
            "errors": errors if errors else None
        }
    
    async def get_models_by_provider(self, provider: str) -> List[Dict]:
        """Get models for a specific provider"""
        data = await self.list_all_models(provider_filter=provider)
        return data.get("models", [])


# Global instance
provider_client = ProviderClient()
