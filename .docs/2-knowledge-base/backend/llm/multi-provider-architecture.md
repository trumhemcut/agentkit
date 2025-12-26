# LLM Providers - Multi-Provider Architecture

## Overview
AgentKit supports multiple LLM providers through a unified architecture that allows seamless switching between different providers and their models.

## Supported Providers

### 1. Ollama (Local)
- **Type**: Local model hosting
- **Default Model**: `qwen:7b`
- **Configuration**: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`
- **Use Case**: Local development, privacy-sensitive applications

### 2. Gemini (Cloud)
- **Type**: Google Cloud API
- **Default Model**: `gemini-1.5-flash`
- **Configuration**: `GEMINI_API_KEY`, `GEMINI_MODEL`
- **Use Case**: Production applications, advanced capabilities

## Architecture

```
Frontend (Provider + Model Selection)
    ↓
API Request (provider + model parameters)
    ↓
ProviderClient (Aggregates all providers)
    ↓
ProviderFactory (Creates provider instance)
    ↓
Agent (Uses LLM from provider)
    ↓
LLM Response (Streaming)
```

## Core Components

### 1. Provider Factory
**Location**: `backend/llm/provider_factory.py`

Responsible for creating provider instances based on type:
```python
LLMProviderFactory.get_provider(
    provider_type="gemini",
    model="gemini-1.5-flash"
)
```

### 2. Provider Implementations

#### Ollama Provider
**Location**: `backend/llm/ollama_provider.py`
- Uses `langchain-ollama` library
- Connects to local Ollama server
- Supports streaming responses

#### Gemini Provider
**Location**: `backend/llm/gemini_provider.py`
- Uses `langchain-google-genai` library
- Connects to Google AI API
- Requires API key authentication

### 3. Provider Clients

#### Ollama Client
**Location**: `backend/llm/ollama_client.py`
- Queries local Ollama server for available models
- Returns model metadata (name, size, parameters)

#### Gemini Client
**Location**: `backend/llm/gemini_client.py`
- Queries Google AI API for available models
- Filters to text generation models
- Handles authentication errors

### 4. Unified Provider Client
**Location**: `backend/llm/provider_client.py`

Aggregates models from all providers:
```python
provider_client.list_all_models()  # All providers
provider_client.get_models_by_provider("gemini")  # Specific provider
```

## Configuration

### Environment Variables

```bash
# Default Settings
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=qwen:7b

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b

# Gemini Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

### Config Schema
**Location**: `backend/config.py`

```python
class Settings(BaseSettings):
    # Provider defaults
    DEFAULT_PROVIDER: str = "ollama"
    DEFAULT_MODEL: str = "qwen:7b"
    
    # Provider-specific settings
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
```

## Agent Integration

### Agent Initialization

Both `ChatAgent` and `CanvasAgent` accept provider parameters:

```python
from agents.chat_agent import ChatAgent

agent = ChatAgent(
    provider="gemini",
    model="gemini-1.5-flash"
)
```

### Agent Base Pattern

```python
def __init__(self, model: str = None, provider: str = None):
    self.provider_type = provider or settings.DEFAULT_PROVIDER
    self.model_name = model or settings.DEFAULT_MODEL
    
    provider_instance = LLMProviderFactory.get_provider(
        provider_type=self.provider_type,
        model=self.model_name
    )
    self.llm = provider_instance.get_model()
```

## API Contract

### Models Endpoint
**GET** `/models`

Returns all providers and their models:
```json
{
  "providers": [
    {"id": "ollama", "name": "Ollama", "available": true},
    {"id": "gemini", "name": "Gemini", "available": true}
  ],
  "models": [
    {
      "id": "qwen:7b",
      "name": "Qwen 7B",
      "size": "7B parameters",
      "available": true,
      "provider": "ollama"
    },
    {
      "id": "gemini-1.5-flash",
      "name": "Gemini 1.5 Flash",
      "size": "Google Cloud",
      "available": true,
      "provider": "gemini"
    }
  ],
  "default_provider": "ollama",
  "default_model": "qwen:7b"
}
```

### Provider-Specific Models
**GET** `/models/{provider}`

Returns models for specific provider:
```json
{
  "models": [
    {
      "id": "gemini-1.5-flash",
      "name": "Gemini 1.5 Flash",
      "size": "Google Cloud",
      "available": true,
      "provider": "gemini"
    }
  ]
}
```

