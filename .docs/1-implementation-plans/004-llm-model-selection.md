# Implementation Plan: LLM Model Selection

**Requirement**: Support API to display available models and allow frontend to select models during chat. Currently support the models from Ollama. Model selector should be positioned similar to ChatGPT UI (at top of page).

**Related Files**:
- Backend: `backend/llm/`, `backend/api/routes.py`, `backend/config.py`
- Frontend: `frontend/components/Header.tsx`, `frontend/services/api.ts`, `frontend/types/`

---

## 1. Backend Tasks (LangGraph + AG-UI)

**Delegate to Backend Agent** - See [backend.agent.md](.github/agents/backend.agent.md)

### Task 1.1: Create Models API Endpoint
**File**: `backend/api/routes.py`

Add new endpoint to list available Ollama models:
```python
@router.get("/models")
async def list_models():
    """List available Ollama models"""
    # Query Ollama API for available models
    # Filter for qwen models (qwen-4b, qwen-7b)
    # Return model list with metadata
```

**Requirements**:
- Call Ollama API at `http://localhost:11434/api/tags` to get available models
- Return structured response with model name, size, and availability status
- Handle errors gracefully (Ollama not running, no models available)

**Response Schema**:
```python
{
  "models": [
    {
      "id": "qwen:4b",
      "name": "Qwen 4B",
      "size": "4B parameters",
      "available": true
    },
    {
      "id": "qwen:7b", 
      "name": "Qwen 7B",
      "size": "7B parameters",
      "available": true
    },
    ...
  ],
  "default": "qwen:7b"
}
```

### Task 1.2: Update Chat/Canvas Endpoints to Accept Model Parameter
**Files**: `backend/api/routes.py`, `backend/api/models.py`

Update request models to include optional model parameter:
```python
class RunAgentInput(BaseModel):
    thread_id: str
    run_id: str
    messages: List[MessageInput]
    model: Optional[str] = None  # Add model selection

class CanvasMessageRequest(BaseModel):
    thread_id: str
    run_id: str
    messages: List[MessageInput]
    artifact: Optional[ArtifactV3] = None
    selectedText: Optional[SelectedText] = None
    action: Optional[str] = None
    model: Optional[str] = None  # Add model selection
```

**Requirements**:
- Add `model` field to request schemas with default value from config
- Validate model is in allowed list (qwen:4b, qwen:7b)
- Pass model parameter to agents

### Task 1.3: Update LLM Provider to Support Dynamic Model Selection
**File**: `backend/llm/ollama_provider.py`

Modify OllamaProvider to accept model parameter:
```python
class OllamaProvider:
    def __init__(self, model: str = None):
        self.model = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=model or settings.OLLAMA_MODEL,
            streaming=True
        )
```

**Requirements**:
- Accept optional model parameter in constructor
- Fall back to config default if not provided
- Update factory method to pass model parameter

### Task 1.4: Update Base Agent to Accept Model Parameter
**File**: `backend/agents/base_agent.py`

Update agent initialization to accept and use model parameter:
```python
class BaseAgent:
    def __init__(self, model: str = None):
        self.llm_provider = LLMProviderFactory.get_provider("ollama")
        # Initialize with specified model or default
```

**Requirements**:
- Pass model to LLM provider during initialization
- Ensure ChatAgent and CanvasAgent inherit this behavior
- Update agent instantiation in routes to pass model from request

### Task 1.5: Update Ollama Client Service
**File**: Create `backend/llm/ollama_client.py`

Create utility class to interact with Ollama API:
```python
class OllamaClient:
    @staticmethod
    async def list_available_models():
        """Query Ollama for available models"""
        # Call /api/tags endpoint
        # Parse and filter models
        # Return structured list
```

**Requirements**:
- Use httpx or requests to call Ollama API
- Handle connection errors
- Cache model list for performance (optional)

---

## 2. Protocol (AG-UI Communication)

### Message Format Updates

**Request Enhancement** (Frontend → Backend):
```typescript
// Existing chat request with new model field
{
  thread_id: string;
  run_id: string;
  messages: Message[];
  model?: string;  // NEW: Selected model ID (e.g., "qwen:7b")
}
```

**New Models API** (Backend → Frontend):
```typescript
// GET /api/models response
{
  models: Array<{
    id: string;          // e.g., "qwen:7b"
    name: string;        // e.g., "Qwen 7B"
    size: string;        // e.g., "7B parameters"
    available: boolean;  // Is model downloaded/ready
  }>;
  default: string;       // Default model ID
}
```

### State Management
- Frontend stores selected model in localStorage/session
- Model selection persists across page refreshes
- Default model loaded on first visit

### Error Handling
- Backend validates model exists before processing
- Return clear error if model not available
- Frontend shows appropriate error message

---

## 3. Frontend Tasks (AG-UI)

**Delegate to Frontend Agent** - See [frontend.agent.md](.github/agents/frontend.agent.md)

### Task 3.1: Create Model Selector Component
**File**: Create `frontend/components/ModelSelector.tsx`

Create dropdown component using Shadcn UI:
```tsx
// Dropdown menu component with model list
// Display model name, size, availability
// Emit event when model selected
// Show current selected model
```

**Requirements**:
- Use Shadcn UI `DropdownMenu` component
- Display model icon, name, and size
- Show checkmark for currently selected model
- Disable unavailable models
- Match ChatGPT UI styling and positioning
- Responsive design for mobile

