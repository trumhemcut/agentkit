# LLM Provider Documentation

**Last Updated**: December 26, 2025

## Overview

The LLM provider system supports dynamic model selection, allowing users to choose different language models at runtime. Currently supports:
- **Ollama** - Local models (e.g., Qwen)
- **Gemini** - Google's Gemini models
- **Azure OpenAI** - Microsoft Azure-hosted OpenAI models

## Architecture

### Components

1. **OllamaProvider** (`llm/ollama_provider.py`) - LangChain Ollama integration
2. **GeminiProvider** (`llm/gemini_provider.py`) - LangChain Gemini integration
3. **AzureOpenAIProvider** (`llm/azure_openai_provider.py`) - LangChain Azure OpenAI integration
4. **LLMProviderFactory** (`llm/provider_factory.py`) - Provider instantiation
5. **OllamaClient** (`llm/ollama_client.py`) - Direct Ollama API interaction
6. **GeminiClient** (`llm/gemini_client.py`) - Gemini model listing
7. **AzureOpenAIClient** (`llm/azure_openai_client.py`) - Azure OpenAI model listing
8. **ProviderClient** (`llm/provider_client.py`) - Unified API for all providers

## Provider Factory

**File**: `backend/llm/provider_factory.py`

Factory pattern for creating LLM provider instances with optional model selection.

### Usage

```python
from llm.provider_factory import LLMProviderFactory

# Ollama provider
provider = LLMProviderFactory.get_provider("ollama", model="qwen:7b")

# Gemini provider
provider = LLMProviderFactory.get_provider("gemini", model="gemini-2.5-flash")

# Azure OpenAI provider
provider = LLMProviderFactory.get_provider("azure-openai", model="gpt-4")
```

### Implementation

```python
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
            return AzureOpenAIProvider(deployment=model)
        raise ValueError(f"Unknown provider: {provider_type}")
```

## Ollama Provider

**File**: `backend/llm/ollama_provider.py`

Wraps LangChain's ChatOllama with dynamic model selection.

### Features

- Dynamic model selection at initialization
- Streaming support
- Falls back to default model from settings

### Usage

```python
from llm.ollama_provider import OllamaProvider

# Use default model (qwen:7b from settings)
provider = OllamaProvider()
llm = provider.get_model()

# Use specific model
provider = OllamaProvider(model="qwen:4b")
llm = provider.get_model()

# Stream responses
async for chunk in llm.astream(messages):
    print(chunk.content)
```

### Implementation

```python
class OllamaProvider:
    def __init__(self, model: str = None):
        """
        Initialize Ollama provider with optional model parameter
        
        Args:
            model: Model name to use (e.g., "qwen:7b", "qwen:4b")
                   Falls back to settings.OLLAMA_MODEL if not provided
        """
        self.model = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=model or settings.OLLAMA_MODEL,
            streaming=True
        )
    
    def get_model(self):
        return self.model
```

## Ollama Client

**File**: `backend/llm/ollama_client.py`

Direct HTTP client for Ollama API to list available models and check availability.

### Features

- List all available Ollama models
- Parse model metadata (size, parameters)
- Check model availability
- Validate model names against allowed list
- Graceful error handling (connection errors, timeouts)

### Usage

```python
from llm.ollama_client import ollama_client

# List available models
models_data = await ollama_client.list_available_models()
# Returns:
# {
#   "models": [
#     {
#       "id": "qwen:4b",
#       "name": "Qwen 4B",
#       "size": "4B parameters",
#       "available": True,
#       "size_bytes": 2330093361
#     },
#     ...
#   ],
#   "default": "qwen:7b"
# }

# Check if specific model available
is_available = await ollama_client.check_model_available("qwen:7b")

# Validate model name
is_valid = ollama_client.is_valid_model("qwen:4b")
```

### Implementation

```python
class OllamaClient:
    """Client for interacting with Ollama API"""
    
    async def list_available_models(self) -> Dict[str, any]:
        """Query Ollama for available models"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                # Parse and structure models
                models = []
                for model_info in data["models"]:
                    # Extract and format model details
                    ...
                
                return {
                    "models": models,
                    "default": settings.OLLAMA_MODEL
                }
        except httpx.ConnectError:
            return {
                "models": [],
                "default": settings.OLLAMA_MODEL,
                "error": "Unable to connect to Ollama..."
            }
```

