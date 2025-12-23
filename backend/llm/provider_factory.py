from llm.ollama_provider import OllamaProvider


class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "ollama"):
        if provider_type == "ollama":
            return OllamaProvider()
        raise ValueError(f"Unknown provider: {provider_type}")