**Component Structure**:
```tsx
<DropdownMenu>
  <DropdownMenuTrigger>
    <Button variant="ghost">
      <Bot /> {currentModel.name}
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    {models.map(model => (
      <DropdownMenuItem 
        key={model.id}
        onClick={() => onSelectModel(model.id)}
        disabled={!model.available}
      >
        {/* Model info */}
      </DropdownMenuItem>
    ))}
  </DropdownMenuContent>
</DropdownMenu>
```

### Task 3.2: Update Header Component
**File**: `frontend/components/Header.tsx`

Integrate ModelSelector into header:
```tsx
export function Header() {
  return (
    <header className="bg-background shadow-sm">
      <div className="flex h-16 items-center px-6 justify-between">
        <div className="flex items-center gap-3">
          {/* Existing logo and title */}
        </div>
        <ModelSelector />  {/* NEW: Model selector */}
      </div>
    </header>
  );
}
```

**Requirements**:
- Position model selector at right side of header
- Maintain existing header layout and branding
- Ensure responsive behavior

### Task 3.3: Create useModelSelection Hook
**File**: Create `frontend/hooks/useModelSelection.ts`

Custom hook to manage model selection state:
```typescript
export function useModelSelection() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Fetch available models from API
  // Load saved model from localStorage
  // Persist model selection
  // Return models, selectedModel, selectModel function
}
```

**Requirements**:
- Fetch models on mount from `/api/models`
- Load previously selected model from localStorage
- Save model selection to localStorage on change
- Provide loading and error states
- Return helper functions for model operations

### Task 3.4: Update API Service
**File**: `frontend/services/api.ts`

Add functions for model operations:
```typescript
// Fetch available models
export async function fetchAvailableModels() {
  const response = await fetch(`${API_BASE_URL}/api/models`);
  return response.json();
}

// Update chat requests to include model
export async function sendChatMessage(
  messages: Message[],
  threadId: string,
  runId: string,
  model: string,  // NEW: Add model parameter
  onEvent: (event: any) => void
): Promise<void> {
  // Include model in request body
}
```

**Requirements**:
- Add `fetchAvailableModels()` function
- Update `sendChatMessage()` to accept model parameter
- Update `sendCanvasMessage()` to accept model parameter
- Include model in request body
- Handle API errors gracefully

### Task 3.5: Update Type Definitions
**File**: `frontend/types/chat.ts`

Add model-related types:
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

### Task 3.6: Update Chat Components to Use Selected Model
**Files**: `frontend/hooks/useAGUI.ts`, `frontend/hooks/useCanvasChat.ts`

Update hooks to pass selected model to API calls:
```typescript
// Get selected model from context/hook
const { selectedModel } = useModelSelection();

// Pass to API call
await sendChatMessage(messages, threadId, runId, selectedModel, onEvent);
```

**Requirements**:
- Access selected model from useModelSelection hook
- Pass model to all chat/canvas API calls
- Fall back to default if no model selected
- Update loading states appropriately

### Task 3.7: Add Model Selection to Canvas Page
**File**: `frontend/components/Canvas/CanvasLayout.tsx`

Ensure model selector also appears in canvas view header

---

## 4. Integration Points

### Backend → Frontend
1. **Models API**: `GET /api/models` returns list of available models
2. **Chat API**: `POST /api/chat` accepts optional `model` parameter
3. **Canvas API**: `POST /api/canvas/stream` accepts optional `model` parameter

### Frontend → Backend  
1. **Model Selection**: User selects model from dropdown
2. **Request Enhancement**: Model ID included in all chat/canvas requests
3. **Persistence**: Selected model saved in localStorage

### State Synchronization
- Model selection stored client-side (localStorage)
- Backend validates model on each request
- Error handling if model not available

---

## 5. Testing Requirements

### Backend Tests
- Test `/api/models` endpoint returns correct format
- Test model validation in chat/canvas endpoints
- Test error handling for invalid models
- Test Ollama connection failures
- Test agent initialization with different models

### Frontend Tests
- Test ModelSelector component renders correctly
- Test model selection persistence (localStorage)
- Test API integration with model parameter
- Test error states (no models available, API failure)
- Test responsive behavior

### Integration Tests
- End-to-end: Select model → Send message → Receive response
- Test model switching during conversation
- Test default model behavior
- Test model persistence across page refresh

---

## 6. Implementation Order

1. **Backend Phase 1**: Create models API endpoint and Ollama client
2. **Backend Phase 2**: Update request schemas and agent initialization
3. **Frontend Phase 1**: Create model selector UI component and hook
4. **Frontend Phase 2**: Integrate into header and update API calls
5. **Integration**: Connect frontend to backend, test end-to-end
6. **Polish**: Add loading states, error handling, persistence

---

## 7. Dependencies

### Backend
- Existing: `backend/llm/ollama_provider.py`, `backend/api/routes.py`
- New: `backend/llm/ollama_client.py`
- Requires: Ollama running with qwen:4b and qwen:7b models

### Frontend
- Existing: Shadcn UI components (DropdownMenu, Button)
- New: `ModelSelector.tsx`, `useModelSelection.ts`
- Requires: Backend models API endpoint

---

## 8. Success Criteria

- [ ] Backend exposes `/api/models` endpoint with available models
- [ ] Backend accepts `model` parameter in chat/canvas requests
- [ ] Frontend displays model selector in header (ChatGPT-style)
- [ ] User can select between qwen-4b and qwen-7b models
- [ ] Selected model persists across page refreshes
- [ ] Chat/canvas requests use selected model
- [ ] Appropriate error handling for unavailable models
- [ ] Responsive design works on mobile devices
- [ ] Documentation updated in knowledge base

---

## 9. Future Enhancements

- Support for additional Ollama models
- Model performance metrics display
- Model auto-detection and download
- Per-thread model selection
- Model recommendation based on query type