### Model Name Parsing

The client automatically parses Qwen model names to provide user-friendly labels:

- `qwen:4b` → "Qwen 4B" / "4B parameters"
- `qwen:7b` → "Qwen 7B" / "7B parameters"
- `qwen:14b` → "Qwen 14B" / "14B parameters"
- `qwen:32b` → "Qwen 32B" / "32B parameters"

### Error Handling

The client handles various error scenarios:

1. **Connection Error**: Ollama not running
   - Returns empty models list with error message
   - Uses default model from settings

2. **Timeout**: Request takes too long
   - Returns empty models list with timeout message
   
3. **Other Errors**: Parsing failures, etc.
   - Returns empty models list with error details

## Agent Integration

Agents accept optional model parameter during initialization:

### ChatAgent

```python
from agents.chat_agent import ChatAgent

# Default model
agent = ChatAgent()

# Specific model
agent = ChatAgent(model="qwen:4b")
```

### CanvasAgent

```python
from agents.canvas_agent import CanvasAgent

# Default model
agent = CanvasAgent()

# Specific model
agent = CanvasAgent(model="qwen:7b")
```

### Implementation Pattern

```python
class ChatAgent(BaseAgent):
    def __init__(self, model: str = None):
        """
        Initialize ChatAgent with optional model parameter
        
        Args:
            model: Model name to use (e.g., "qwen:7b", "qwen:4b")
                   Falls back to default if not provided
        """
        provider = LLMProviderFactory.get_provider("ollama", model=model)
        self.llm = provider.get_model()
```

## API Integration

### Request Models

Both chat and canvas endpoints accept optional `model` field:

**File**: `backend/api/models.py`

```python
class RunAgentInput(BaseModel):
    thread_id: str
    run_id: str
    messages: List[Message]
    model: Optional[str] = None  # Optional model selection

class CanvasMessageRequest(BaseModel):
    thread_id: str
    run_id: str
    messages: List[Message]
    artifact: Optional[ArtifactV3] = None
    selectedText: Optional[SelectedText] = None
    action: Optional[str] = None
    model: Optional[str] = None  # Optional model selection
```

### Endpoints

#### GET /api/models

List all available Ollama models.

**Response**:
```json
{
  "models": [
    {
      "id": "qwen:4b",
      "name": "Qwen 4B",
      "size": "4B parameters",
      "available": true,
      "size_bytes": 2330093361
    },
    {
      "id": "qwen:7b",
      "name": "Qwen 7B",
      "size": "7B parameters",
      "available": true,
      "size_bytes": 4511914544
    }
  ],
  "default": "qwen:7b"
}
```

**Error Response**:
```json
{
  "models": [],
  "default": "qwen:7b",
  "error": "Unable to connect to Ollama. Please ensure Ollama is running."
}
```

**Implementation**:
```python
@router.get("/models")
async def list_models():
    """List available Ollama models"""
    try:
        models_data = await ollama_client.list_available_models()
        return models_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")
```

#### POST /api/chat

Send chat message with optional model selection.

**Request**:
```json
{
  "thread_id": "thread-123",
  "run_id": "run-456",
  "messages": [...],
  "model": "qwen:4b"
}
```

**Implementation**:
```python
@router.post("/chat")
async def chat_endpoint(input_data: RunAgentInput, request: Request):
    # Create agent with optional model
    chat_agent = ChatAgent(model=input_data.model)
    
    # Stream responses
    async for event in chat_agent.run(state):
        yield encoder.encode(event)
```

#### POST /api/canvas/stream

Send canvas message with optional model selection.

**Request**:
```json
{
  "thread_id": "thread-123",
  "run_id": "run-456",
  "messages": [...],
  "artifact": {...},
  "action": "create",
  "model": "qwen:7b"
}
```

**Implementation**:
```python
@router.post("/canvas/stream")
async def canvas_stream_endpoint(input_data: CanvasMessageRequest, request: Request):
    if route == "artifact_action":
        # Use canvas agent with optional model
        canvas_agent = CanvasAgent(model=input_data.model)
    else:
        # Use chat agent with optional model
        chat_agent = ChatAgent(model=input_data.model)
```

