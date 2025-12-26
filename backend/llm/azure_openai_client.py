"""Azure OpenAI Client for listing models and deployments"""

from config import settings
import logging

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """
    Client for Azure OpenAI model listing
    
    Note: Azure OpenAI uses deployments rather than direct model listing.
    This client returns pre-configured models from settings and common Azure OpenAI models.
    """
    
    def list_models(self):
        """
        List available Azure OpenAI models/deployments
        
        Azure OpenAI doesn't have a public list API like Ollama.
        Instead, we return:
        1. The configured deployment from settings
        2. Common Azure OpenAI models available for deployment
        
        Returns:
            dict: Dictionary containing models list, default model, and any errors
        """
        try:
            models = []
            
            # Add configured deployment if available
            if settings.AZURE_OPENAI_DEPLOYMENT and settings.AZURE_OPENAI_ENDPOINT:
                models.append({
                    "id": settings.AZURE_OPENAI_DEPLOYMENT,
                    "name": f"{settings.AZURE_OPENAI_MODEL} (Deployment)",
                    "size": "Azure Cloud",
                    "available": True,
                    "provider": "azure-openai",
                    "is_deployment": True
                })
                logger.info(f"Added configured deployment: {settings.AZURE_OPENAI_DEPLOYMENT}")
            
            # Add common Azure OpenAI models
            common_models = [
                {"id": "gpt-4", "name": "GPT-4", "description": "Most capable GPT-4 model"},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "Faster GPT-4 with 128k context"},
                {"id": "gpt-4o", "name": "GPT-4o", "description": "Latest multimodal GPT-4 model"},
                {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo", "description": "Fast and efficient model"},
                {"id": "gpt-4-32k", "name": "GPT-4 32K", "description": "GPT-4 with extended context"},
            ]
            
            # Only add common models if we have valid Azure configuration
            has_config = bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY)
            
            for model in common_models:
                models.append({
                    "id": model["id"],
                    "name": model["name"],
                    "size": "Azure Cloud",
                    "available": has_config,
                    "provider": "azure-openai",
                    "description": model.get("description", ""),
                    "is_deployment": False
                })
            
            default_model = settings.AZURE_OPENAI_DEPLOYMENT or "gpt-4"
            
            logger.info(f"Listed {len(models)} Azure OpenAI models")
            
            return {
                "models": models,
                "default": default_model
            }
            
        except Exception as e:
            logger.error(f"Error listing Azure OpenAI models: {e}")
            return {
                "models": [],
                "default": None,
                "error": str(e)
            }


# Singleton instance
azure_openai_client = AzureOpenAIClient()
