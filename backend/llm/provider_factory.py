from llm.ollama_provider import OllamaProvider
from llm.gemini_provider import GeminiProvider


class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "ollama", model: str = None):
        """
        Get LLM provider instance
        
        Args:
            provider_type: Type of provider ("ollama", "gemini")
            model: Optional model name to use with the provider
        
        Returns:
            Provider instance
        """
        if provider_type == "ollama":
            return OllamaProvider(model=model)
        elif provider_type == "gemini":
            return GeminiProvider(model=model)
        raise ValueError(f"Unknown provider: {provider_type}")