### Chat Request
**POST** `/chat/{agent_id}`

Include provider in request:
```json
{
  "thread_id": "uuid",
  "run_id": "uuid",
  "messages": [...],
  "provider": "gemini",
  "model": "gemini-1.5-flash",
  "agent": "chat"
}
```

## Request Models

### RunAgentInput
**Location**: `backend/api/models.py`

```python
class RunAgentInput(BaseModel):
    thread_id: str
    run_id: str
    messages: List[Message]
    provider: Optional[str] = None  # Provider selection
    model: Optional[str] = None     # Model selection
    agent: Optional[str] = "chat"
```

## Error Handling

### Provider Unavailable
- Provider marked as unavailable in response
- Error details in `errors` array
- Other providers remain functional

### Invalid API Key
- Gemini provider not listed as available
- Clear error message to user
- Graceful fallback to available providers

### Model Not Found
- Validation against available models
- Fall back to default model
- Log warning for debugging

## Adding New Providers

### Step 1: Create Provider Class
**Location**: `backend/llm/{provider_name}_provider.py`

```python
from langchain_{provider} import Chat{Provider}

class {Provider}Provider:
    def __init__(self, model: str = None):
        self.model = Chat{Provider}(
            model=model or settings.{PROVIDER}_MODEL,
            # Provider-specific config
        )
    
    def get_model(self):
        return self.model
```

### Step 2: Create Client Class
**Location**: `backend/llm/{provider_name}_client.py`

```python
class {Provider}Client:
    async def list_available_models(self) -> Dict:
        # Query provider API
        # Return structured model list
        return {
            "models": [...],
            "default": settings.{PROVIDER}_MODEL
        }

{provider}_client = {Provider}Client()
```

### Step 3: Update Provider Factory
**Location**: `backend/llm/provider_factory.py`

```python
from llm.{provider}_provider import {Provider}Provider

def get_provider(provider_type: str, model: str = None):
    if provider_type == "{provider}":
        return {Provider}Provider(model=model)
    # ... existing providers
```

### Step 4: Update Provider Client
**Location**: `backend/llm/provider_client.py`

```python
from llm.{provider}_client import {provider}_client

async def list_all_models(self, provider_filter: Optional[str] = None):
    # Add provider to aggregation
    if not provider_filter or provider_filter == "{provider}":
        {provider}_data = await {provider}_client.list_available_models()
        # Process and add to all_models
```

### Step 5: Update Configuration
**Location**: `backend/config.py`

```python
class Settings(BaseSettings):
    # {Provider} settings
    {PROVIDER}_API_KEY: str = ""
    {PROVIDER}_MODEL: str = "default-model"
```

### Step 6: Update Requirements
Add provider's LangChain integration to `requirements.txt`

## Best Practices

### Provider Selection
- Default to Ollama for local development
- Use Gemini for production (better performance)
- Consider cost implications for cloud providers

### Model Selection
- Start with default models (tested and reliable)
- Test custom models before production use
- Monitor token usage for cloud providers

### Error Handling
- Always handle provider unavailability
- Provide fallback mechanisms
- Log errors for debugging

### Configuration
- Use environment variables for secrets
- Provide sensible defaults
- Document all configuration options

## Testing

### Unit Tests
- Test each provider independently
- Mock external API calls
- Verify error handling

### Integration Tests
- Test provider switching
- Verify model listing
- Test end-to-end chat flow

### Manual Testing
```bash
# Test Ollama
curl http://localhost:8000/models/ollama

# Test Gemini
curl http://localhost:8000/models/gemini

# Test chat with Gemini
curl -X POST http://localhost:8000/chat/chat \
  -d '{"messages": [...], "provider": "gemini"}'
```

## Troubleshooting

### Provider Not Available
1. Check environment variables
2. Verify service is running (Ollama) or API key is valid (Gemini)
3. Review logs for connection errors

### Model Not Found
1. Verify model name matches exactly
2. Check `/models/{provider}` endpoint
3. Ensure model is available for provider

### Streaming Issues
1. Verify provider supports streaming
2. Check network connectivity
3. Review timeout settings

## Related Documentation
- [Gemini Integration](./GEMINI_INTEGRATION_README.md)
- [Model Selection](./llm-model-selection.md)
- [Implementation Plan](/.docs/1-implementation-plans/012-support-gemini.md)