## Configuration

**File**: `backend/config.py`

```python
class Settings(BaseSettings):
    # LLM settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen:7b"  # Default model
```

### Environment Variables

Set via `.env` file:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

## Supported Models

Currently supported Qwen models:

| Model ID | Display Name | Parameters | Use Case |
|----------|-------------|------------|----------|
| qwen:4b  | Qwen 4B     | 4B         | Faster responses, lower resource usage |
| qwen:7b  | Qwen 7B     | 7B         | Balanced performance (default) |
| qwen:14b | Qwen 14B    | 14B        | Better quality, more resources |
| qwen:32b | Qwen 32B    | 32B        | Highest quality, requires powerful hardware |

## Adding New Models

To support additional models:

1. **Pull model in Ollama**:
   ```bash
   ollama pull model-name:tag
   ```

2. **Update validation** (optional):
   ```python
   # In ollama_client.py
   def is_valid_model(self, model_name: str):
       allowed_models = [
           "qwen:4b",
           "qwen:7b",
           "new-model:tag"  # Add here
       ]
   ```

3. **Update parsing** (for custom display names):
   ```python
   # In ollama_client.py - list_available_models()
   if "new-model" in model_name.lower():
       display_name = "Custom Model Name"
       size_label = "Size info"
   ```

## Dependencies

**File**: `backend/requirements.txt`

```txt
langchain-ollama==0.2.0  # LangChain Ollama integration
httpx==0.27.0            # Async HTTP client for Ollama API
```

## Testing

### Test Model Listing

```bash
cd backend
python -c "import asyncio; from llm.ollama_client import ollama_client; print(asyncio.run(ollama_client.list_available_models()))"
```

### Test Agent with Model

```python
from agents.chat_agent import ChatAgent

# Test with specific model
agent = ChatAgent(model="qwen:4b")
state = {
    "messages": [{"role": "user", "content": "Hello"}],
    "thread_id": "test",
    "run_id": "test"
}

async for event in agent.run(state):
    print(event)
```

## Best Practices

1. **Model Selection**
   - Let frontend users choose model via UI
   - Fall back to default if model not specified
   - Validate model exists before using

2. **Error Handling**
   - Handle Ollama connection failures gracefully
   - Return meaningful error messages
   - Don't crash on invalid model names

3. **Performance**
   - Smaller models (4B) for faster responses
   - Larger models (7B+) for better quality
   - Consider user's hardware capabilities

4. **Configuration**
   - Set sensible defaults in config
   - Allow override via environment variables
   - Document supported models

---

## Azure OpenAI Provider

**File**: `backend/llm/azure_openai_provider.py`

Wraps LangChain's AzureChatOpenAI for integration with Microsoft Azure-hosted OpenAI models.

### Features

- Support for GPT-4, GPT-3.5, and other Azure OpenAI models
- Deployment-based model access
- Streaming support
- Configurable API version

### Usage

```python
from llm.azure_openai_provider import AzureOpenAIProvider

# Use configured deployment
provider = AzureOpenAIProvider()
llm = provider.get_model()

# Use specific deployment
provider = AzureOpenAIProvider(deployment="gpt-4-deployment")
llm = provider.get_model()

# Use specific model
provider = AzureOpenAIProvider(model="gpt-4")
llm = provider.get_model()
```

### Implementation

```python
class AzureOpenAIProvider:
    def __init__(self, model: str = None, deployment: str = None):
        """
        Initialize Azure OpenAI provider
        
        Args:
            model: Model name (e.g., "gpt-4", "gpt-35-turbo", "gpt-4o")
            deployment: Azure deployment name (overrides settings)
        """
        deployment_name = deployment or settings.AZURE_OPENAI_DEPLOYMENT
        model_name = model or settings.AZURE_OPENAI_MODEL
        
        self.model = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            openai_api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=deployment_name,
            openai_api_key=settings.AZURE_OPENAI_API_KEY,
            model=model_name,
            streaming=True,
            temperature=0.7
        )
    
    def get_model(self):
        return self.model
```

### Configuration

**Settings** (`backend/config.py`):

