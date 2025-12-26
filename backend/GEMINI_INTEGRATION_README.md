# Gemini Provider Integration - Backend Implementation

## Overview
This document describes the backend implementation of Gemini provider support for AgentKit. The implementation adds Google Gemini as a new LLM provider alongside Ollama, enabling users to select between different providers and their models.

## Architecture Changes

### Provider System Architecture
```
┌─────────────────────┐
│   API Routes        │
│  /models            │ → Returns all providers & models
│  /models/{provider} │ → Returns provider-specific models
│  /chat/{agent_id}   │ → Accepts provider parameter
└─────────────────────┘
         ↓
┌─────────────────────┐
│  ProviderClient     │ → Aggregates models from all providers
└─────────────────────┘
         ↓
    ┌────────┴────────┐
    ↓                 ↓
┌──────────┐    ┌──────────┐
│ Ollama   │    │ Gemini   │
│ Client   │    │ Client   │
└──────────┘    └──────────┘
    ↓                 ↓
┌──────────┐    ┌──────────┐
│ Ollama   │    │ Gemini   │
│ Provider │    │ Provider │
└──────────┘    └──────────┘
```

## Files Created

### 1. `backend/llm/gemini_provider.py`
**Purpose**: LangChain provider wrapper for Gemini models

**Key Features**:
- Uses `langchain-google-genai` library
- Supports streaming responses
- Accepts model name and API key from config
- Default model: `gemini-1.5-flash`

**Usage**:
```python
from llm.gemini_provider import GeminiProvider

provider = GeminiProvider(model="gemini-1.5-flash")
llm = provider.get_model()
```

### 2. `backend/llm/gemini_client.py`
**Purpose**: Direct API client for listing available Gemini models

**Key Features**:
- Queries Google AI API for available models
- Filters to text generation models only
- Handles authentication errors gracefully
- Returns structured model metadata

**API Response Format**:
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
  ],
  "default": "gemini-1.5-flash"
}
```

### 3. `backend/llm/provider_client.py`
**Purpose**: Unified client aggregating models from all providers

**Key Features**:
- Lists models from all providers or specific provider
- Handles provider-specific errors
- Returns unified structure for frontend
- Global singleton instance

**API Response Format**:
```json
{
  "providers": [
    {"id": "ollama", "name": "Ollama", "available": true},
    {"id": "gemini", "name": "Gemini", "available": true}
  ],
  "models": [...],
  "default_provider": "ollama",
  "default_model": "qwen:7b",
  "errors": null
}
```

## Files Modified

### 1. `backend/config.py`
**Changes**: Added Gemini configuration settings

```python
# LLM settings - Ollama
OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_MODEL: str = "qwen:7b"

# LLM settings - Gemini
GEMINI_API_KEY: str = ""
GEMINI_MODEL: str = "gemini-1.5-flash"

# Default provider
DEFAULT_PROVIDER: str = "ollama"
DEFAULT_MODEL: str = "qwen:7b"
```

### 2. `backend/llm/provider_factory.py`
**Changes**: Added Gemini to provider factory

```python
def get_provider(provider_type: str = "ollama", model: str = None):
    if provider_type == "ollama":
        return OllamaProvider(model=model)
    elif provider_type == "gemini":
        return GeminiProvider(model=model)
    raise ValueError(f"Unknown provider: {provider_type}")
```

### 3. `backend/api/routes.py`
**Changes**: 
- Updated `/models` endpoint to use `provider_client`
- Added `/models/{provider}` endpoint for provider-specific models

```python
@router.get("/models")
async def list_models():
    """List available models from all providers"""
    models_data = await provider_client.list_all_models()
    return models_data

@router.get("/models/{provider}")
async def list_provider_models(provider: str):
    """List models from a specific provider"""
    models = await provider_client.get_models_by_provider(provider)
    return {"models": models}
```

### 4. `backend/api/models.py`
**Changes**: Added `provider` field to request models

```python
class RunAgentInput(BaseModel):
    thread_id: str
    run_id: str
    messages: List[Message]
    model: Optional[str] = None
    provider: Optional[str] = None  # NEW
    agent: Optional[str] = "chat"
    # ... other fields
```

### 5. `backend/agents/chat_agent.py`
**Changes**: Added provider parameter to initialization

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

### 6. `backend/agents/canvas_agent.py`
**Changes**: Same as ChatAgent - added provider parameter

### 7. `backend/requirements.txt`
**Changes**: Added `langchain-google-genai` dependency

```
langchain-google-genai
```

### 8. `backend/.env.example`
**Changes**: Added Gemini environment variables

```bash
# LLM Provider Settings
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=qwen:7b

# Gemini Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Default Provider Settings
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=qwen:7b

# Gemini Configuration (optional)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
```

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env` file

## API Changes

### Models Endpoint (Updated)

**Request**: `GET /models`

**Response**:
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
  "default_model": "qwen:7b",
  "errors": null
}
```

### Provider Models Endpoint (New)

**Request**: `GET /models/{provider}`

**Response**:
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

### Chat Endpoint (Updated)

**Request**: `POST /chat/{agent_id}`

```json
{
  "thread_id": "uuid",
  "run_id": "uuid",
  "messages": [...],
  "provider": "gemini",  // NEW
  "model": "gemini-1.5-flash",
  "agent": "chat"
}
```

## Installation & Setup

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. **Run the server**:
```bash
python main.py
```

## Testing

### Manual Testing

1. **Test model listing**:
```bash
curl http://localhost:8000/models
```

2. **Test Gemini models**:
```bash
curl http://localhost:8000/models/gemini
```

3. **Test chat with Gemini**:
```bash
curl -X POST http://localhost:8000/chat/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "provider": "gemini",
    "model": "gemini-1.5-flash"
  }'
```

## Error Handling

### Invalid Gemini API Key
If `GEMINI_API_KEY` is invalid or empty:
- Gemini provider won't be listed as available
- Error message returned in `errors` array
- Ollama remains available (graceful degradation)

### Provider Unavailable
If a provider is down:
- Other providers remain functional
- Error logged but doesn't break app
- Frontend can fallback to available providers

## Migration Guide

### For Existing Installations

1. **Update dependencies**:
```bash
pip install langchain-google-genai
```

2. **Add environment variables** (optional):
```bash
# .env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=qwen:7b
```

3. **No code changes needed** - backward compatible with existing installations

### Default Behavior

- Without Gemini API key: Only Ollama available (existing behavior)
- With Gemini API key: Both providers available
- Default provider: Ollama (unless changed in config)

## Next Steps

### Frontend Implementation
The backend implementation is complete. Next, implement frontend changes:

1. Update TypeScript types for provider support
2. Create ProviderSelector component
3. Update ModelSelector to filter by provider
4. Update API client to send provider parameter
5. Update Zustand store for provider state

See: `.docs/1-implementation-plans/012-support-gemini.md` (Frontend section)

## Troubleshooting

### Gemini models not showing
- Check `GEMINI_API_KEY` in `.env`
- Verify API key is valid
- Check logs for API errors

### Provider selection not working
- Verify frontend sends `provider` parameter
- Check agent initialization includes provider
- Review logs for provider factory errors

### Model not found
- Ensure model name matches exactly
- Check model availability via `/models` endpoint
- Verify provider supports the model

## Additional Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [LangChain Google GenAI](https://python.langchain.com/docs/integrations/chat/google_generative_ai)
- [Implementation Plan](/.docs/1-implementation-plans/012-support-gemini.md)
