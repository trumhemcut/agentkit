# Azure OpenAI Provider Integration - Implementation Plan

## Overview
Add Azure OpenAI as a new LLM provider for AgentKit, following the same integration pattern used for Gemini. This enables users to select Azure OpenAI models alongside Ollama and Gemini providers.

## Requirement
Similar to Gemini integration, support Azure OpenAI provider with model selection capabilities.

## Architecture Pattern
Follow the existing provider architecture established by Gemini integration:

```
API Routes (routes.py)
    ↓
ProviderClient (provider_client.py) → Aggregates all providers
    ↓
┌──────────┬──────────┬────────────┐
│ Ollama   │ Gemini   │ Azure      │
│ Client   │ Client   │ OpenAI     │
│          │          │ Client     │
└──────────┴──────────┴────────────┘
    ↓           ↓           ↓
┌──────────┬──────────┬────────────┐
│ Ollama   │ Gemini   │ Azure      │
│ Provider │ Provider │ OpenAI     │
│          │          │ Provider   │
└──────────┴──────────┴────────────┘
```

---

## Backend Tasks (For Backend Agent)

### 1. Configuration Setup (`backend/config.py`)

**Task**: Add Azure OpenAI configuration settings

**Changes**:
- Add `AZURE_OPENAI_API_KEY` setting
- Add `AZURE_OPENAI_ENDPOINT` setting (required for Azure)
- Add `AZURE_OPENAI_API_VERSION` setting (default: "2024-02-15-preview")
- Add `AZURE_OPENAI_DEPLOYMENT` setting (deployment name)
- Add `AZURE_OPENAI_MODEL` setting (default: "gpt-4")
- Update `.env.example` with Azure OpenAI variables

**Reference**: Similar to `GEMINI_API_KEY` and `GEMINI_MODEL` in existing config

### 2. Azure OpenAI Provider (`backend/llm/azure_openai_provider.py`)

**Task**: Create LangChain provider wrapper for Azure OpenAI

**Implementation**:
```python
from langchain_openai import AzureChatOpenAI
from config import settings

class AzureOpenAIProvider:
    def __init__(self, model: str = None, deployment: str = None):
        """
        Initialize Azure OpenAI provider
        
        Args:
            model: Model name (e.g., "gpt-4", "gpt-35-turbo")
            deployment: Azure deployment name (overrides settings)
        """
        self.model = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            openai_api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=deployment or settings.AZURE_OPENAI_DEPLOYMENT,
            openai_api_key=settings.AZURE_OPENAI_API_KEY,
            model=model or settings.AZURE_OPENAI_MODEL,
            streaming=True,
            temperature=0.7
        )
    
    def get_model(self):
        return self.model
```

**Dependencies**:
- `langchain-openai` package
- Azure OpenAI service credentials

**Reference**: Pattern from `gemini_provider.py`

### 3. Azure OpenAI Client (`backend/llm/azure_openai_client.py`)

**Task**: Create client for listing available Azure OpenAI deployments/models

**Implementation**:
```python
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from config import settings
import logging

logger = logging.getLogger(__name__)

class AzureOpenAIClient:
    def list_models(self):
        """
        List available Azure OpenAI models/deployments
        
        Note: Azure OpenAI uses deployments, not direct model listing
        Returns pre-configured models from settings or common models
        """
        try:
            # Azure OpenAI doesn't have a public list API like Ollama
            # Return configured deployment + common Azure OpenAI models
            models = []
            
            # Add configured deployment
            if settings.AZURE_OPENAI_DEPLOYMENT:
                models.append({
                    "id": settings.AZURE_OPENAI_DEPLOYMENT,
                    "name": f"{settings.AZURE_OPENAI_MODEL} (Deployment)",
                    "size": "Azure Cloud",
                    "available": True,
                    "provider": "azure-openai"
                })
            
            # Add common Azure OpenAI models
            common_models = [
                {"id": "gpt-4", "name": "GPT-4"},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
                {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo"},
                {"id": "gpt-4o", "name": "GPT-4o"},
            ]
            
            for model in common_models:
                models.append({
                    "id": model["id"],
                    "name": model["name"],
                    "size": "Azure Cloud",
                    "available": True,
                    "provider": "azure-openai"
                })
            
            return {
                "models": models,
                "default": settings.AZURE_OPENAI_DEPLOYMENT or "gpt-4"
            }
            
        except Exception as e:
            logger.error(f"Error listing Azure OpenAI models: {e}")
            return {"models": [], "default": None, "error": str(e)}

azure_openai_client = AzureOpenAIClient()
```

**Key Considerations**:
- Azure OpenAI uses deployments, not direct model API
- List pre-configured models + deployment from settings
- Handle authentication gracefully

**Reference**: Pattern from `gemini_client.py`