```python
class Settings(BaseSettings):
    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT: str = ""
    AZURE_OPENAI_MODEL: str = "gpt-4"
```

**Environment Variables** (`.env`):

```bash
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4-deployment
AZURE_OPENAI_MODEL=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Azure OpenAI Client

**File**: `backend/llm/azure_openai_client.py`

Provides model listing functionality for Azure OpenAI.

**Key Points**:
- Azure OpenAI uses deployments, not direct model listing
- Returns configured deployment + common Azure models
- Graceful error handling for missing credentials

```python
class AzureOpenAIClient:
    def list_models(self):
        """
        List available Azure OpenAI models/deployments
        
        Returns:
            dict: Models list, default model, and any errors
        """
        models = []
        
        # Add configured deployment
        if settings.AZURE_OPENAI_DEPLOYMENT:
            models.append({
                "id": settings.AZURE_OPENAI_DEPLOYMENT,
                "name": f"{settings.AZURE_OPENAI_MODEL} (Deployment)",
                "provider": "azure-openai",
                "is_deployment": True
            })
        
        # Add common models
        common_models = ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-35-turbo"]
        for model_id in common_models:
            models.append({
                "id": model_id,
                "name": model_id.upper(),
                "provider": "azure-openai",
                "is_deployment": False
            })
        
        return {"models": models, "default": settings.AZURE_OPENAI_DEPLOYMENT}
```

### Supported Models

| Model ID | Name | Description |
|----------|------|-------------|
| `gpt-4` | GPT-4 | Most capable GPT-4 model |
| `gpt-4-turbo` | GPT-4 Turbo | Faster GPT-4 with 128k context |
| `gpt-4o` | GPT-4o | Latest multimodal GPT-4 model |
| `gpt-35-turbo` | GPT-3.5 Turbo | Fast and efficient model |
| `gpt-4-32k` | GPT-4 32K | GPT-4 with extended context |

**Note**: Availability depends on Azure region and subscription.

### Azure Setup Guide

1. **Create Azure OpenAI Resource**
   - Go to Azure Portal
   - Create Azure OpenAI resource
   - Note endpoint URL

2. **Deploy Model**
   - Go to Model deployments
   - Create new deployment
   - Select model (e.g., GPT-4)
   - Name deployment

3. **Get Credentials**
   - Go to Keys and Endpoint
   - Copy API key
   - Copy endpoint URL

4. **Configure AgentKit**
   - Add credentials to `.env`
   - Restart backend

### Dependencies

**File**: `backend/requirements.txt`

```txt
langchain-openai>=0.2.0  # LangChain Azure OpenAI integration
openai>=1.0.0            # Official OpenAI SDK (supports Azure)
azure-identity>=1.15.0   # Azure authentication
```

---

## Provider Client (Unified API)

**File**: `backend/llm/provider_client.py`

Unified client that aggregates models from all providers (Ollama, Gemini, Azure OpenAI).

### Usage

```python
from llm.provider_client import provider_client

# List all models from all providers
data = await provider_client.list_all_models()

# List models from specific provider
ollama_models = await provider_client.get_models_by_provider("ollama")
gemini_models = await provider_client.get_models_by_provider("gemini")
azure_models = await provider_client.get_models_by_provider("azure-openai")
```

### Response Format

```json
{
  "providers": [
    {"id": "ollama", "name": "Ollama", "available": true},
    {"id": "gemini", "name": "Gemini", "available": true},
    {"id": "azure-openai", "name": "Azure OpenAI", "available": true}
  ],
  "models": [
    {
      "id": "qwen:7b",
      "name": "Qwen 7B",
      "provider": "ollama",
      "available": true
    },
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "provider": "azure-openai",
      "available": true
    }
  ],
  "default_provider": "ollama",
  "default_model": "qwen:7b",
  "errors": []
}
```

### Error Handling

- Graceful degradation if a provider is unavailable
- Returns errors per provider
- Other providers continue to work

---

## Future Enhancements

- Support for additional providers (Anthropic Claude, etc.)
- Model performance metrics display
- Automatic model selection based on query complexity
- Model caching and optimization
- Multi-model ensemble responses
- Provider health monitoring
- Cost tracking for cloud providers
