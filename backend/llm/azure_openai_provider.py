"""Azure OpenAI Provider for LangChain integration"""

from langchain_openai import AzureChatOpenAI
from config import settings
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AzureOpenAIProvider:
    """
    Azure OpenAI provider wrapper for LangChain
    
    This provider enables using Azure OpenAI models with LangGraph agents.
    Azure OpenAI requires an endpoint, API key, deployment name, and API version.
    """
    
    def __init__(self, model: str = None, deployment: str = None):
        """
        Initialize Azure OpenAI provider
        
        Args:
            model: Model name (e.g., "gpt-4", "gpt-35-turbo", "gpt-4o")
            deployment: Azure deployment name (overrides settings)
        """
        try:
            # Use provided deployment or fall back to settings
            deployment_name = deployment or settings.AZURE_OPENAI_DEPLOYMENT
            model_name = model or settings.AZURE_OPENAI_MODEL
            
            if not settings.AZURE_OPENAI_ENDPOINT:
                raise ValueError("AZURE_OPENAI_ENDPOINT is not configured")
            
            if not settings.AZURE_OPENAI_API_KEY:
                raise ValueError("AZURE_OPENAI_API_KEY is not configured")
            
            if not deployment_name:
                raise ValueError("AZURE_OPENAI_DEPLOYMENT is not configured")
            
            logger.info(f"Initializing Azure OpenAI with deployment: {deployment_name}, model: {model_name}")
            
            self.model = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                openai_api_version=settings.AZURE_OPENAI_API_VERSION,
                deployment_name=deployment_name,
                openai_api_key=settings.AZURE_OPENAI_API_KEY,
                model=model_name,
                streaming=True,
                temperature=0.7
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI provider: {e}")
            raise
    
    def get_model(self):
        """
        Get the LangChain Azure OpenAI model instance
        
        Returns:
            AzureChatOpenAI: LangChain Azure OpenAI model
        """
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
