# LLM Model Selection Feature

**Last Updated**: December 23, 2025  
**Status**: ✅ Backend Implemented | ⏳ Frontend Pending

## Overview

This feature allows users to select different LLM models during chat and canvas interactions, similar to ChatGPT's model selector UI.

## Backend Implementation

### ✅ Completed Components

#### 1. Ollama Client (`backend/llm/ollama_client.py`)

**Purpose**: Direct HTTP client to interact with Ollama API

**Features**:
- Lists available Ollama models via `/api/tags` endpoint
- Parses model metadata (size, parameters)
- Provides user-friendly display names
- Handles connection errors gracefully
- Validates model names

**Key Methods**:
```python
# List all available models
await ollama_client.list_available_models()

# Check if model is available
await ollama_client.check_model_available("qwen:7b")

# Validate model name
ollama_client.is_valid_model("qwen:4b")
```

#### 2. Updated Ollama Provider (`backend/llm/ollama_provider.py`)

**Changes**: Accepts optional `model` parameter

```python
# Before
provider = OllamaProvider()

# After - dynamic model selection
provider = OllamaProvider(model="qwen:4b")
```

#### 3. Updated Provider Factory (`backend/llm/provider_factory.py`)

**Changes**: Passes model parameter to providers

```python
LLMProviderFactory.get_provider("ollama", model="qwen:7b")
```

#### 4. Updated Agents

**ChatAgent** (`backend/agents/chat_agent.py`):
```python
agent = ChatAgent(model="qwen:4b")
```

**CanvasAgent** (`backend/agents/canvas_agent.py`):
```python
agent = CanvasAgent(model="qwen:7b")
```

#### 5. Updated API Models (`backend/api/models.py`)

**Added `model` field to request models**:

```python
class RunAgentInput(BaseModel):
    thread_id: str
    run_id: str
    messages: List[Message]
    model: Optional[str] = None  # NEW

class CanvasMessageRequest(BaseModel):
    thread_id: str
    run_id: str
    messages: List[Message]
    artifact: Optional[ArtifactV3] = None
    selectedText: Optional[SelectedText] = None
    action: Optional[str] = None
    model: Optional[str] = None  # NEW
```

#### 6. New API Endpoint (`backend/api/routes.py`)

**GET /api/models**: List available models

```python
@router.get("/models")
async def list_models():
    """List available Ollama models"""
    models_data = await ollama_client.list_available_models()
    return models_data
```

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

#### 7. Updated Chat & Canvas Routes

**Changes**: Pass model from request to agents

```python
# Chat endpoint
chat_agent = ChatAgent(model=input_data.model)

# Canvas endpoint
canvas_agent = CanvasAgent(model=input_data.model)
```

### Dependencies

**Added to `requirements.txt`**:
```
httpx==0.27.0  # For Ollama API client
```

---

## API Contract

### GET /api/models

**Purpose**: List available Ollama models

**Response**:
```typescript
{
  models: Array<{
    id: string;
    name: string;
    size: string;
    available: boolean;
    size_bytes: number;
  }>;
  default: string;
  error?: string;  // Present if Ollama connection failed
}
```

### POST /api/chat

**Request** (new field):
```json
{
  "thread_id": "thread-123",
  "run_id": "run-456",
  "messages": [...],
  "model": "qwen:7b"  // NEW - optional
}
```

### POST /api/canvas/stream

**Request** (new field):
```json
{
  "thread_id": "thread-123",
  "run_id": "run-456",
  "messages": [...],
  "artifact": {...},
  "action": "create",
  "model": "qwen:4b"  // NEW - optional
}
```

---

## Supported Models

| Model ID | Display Name | Parameters | Use Case |
|----------|-------------|------------|----------|
| qwen:4b  | Qwen 4B     | 4B         | Faster responses |
| qwen:7b  | Qwen 7B     | 7B         | Balanced (default) |
| qwen:14b | Qwen 14B    | 14B        | Better quality |
| qwen:32b | Qwen 32B    | 32B        | Highest quality |

---

## Testing

### Test Backend Implementation

**1. Test Model Listing**:
```bash
cd backend
python -c "import asyncio; from llm.ollama_client import ollama_client; print(asyncio.run(ollama_client.list_available_models()))"
```

**Expected Output**:
```python
{
  'models': [
    {'id': 'qwen:4b', 'name': 'Qwen 4B', 'size': '4B parameters', ...},
    {'id': 'qwen:7b', 'name': 'Qwen 7B', 'size': '7B parameters', ...}
  ],
  'default': 'qwen:7b'
}
```

**2. Test API Endpoint**:
```bash
# Start backend server
cd backend
uvicorn main:app --reload

# In another terminal
curl http://localhost:8000/api/models
```

**3. Test Chat with Model**:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "qwen:4b"
  }'
```

---

## Frontend Integration (Next Steps)

### ⏳ Pending Tasks

Based on [implementation plan](../../1-implementation-plans/004-llm-model-selection.md):

#### 1. Create Model Selector Component

**File**: `frontend/components/ModelSelector.tsx`

- Dropdown menu using Shadcn UI
- Display model name, size, availability
- Show checkmark for selected model
- Match ChatGPT UI styling

#### 2. Create useModelSelection Hook

**File**: `frontend/hooks/useModelSelection.ts`

- Fetch models from `/api/models`
- Manage selected model state
- Persist selection to localStorage
- Provide loading/error states

#### 3. Update Header Component

**File**: `frontend/components/Header.tsx`

- Integrate ModelSelector in header
- Position at right side (ChatGPT-style)

#### 4. Update API Service

**File**: `frontend/services/api.ts`

- Add `fetchAvailableModels()` function
- Update `sendChatMessage()` to accept model parameter
- Update `sendCanvasMessage()` to accept model parameter

#### 5. Update Type Definitions

**File**: `frontend/types/chat.ts`

```typescript
export interface LLMModel {
  id: string;
  name: string;
  size: string;
  available: boolean;
}