### 4. Update Provider Factory (`backend/llm/provider_factory.py`)

**Task**: Add Azure OpenAI to provider factory

**Changes**:
```python
from llm.azure_openai_provider import AzureOpenAIProvider

class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "ollama", model: str = None):
        """
        Get LLM provider instance
        
        Args:
            provider_type: Type of provider ("ollama", "gemini", "azure-openai")
            model: Optional model name or deployment name
        
        Returns:
            Provider instance
        """
        if provider_type == "ollama":
            return OllamaProvider(model=model)
        elif provider_type == "gemini":
            return GeminiProvider(model=model)
        elif provider_type == "azure-openai":
            return AzureOpenAIProvider(deployment=model)
        raise ValueError(f"Unknown provider: {provider_type}")
```

**Reference**: Existing Gemini integration

### 5. Update Provider Client (`backend/llm/provider_client.py`)

**Task**: Add Azure OpenAI to unified provider client

**Changes**:
- Import `azure_openai_client`
- Add Azure OpenAI to `list_models()` method
- Handle Azure OpenAI errors gracefully
- Add to available providers list

**Example**:
```python
from llm.azure_openai_client import azure_openai_client

def list_models(self, provider: str = None):
    # ... existing code ...
    
    # Fetch Azure OpenAI models
    if provider is None or provider == "azure-openai":
        azure_result = azure_openai_client.list_models()
        if azure_result.get("models"):
            all_models.extend(azure_result["models"])
            if azure_result.get("default"):
                default_models["azure-openai"] = azure_result["default"]
        if azure_result.get("error"):
            errors["azure-openai"] = azure_result["error"]
    
    # Add Azure OpenAI to available providers
    providers.append({
        "id": "azure-openai",
        "name": "Azure OpenAI",
        "available": len([m for m in all_models if m["provider"] == "azure-openai"]) > 0
    })
```

**Reference**: Existing Gemini integration in provider_client.py

### 6. Update Requirements (`backend/requirements.txt`)

**Task**: Add Azure OpenAI dependencies

**Changes**:
```txt
langchain-openai>=0.2.0
openai>=1.0.0
azure-identity>=1.15.0  # For Azure authentication
```

### 7. Update Documentation (`backend/AZURE_OPENAI_INTEGRATION_README.md`)

**Task**: Create comprehensive documentation (Optional but recommended)

**Content**:
- Architecture overview
- Configuration guide
- API endpoints
- Frontend integration guide
- Authentication setup
- Deployment vs model explanation

**Reference**: `GEMINI_INTEGRATION_README.md` structure

---

## Frontend Tasks (For Frontend Agent)

### 1. Update Provider Icons (`frontend/components/ProviderSelector.tsx`)

**Task**: Add Azure OpenAI icon mapping

**Changes**:
```typescript
import { Cloud, Server, Azure } from 'lucide-react'; // Or use appropriate icon

const providerIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  ollama: Server,
  gemini: Cloud,
  'azure-openai': Cloud, // Or Azure-specific icon if available
};
```

### 2. Update Model Store Types (`frontend/types/model.ts` or inline)

**Task**: Ensure TypeScript types support "azure-openai" provider

**Changes**:
- Update provider type unions if strictly typed
- Ensure model metadata includes Azure-specific fields (deployment, version)

### 3. Test Frontend Integration

**Task**: Verify frontend correctly displays Azure OpenAI

**Validation**:
- Provider selector shows "Azure OpenAI" option
- Model selector lists Azure deployments/models
- Chat interface uses Azure OpenAI when selected
- Error handling for missing credentials

---

## Protocol (AG-UI)

### Existing Protocol Support
The current AG-UI protocol already supports dynamic provider/model selection through:
- `GET /models` - Returns all providers and models
- `GET /models/{provider}` - Returns provider-specific models
- `POST /chat/{agent_id}` - Accepts `provider` and `model` parameters

**No protocol changes required** - Azure OpenAI fits existing contract.

### API Response Format
```json
{
  "providers": [
    {"id": "ollama", "name": "Ollama", "available": true},
    {"id": "gemini", "name": "Gemini", "available": true},
    {"id": "azure-openai", "name": "Azure OpenAI", "available": true}
  ],
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "size": "Azure Cloud",
      "available": true,
      "provider": "azure-openai"
    }
  ],
  "default_provider": "ollama",
  "default_model": "qwen:7b"
}
```

---

## Testing Strategy

### Backend Tests
1. **Unit Tests** (`backend/tests/test_azure_openai_provider.py`)
   - Test AzureOpenAIProvider initialization
   - Test model retrieval
   - Test streaming support
   - Test error handling (missing credentials)

2. **Integration Tests** (`backend/tests/test_azure_openai_integration.py`)
   - Test model listing API
   - Test chat with Azure OpenAI provider
   - Test provider switching (Ollama → Azure OpenAI)
   - Test deployment name handling

