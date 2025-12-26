"""
Tests for Azure OpenAI Provider Integration

Test the Azure OpenAI provider, client, and factory integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from llm.azure_openai_provider import AzureOpenAIProvider
from llm.azure_openai_client import AzureOpenAIClient
from llm.provider_factory import LLMProviderFactory
from llm.provider_client import provider_client


class TestAzureOpenAIProvider:
    """Test AzureOpenAIProvider initialization and configuration"""
    
    @patch('llm.azure_openai_provider.settings')
    @patch('llm.azure_openai_provider.AzureChatOpenAI')
    def test_provider_initialization_default(self, mock_azure_chat, mock_settings):
        """Test provider initialization with default settings"""
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_KEY = "test-key"
        mock_settings.AZURE_OPENAI_DEPLOYMENT = "test-deployment"
        mock_settings.AZURE_OPENAI_MODEL = "gpt-4"
        mock_settings.AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
        
        provider = AzureOpenAIProvider()
        
        mock_azure_chat.assert_called_once()
        assert mock_azure_chat.call_args.kwargs['azure_endpoint'] == "https://test.openai.azure.com/"
        assert mock_azure_chat.call_args.kwargs['deployment_name'] == "test-deployment"
        assert mock_azure_chat.call_args.kwargs['model'] == "gpt-4"
    
    @patch('llm.azure_openai_provider.settings')
    @patch('llm.azure_openai_provider.AzureChatOpenAI')
    def test_provider_initialization_custom_model(self, mock_azure_chat, mock_settings):
        """Test provider initialization with custom model"""
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_KEY = "test-key"
        mock_settings.AZURE_OPENAI_DEPLOYMENT = "test-deployment"
        mock_settings.AZURE_OPENAI_MODEL = "gpt-4"
        mock_settings.AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
        
        provider = AzureOpenAIProvider(model="gpt-4-turbo")
        
        assert mock_azure_chat.call_args.kwargs['model'] == "gpt-4-turbo"
    
    @patch('llm.azure_openai_provider.settings')
    @patch('llm.azure_openai_provider.AzureChatOpenAI')
    def test_provider_initialization_custom_deployment(self, mock_azure_chat, mock_settings):
        """Test provider initialization with custom deployment"""
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_KEY = "test-key"
        mock_settings.AZURE_OPENAI_DEPLOYMENT = "test-deployment"
        mock_settings.AZURE_OPENAI_MODEL = "gpt-4"
        mock_settings.AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
        
        provider = AzureOpenAIProvider(deployment="custom-deployment")
        
        assert mock_azure_chat.call_args.kwargs['deployment_name'] == "custom-deployment"
    
    @patch('llm.azure_openai_provider.settings')
    def test_provider_missing_endpoint(self, mock_settings):
        """Test provider initialization fails without endpoint"""
        mock_settings.AZURE_OPENAI_ENDPOINT = ""
        mock_settings.AZURE_OPENAI_API_KEY = "test-key"
        mock_settings.AZURE_OPENAI_DEPLOYMENT = "test-deployment"
        
        with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is not configured"):
            AzureOpenAIProvider()
    
    @patch('llm.azure_openai_provider.settings')
    def test_provider_missing_api_key(self, mock_settings):
        """Test provider initialization fails without API key"""
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_KEY = ""
        mock_settings.AZURE_OPENAI_DEPLOYMENT = "test-deployment"
        
        with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY is not configured"):
            AzureOpenAIProvider()


class TestAzureOpenAIClient:
    """Test AzureOpenAIClient model listing"""
    
    @patch('llm.azure_openai_client.settings')
    def test_list_models_with_deployment(self, mock_settings):
        """Test listing models with configured deployment"""
        mock_settings.AZURE_OPENAI_DEPLOYMENT = "gpt-4-deployment"
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_KEY = "test-key"
        mock_settings.AZURE_OPENAI_MODEL = "gpt-4"
        
        client = AzureOpenAIClient()
        result = client.list_models()
        
        assert "models" in result
        assert len(result["models"]) > 0
        
        # Check deployment model is included
        deployment_models = [m for m in result["models"] if m.get("is_deployment")]
        assert len(deployment_models) == 1
        assert deployment_models[0]["id"] == "gpt-4-deployment"
        
        # Check common models are included
        common_models = [m for m in result["models"] if not m.get("is_deployment")]
        assert len(common_models) > 0
    
    @patch('llm.azure_openai_client.settings')
    def test_list_models_without_deployment(self, mock_settings):
        """Test listing models without configured deployment"""
        mock_settings.AZURE_OPENAI_DEPLOYMENT = ""
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_KEY = "test-key"
        
        client = AzureOpenAIClient()
        result = client.list_models()
        
        assert "models" in result
        # Should still return common models
        assert len(result["models"]) > 0
        
        # No deployment models
        deployment_models = [m for m in result["models"] if m.get("is_deployment")]
        assert len(deployment_models) == 0
    
    @patch('llm.azure_openai_client.settings')
    def test_list_models_no_credentials(self, mock_settings):
        """Test listing models without credentials shows unavailable"""
        mock_settings.AZURE_OPENAI_DEPLOYMENT = ""
        mock_settings.AZURE_OPENAI_ENDPOINT = ""
        mock_settings.AZURE_OPENAI_API_KEY = ""
        
        client = AzureOpenAIClient()
        result = client.list_models()
        
        assert "models" in result
        # Models are listed but marked as unavailable
        for model in result["models"]:
            assert model["available"] == False


class TestProviderFactory:
    """Test LLMProviderFactory with Azure OpenAI"""
    
    @patch('llm.azure_openai_provider.settings')
    @patch('llm.azure_openai_provider.AzureChatOpenAI')
    def test_factory_creates_azure_provider(self, mock_azure_chat, mock_settings):
        """Test factory creates Azure OpenAI provider"""
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_KEY = "test-key"
        mock_settings.AZURE_OPENAI_DEPLOYMENT = "test-deployment"
        mock_settings.AZURE_OPENAI_MODEL = "gpt-4"
        mock_settings.AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
        
        provider = LLMProviderFactory.get_provider("azure-openai")
        
        assert provider is not None
        assert isinstance(provider, AzureOpenAIProvider)
    
    @patch('llm.azure_openai_provider.settings')
    @patch('llm.azure_openai_provider.AzureChatOpenAI')
    def test_factory_creates_azure_provider_with_model(self, mock_azure_chat, mock_settings):
        """Test factory creates Azure OpenAI provider with specific model"""
        mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock_settings.AZURE_OPENAI_API_KEY = "test-key"
        mock_settings.AZURE_OPENAI_DEPLOYMENT = "test-deployment"
        mock_settings.AZURE_OPENAI_MODEL = "gpt-4"
        mock_settings.AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
        
        provider = LLMProviderFactory.get_provider("azure-openai", model="gpt-4-turbo")
        
        # Model parameter is used as deployment name for Azure OpenAI
        assert mock_azure_chat.call_args.kwargs['deployment_name'] == "gpt-4-turbo"


class TestProviderClient:
    """Test unified ProviderClient with Azure OpenAI"""
    
    @pytest.mark.asyncio
    @patch('llm.provider_client.azure_openai_client')
    @patch('llm.provider_client.gemini_client')
    @patch('llm.provider_client.ollama_client')
    @patch('llm.provider_client.settings')
    async def test_list_all_models_includes_azure(
        self, mock_settings, mock_ollama, mock_gemini, mock_azure
    ):
        """Test listing all models includes Azure OpenAI"""
        mock_settings.DEFAULT_PROVIDER = "ollama"
        mock_settings.DEFAULT_MODEL = "qwen:7b"
        
        # Mock responses
        mock_ollama.list_available_models = AsyncMock(return_value={
            "models": [{"id": "qwen:7b", "name": "Qwen 7B"}]
        })
        mock_gemini.list_available_models = AsyncMock(return_value={
            "models": [{"id": "gemini-2.5-flash", "name": "Gemini Flash"}]
        })
        mock_azure.list_models.return_value = {
            "models": [{"id": "gpt-4", "name": "GPT-4"}]
        }
        
        result = await provider_client.list_all_models()
        
        assert "providers" in result
        assert len(result["providers"]) == 3
        
        # Check Azure OpenAI provider is included
        azure_provider = next((p for p in result["providers"] if p["id"] == "azure-openai"), None)
        assert azure_provider is not None
        assert azure_provider["name"] == "Azure OpenAI"
        
        # Check models from all providers
        assert len(result["models"]) == 3
        model_providers = [m["provider"] for m in result["models"]]
        assert "ollama" in model_providers
        assert "gemini" in model_providers
        assert "azure-openai" in model_providers
    
    @pytest.mark.asyncio
    @patch('llm.provider_client.azure_openai_client')
    @patch('llm.provider_client.settings')
    async def test_get_azure_models_only(self, mock_settings, mock_azure):
        """Test getting only Azure OpenAI models"""
        mock_azure.list_models.return_value = {
            "models": [
                {"id": "gpt-4", "name": "GPT-4"},
                {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo"}
            ]
        }
        
        result = await provider_client.get_models_by_provider("azure-openai")
        
        assert len(result) == 2
        assert all(m["provider"] == "azure-openai" for m in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