export interface ModelsResponse {
  models: LLMModel[];
  default: string;
}
```

#### 6. Update Chat/Canvas Hooks

**Files**: 
- `frontend/hooks/useAGUI.ts`
- `frontend/hooks/useCanvasChat.ts`

Pass selected model to API calls

---

## Configuration

**File**: `backend/config.py`

```python
class Settings(BaseSettings):
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen:7b"  # Default model
```

**Environment Variables** (`.env`):
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           Frontend (Next.js)                     │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────┐  │
│  │ ModelSelector│→ │useModelSelection│→ │useAGUI/useCanvasChat│  │
│  │  Component   │  │     Hook        │  │       Hooks         │  │
│  └──────┬───────┘  └────────┬────────┘  └─────────┬──────────┘  │
│         │                    │                      │             │
│         │ GET /api/models    │                      │             │
│         └────────────────────┼──────────────────────┘             │
│                              │ POST /api/chat                     │
│                              │ (with model param)                 │
└──────────────────────────────┼────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                         │
│  ┌────────────────┐     ┌──────────────────┐                    │
│  │ GET /api/models│────→│ OllamaClient     │                    │
│  └────────────────┘     └──────────────────┘                    │
│                                  │                                │
│  ┌────────────────┐              │ list_available_models()       │
│  │POST /api/chat  │              ▼                                │
│  │ {model: "..."] │     ┌──────────────────┐                    │
│  └───────┬────────┘     │ Ollama HTTP API  │                    │
│          │              │ /api/tags        │                    │
│          ▼              └──────────────────┘                    │
│  ┌──────────────┐                                                │
│  │  ChatAgent   │                                                │
│  │(model param) │       ┌──────────────────┐                    │
│  └──────┬───────┘       │LLMProviderFactory│                    │
│         │               └────────┬─────────┘                    │
│         │                        │                                │
│         ▼                        ▼                                │
│  ┌──────────────┐       ┌──────────────────┐                    │
│  │CanvasAgent   │       │ OllamaProvider   │                    │
│  │(model param) │       │  (model param)   │                    │
│  └──────────────┘       └──────────────────┘                    │
│                                  │                                │
│                                  ▼                                │
│                         ┌──────────────────┐                    │
│                         │  ChatOllama      │                    │
│                         │  (LangChain)     │                    │
│                         └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Ollama Server   │
                         │  qwen:4b, qwen:7b│
                         └──────────────────┘
```

---

## Data Flow

### 1. List Available Models

```
Frontend                Backend                  Ollama
   │                       │                        │
   │ GET /api/models       │                        │
   ├──────────────────────►│                        │
   │                       │ GET /api/tags          │
   │                       ├───────────────────────►│
   │                       │                        │
   │                       │ {models: [...]}        │
   │                       │◄───────────────────────┤
   │                       │                        │
   │ {models:[...]}        │                        │
   │◄──────────────────────┤                        │
   │                       │                        │
```

### 2. Send Message with Model

```
Frontend                Backend                  Ollama
   │                       │                        │
   │ POST /api/chat        │                        │
   │ {model: "qwen:4b"}    │                        │
   ├──────────────────────►│                        │
   │                       │                        │
   │                       │ ChatAgent(model="qwen:4b")
   │                       │         │              │
   │                       │         ▼              │
   │                       │ OllamaProvider         │
   │                       │         │              │
   │                       │         ▼              │
   │                       │ ChatOllama(model="qwen:4b")
   │                       │         │              │
   │                       │         │ astream()    │
   │                       │         ├─────────────►│
   │                       │         │              │
   │ SSE stream            │         │ chunks       │
   │◄──────────────────────┼─────────┼──────────────┤
   │                       │         │              │
```

---

## Error Handling

### Ollama Not Running

**Scenario**: Ollama service not started

**Backend Response**:
```json
{
  "models": [],
  "default": "qwen:7b",
  "error": "Unable to connect to Ollama. Please ensure Ollama is running."
}
```

**Frontend Behavior**: 
- Show error message
- Use default model
- Disable model selector

### Invalid Model

**Scenario**: Request model that doesn't exist

**Backend Behavior**:
- Ollama returns error during generation
- Captured in AG-UI RUN_ERROR event

**Frontend Behavior**:
- Display error message
- Fall back to default model

### Model Not Downloaded

**Scenario**: Model ID exists but not pulled locally

**Backend Response**: Model not in `/api/models` list

**Frontend Behavior**:
- Don't show model in selector
- Prompt user to pull model in Ollama

---

## Future Enhancements

1. **Multi-Provider Support**
   - OpenAI, Anthropic, Google providers
   - Provider selection UI

2. **Model Performance Metrics**
   - Response time tracking
   - Quality ratings
   - Cost estimates

3. **Smart Model Selection**
   - Auto-select based on query complexity
   - Context-aware recommendations

4. **Model Management**
   - Pull models from UI
   - Delete unused models
   - Model update notifications

5. **Per-Thread Model Memory**
   - Remember model per conversation
   - Switch models mid-conversation

---

## Documentation

- [LLM Providers](../backend/llm/providers.md) - Detailed provider documentation
- [API Models](../backend/api/models.md) - Request/response schemas
- [Implementation Plan](../../1-implementation-plans/004-llm-model-selection.md) - Original plan