### Frontend Tests
1. Test provider selector displays Azure OpenAI
2. Test model selector lists Azure models
3. Test chat with Azure OpenAI models
4. Test error states (invalid credentials)

---

## Environment Configuration

### Required Environment Variables
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_MODEL=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional: Set as default provider
DEFAULT_PROVIDER=azure-openai
DEFAULT_MODEL=gpt-4
```

### Setup Guide
1. Create Azure OpenAI resource in Azure Portal
2. Create model deployment (e.g., "gpt-4-deployment")
3. Get API key and endpoint from Azure Portal
4. Add credentials to `.env` file
5. Restart backend server

---

## Migration Path

### For Existing Users
1. Azure OpenAI is optional - no breaking changes
2. Default provider remains "ollama" unless changed
3. Frontend automatically detects new provider
4. No database migrations required

### Rollout Steps
1. Deploy backend with Azure OpenAI support
2. Users add Azure credentials to `.env`
3. Frontend automatically shows new provider
4. Users can switch providers via UI

---

## Dependencies

### Backend
- `langchain-openai>=0.2.0` - LangChain Azure OpenAI integration
- `openai>=1.0.0` - Official OpenAI SDK (supports Azure)
- `azure-identity>=1.15.0` - Azure authentication (optional)

### Frontend
- No new dependencies (uses existing provider/model selection UI)

---

## Success Criteria

### Backend
- ✅ Azure OpenAI provider successfully created
- ✅ Models/deployments listed via API
- ✅ Chat works with Azure OpenAI models
- ✅ Streaming responses functional
- ✅ Error handling for missing credentials
- ✅ Tests pass for Azure OpenAI integration

### Frontend
- ✅ Azure OpenAI appears in provider selector
- ✅ Azure models appear in model selector
- ✅ Chat interface works with Azure models
- ✅ Error messages clear for users

### Integration
- ✅ Switching between Ollama/Gemini/Azure works seamlessly
- ✅ AG-UI protocol supports Azure OpenAI without changes
- ✅ Documentation complete and accurate

---

## Timeline Estimate

### Backend Implementation
- Configuration setup: 15 mins
- Provider class: 30 mins
- Client class: 45 mins
- Factory update: 10 mins
- Provider client update: 20 mins
- Requirements update: 5 mins
- Testing: 45 mins
- **Total Backend**: ~3 hours

### Frontend Implementation
- Icon mapping: 5 mins
- Type updates: 10 mins
- Testing: 20 mins
- **Total Frontend**: ~35 mins

### Documentation & Testing
- README documentation: 30 mins
- Integration testing: 30 mins
- **Total Docs/Testing**: ~1 hour

**Total Estimated Time**: ~4-5 hours

---

## Risks & Mitigations

### Risk 1: Azure Deployment Complexity
- **Issue**: Azure uses deployments instead of direct model names
- **Mitigation**: Document deployment setup clearly, provide fallback to common model names

### Risk 2: Authentication Errors
- **Issue**: Missing or invalid Azure credentials
- **Mitigation**: Graceful error handling, clear error messages, optional provider

### Risk 3: API Version Changes
- **Issue**: Azure OpenAI API versions may change
- **Mitigation**: Use stable API version (2024-02-15-preview), document version in config

---

## Implementation Order

1. **Backend Configuration** (config.py, .env.example)
2. **Backend Provider** (azure_openai_provider.py)
3. **Backend Client** (azure_openai_client.py)
4. **Backend Factory** (provider_factory.py)
5. **Backend Provider Client** (provider_client.py)
6. **Backend Requirements** (requirements.txt)
7. **Backend Tests** (test_azure_openai_*.py)
8. **Frontend Icons** (ProviderSelector.tsx)
9. **Frontend Types** (if needed)
10. **Documentation** (AZURE_OPENAI_INTEGRATION_README.md)
11. **Integration Testing**

---

## References

### Existing Implementations
- Gemini integration: `backend/llm/gemini_provider.py`
- Provider factory: `backend/llm/provider_factory.py`
- Provider client: `backend/llm/provider_client.py`
- Gemini documentation: `backend/GEMINI_INTEGRATION_README.md`

### External Documentation
- LangChain Azure OpenAI: https://python.langchain.com/docs/integrations/chat/azure_chat_openai
- Azure OpenAI Service: https://learn.microsoft.com/en-us/azure/ai-services/openai/
- OpenAI SDK: https://github.com/openai/openai-python

---

## Notes

- Azure OpenAI requires deployment names, unlike Gemini/Ollama direct model access
- API version must be specified for Azure OpenAI
- Endpoint format: `https://{resource-name}.openai.azure.com/`
- Consider adding Azure-specific icons for better UX
- Test with both deployment names and model names
- Document Azure setup process clearly for users
