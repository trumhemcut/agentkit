from llm.ollama_provider import OllamaProvider
from llm.gemini_provider import GeminiProvider
from llm.azure_openai_provider import AzureOpenAIProvider


class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "ollama", model: str = None):
        """
        Get LLM provider instance
        
        Args:
            provider_type: Type of provider ("ollama", "gemini", "azure-openai")
            model: Optional model name or deployment name to use with the provider
        
        Returns:
            Provider instance
        """
        if provider_type == "ollama":
            return OllamaProvider(model=model)
        elif provider_type == "gemini":
            return GeminiProvider(model=model)
        elif provider_type == "azure-openai":
            # For Azure OpenAI, model parameter can be deployment name
            return AzureOpenAIProvider(deployment=model)
        raise ValueError(f"Unknown provider: {provider_type}")
