# LLM Model Selection - Backend Implementation

**Status**: ✅ Complete  
**Date**: December 23, 2025

## Overview

This implementation adds dynamic LLM model selection support to the backend, allowing users to choose different models (e.g., qwen:4b, qwen:7b) for chat and canvas interactions.

## What Was Implemented

### 1. New Files

- **`backend/llm/ollama_client.py`** - HTTP client for Ollama API
  - Lists available models
  - Checks model availability
  - Validates model names
  - Handles connection errors

- **`backend/tests/test_model_selection.py`** - Test suite for model selection
  - Tests Ollama client
  - Tests provider factory
  - Tests agent initialization
  - Tests model validation

### 2. Modified Files

- **`backend/llm/ollama_provider.py`**
  - Added `model` parameter to `__init__()`
  - Falls back to default if not provided

- **`backend/llm/provider_factory.py`**
  - Added `model` parameter to `get_provider()`
  - Passes model to provider instances

- **`backend/agents/chat_agent.py`**
  - Added `model` parameter to `__init__()`
  - Creates provider with specified model

- **`backend/agents/canvas_agent.py`**
  - Added `model` parameter to `__init__()`
  - Creates provider with specified model

- **`backend/api/models.py`**
  - Added `model: Optional[str]` field to `RunAgentInput`
  - Added `model: Optional[str]` field to `CanvasMessageRequest`

- **`backend/api/routes.py`**
  - Added `GET /api/models` endpoint to list available models
  - Updated chat endpoint to pass model to `ChatAgent`
  - Updated canvas endpoint to pass model to `CanvasAgent`

- **`backend/requirements.txt`**
  - Added `httpx==0.27.0` for Ollama API client

### 3. Documentation

- **`.docs/2-knowledge-base/backend/llm/providers.md`**
  - Comprehensive LLM provider documentation
  - OllamaClient usage and API
  - Model selection patterns

- **`.docs/2-knowledge-base/backend/api/models.md`**
  - API models documentation
  - Model parameter usage
  - Request/response examples

- **`.docs/2-knowledge-base/llm-model-selection.md`**
  - Feature overview
  - Architecture diagram
  - Data flow
  - Testing guide

## New API Endpoint

### GET /api/models

Returns list of available Ollama models.

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

## Updated API Endpoints

### POST /api/chat

Now accepts optional `model` parameter:

**Request**:
```json
{
  "thread_id": "thread-123",
  "run_id": "run-456",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "model": "qwen:4b"
}
```

### POST /api/canvas/stream

Now accepts optional `model` parameter:

**Request**:
```json
{
  "thread_id": "canvas-123",
  "run_id": "run-456",
  "messages": [...],
  "artifact": {...},
  "action": "create",
  "model": "qwen:7b"
}
```

## Testing

Run the test suite:

```bash
cd backend
python tests/test_model_selection.py
```

**Expected Output**:
```
============================================================
LLM Model Selection - Backend Implementation Test
============================================================

=== Testing Ollama Client ===
✅ Found 4 models
   Default model: qwen:7b
   - Qwen 4B (qwen:4b) - 4B parameters
   - Qwen 7B (qwen:7b) - 7B parameters

=== Testing Provider Factory ===
✅ Created provider with default model
✅ Created provider with qwen:4b model
✅ Created provider with qwen:7b model

=== Testing Agent Initialization ===
✅ Created ChatAgent with default model
✅ Created ChatAgent with qwen:4b
✅ Created CanvasAgent with default model
✅ Created CanvasAgent with qwen:7b

=== Testing Model Validation ===
✅ qwen:7b available: True
✅ qwen:4b available: True

============================================================
Test Summary
============================================================
✅ PASS - Ollama Client
✅ PASS - Provider Factory
✅ PASS - Agent Initialization
✅ PASS - Model Validation

Passed: 4/4

🎉 All tests passed! Backend implementation is complete.
```

## Manual Testing

### Test Model Listing

```bash
curl http://localhost:8000/api/models
```

### Test Chat with Model

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "qwen:4b"
  }'
```

### Test Ollama Client Directly

```bash
cd backend
python -c "
import asyncio
from llm.ollama_client import ollama_client
print(asyncio.run(ollama_client.list_available_models()))
"
```

## Configuration

**Default model** set in `backend/config.py`:
```python
OLLAMA_MODEL: str = "qwen:7b"
```

Override with environment variable:
```bash
export OLLAMA_MODEL=qwen:4b
```

## Dependencies

**New dependency added**:
- `httpx==0.27.0` - Async HTTP client for Ollama API

Install with:
```bash
pip install httpx==0.27.0
```

Or install all dependencies:
```bash
cd backend
pip install -r requirements.txt
```

## Supported Models

| Model ID | Display Name | Parameters | Use Case |
|----------|-------------|------------|----------|
| qwen:4b  | Qwen 4B     | 4B         | Faster responses, lower resource usage |
| qwen:7b  | Qwen 7B     | 7B         | Balanced performance (default) |
| qwen:14b | Qwen 14B    | 14B        | Better quality, more resources |
| qwen:32b | Qwen 32B    | 32B        | Highest quality, powerful hardware needed |

## Error Handling

### Ollama Not Running

**Response**:
```json
{
  "models": [],
  "default": "qwen:7b",
  "error": "Unable to connect to Ollama. Please ensure Ollama is running."
}
```

### Invalid Model

- Agent creation will fail if model doesn't exist
- Ollama returns error during generation
- Error captured in AG-UI RUN_ERROR event

## Next Steps

### Frontend Implementation

The backend is complete. Next, implement the frontend:

1. **Create ModelSelector component** (`frontend/components/ModelSelector.tsx`)
2. **Create useModelSelection hook** (`frontend/hooks/useModelSelection.ts`)
3. **Update Header component** (`frontend/components/Header.tsx`)
4. **Update API service** (`frontend/services/api.ts`)
5. **Update chat/canvas hooks** to pass model parameter

See [implementation plan](.docs/1-implementation-plans/004-llm-model-selection.md) for details.

## Documentation

- [LLM Providers](../.docs/2-knowledge-base/backend/llm/providers.md)
- [API Models](../.docs/2-knowledge-base/backend/api/models.md)
- [Model Selection Feature](../.docs/2-knowledge-base/llm-model-selection.md)
- [Implementation Plan](../.docs/1-implementation-plans/004-llm-model-selection.md)

## Architecture

```
Frontend Request
      │
      ▼
POST /api/chat
{model: "qwen:4b"}
      │
      ▼
ChatAgent(model="qwen:4b")
      │
      ▼
LLMProviderFactory.get_provider("ollama", model="qwen:4b")
      │
      ▼
OllamaProvider(model="qwen:4b")
      │
      ▼
ChatOllama(model="qwen:4b")
      │
      ▼
Ollama Server
```

## Backward Compatibility

✅ **Fully backward compatible**

- If `model` parameter not provided, uses default from config
- Existing API calls work without changes
- No breaking changes to existing functionality

## Summary

✅ Backend implementation complete  
✅ All tests passing  
✅ Documentation written  
✅ Backward compatible  
⏳ Frontend implementation pending

The backend now supports dynamic model selection. Users can specify which model to use for each chat or canvas request, enabling flexibility in balancing response speed vs. quality.
