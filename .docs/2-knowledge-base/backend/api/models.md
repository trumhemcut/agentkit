# API Models Documentation

**Last Updated**: December 23, 2025

## Overview

Pydantic models for request/response validation in the FastAPI backend. Ensures type safety and automatic validation for all API endpoints.

## Core Models

### Message

**File**: `backend/api/models.py`

Basic message structure used across all chat/canvas endpoints.

```python
class Message(BaseModel):
    role: str      # "user" | "assistant" | "system"
    content: str   # Message content
```

**Usage**:
```json
{
  "role": "user",
  "content": "Hello, how are you?"
}
```

---

## Chat Models

### RunAgentInput

**Purpose**: Request model for chat endpoint

**Fields**:
- `thread_id` (str): Unique conversation thread ID (auto-generated if not provided)
- `run_id` (str): Unique run ID for this request (auto-generated if not provided)
- `messages` (List[Message]): Array of conversation messages
- `model` (Optional[str]): Model to use for this request (e.g., "qwen:7b")

**Definition**:
```python
class RunAgentInput(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    model: Optional[str] = None  # Optional model selection
```

**Example Request**:
```json
{
  "thread_id": "thread-abc-123",
  "run_id": "run-xyz-789",
  "messages": [
    {
      "role": "user",
      "content": "What is Python?"
    }
  ],
  "model": "qwen:7b"
}
```

**Example with Auto-Generated IDs**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ]
}
```

---

## Canvas Models

### ArtifactContentCode

**Purpose**: Code artifact content

```python
class ArtifactContentCode(BaseModel):
    index: int              # Version/index number
    type: Literal["code"]   # Must be "code"
    title: str              # Artifact title
    code: str               # Code content
    language: str           # Programming language (e.g., "python", "javascript")
```

**Example**:
```json
{
  "index": 1,
  "type": "code",
  "title": "Hello World",
  "code": "print('Hello, World!')",
  "language": "python"
}
```

### ArtifactContentText

**Purpose**: Text/Markdown artifact content

```python
class ArtifactContentText(BaseModel):
    index: int              # Version/index number
    type: Literal["text"]   # Must be "text"
    title: str              # Artifact title
    fullMarkdown: str       # Markdown content
```

**Example**:
```json
{
  "index": 1,
  "type": "text",
  "title": "Project Plan",
  "fullMarkdown": "# Project Plan\n\n## Goals\n- Goal 1\n- Goal 2"
}
```

### ArtifactV3

**Purpose**: Canvas artifact with versioning

```python
class ArtifactV3(BaseModel):
    currentIndex: int                                              # Current active version
    contents: List[Union[ArtifactContentCode, ArtifactContentText]] # All versions
```

**Example**:
```json
{
  "currentIndex": 2,
  "contents": [
    {
      "index": 1,
      "type": "code",
      "title": "Calculator",
      "code": "def add(a, b): return a + b",
      "language": "python"
    },
    {
      "index": 2,
      "type": "code",
      "title": "Calculator v2",
      "code": "def add(a, b): return a + b\ndef subtract(a, b): return a - b",
      "language": "python"
    }
  ]
}
```

### SelectedText

**Purpose**: User-selected text in artifact

```python
class SelectedText(BaseModel):
    start: int    # Start position in text
    end: int      # End position in text
    text: str     # Selected text content
```

**Example**:
```json
{
  "start": 10,
  "end": 25,
  "text": "selected text"
}
```

### CanvasMessageRequest

**Purpose**: Request model for canvas chat endpoint

**Fields**:
- `thread_id` (str): Unique conversation thread ID
- `run_id` (str): Unique run ID for this request
- `messages` (List[Message]): Array of conversation messages
- `artifact` (Optional[ArtifactV3]): Current artifact state
- `selectedText` (Optional[SelectedText]): User-selected text in artifact
- `action` (Optional[str]): Action to perform ("create", "update", "rewrite", "chat")
- `model` (Optional[str]): Model to use for this request

**Definition**:
```python
class CanvasMessageRequest(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    artifact: Optional[ArtifactV3] = None
    selectedText: Optional[SelectedText] = None
    action: Optional[Literal["create", "update", "rewrite", "chat"]] = None
    model: Optional[str] = None  # Optional model selection
```

**Example - Create Artifact**:
```json
{
  "thread_id": "canvas-thread-123",
  "run_id": "run-456",
  "messages": [
    {
      "role": "user",
      "content": "Create a Python function to calculate fibonacci"
    }
  ],
  "action": "create",
  "model": "qwen:7b"
}
```

**Example - Update Artifact**:
```json
{
  "thread_id": "canvas-thread-123",
  "run_id": "run-789",
  "messages": [
    {
      "role": "user",
      "content": "Add error handling"
    }
  ],
  "artifact": {
    "currentIndex": 1,
    "contents": [
      {
        "index": 1,
        "type": "code",
        "title": "Fibonacci",
        "code": "def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)",
        "language": "python"
      }
    ]
  },
  "action": "update",
  "model": "qwen:4b"
}
```

**Example - Rewrite Selected Text**:
```json
{
  "thread_id": "canvas-thread-123",
  "run_id": "run-101",
  "messages": [
    {
      "role": "user",
      "content": "Make this more concise"
    }
  ],
  "artifact": {
    "currentIndex": 1,
    "contents": [...]
  },
  "selectedText": {
    "start": 0,
    "end": 50,
    "text": "def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2)"
  },
  "action": "rewrite",
  "model": "qwen:7b"
}
```

### ArtifactUpdate

**Purpose**: Manual artifact update request (future implementation)

```python
class ArtifactUpdate(BaseModel):
    content: str    # Updated content
    index: int      # Version index
```

---

## Model Selection

### Model Parameter

All request models (RunAgentInput, CanvasMessageRequest) support optional `model` field:

**Purpose**: Allow frontend to specify which LLM model to use

**Format**: String identifier matching Ollama model name (e.g., "qwen:4b", "qwen:7b")

**Behavior**:
- If provided: Use specified model
- If omitted/null: Use default model from config (settings.OLLAMA_MODEL)

**Validation**: 
- No strict validation at model level
- Ollama will error if model doesn't exist
- Frontend should validate against `/api/models` response

**Examples**:

```json
// Use Qwen 4B (faster)
{
  "messages": [...],
  "model": "qwen:4b"
}

// Use Qwen 7B (better quality)
{
  "messages": [...],
  "model": "qwen:7b"
}

// Use default from config
{
  "messages": [...]
}
```

---

## Response Models

### Models List Response

**Endpoint**: GET /api/models

**Structure**:
```typescript
{
  models: Array<{
    id: string;          // Model identifier (e.g., "qwen:7b")
    name: string;        // Display name (e.g., "Qwen 7B")
    size: string;        // Size label (e.g., "7B parameters")
    available: boolean;  // Is model ready to use
    size_bytes: number;  // Model size in bytes
  }>;
  default: string;       // Default model ID
  error?: string;        // Error message if any
}
```

**Success Example**:
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

**Error Example** (Ollama not running):
```json
{
  "models": [],
  "default": "qwen:7b",
  "error": "Unable to connect to Ollama. Please ensure Ollama is running."
}
```

---

## Validation

### Automatic Validation

Pydantic automatically validates:
- Required fields are present
- Field types match definitions
- Literal types match allowed values
- UUIDs are properly formatted

### Example Validation Errors

**Missing Required Field**:
```json
// Request: {"thread_id": "123"}
// Error: Field 'messages' required
```

**Invalid Type**:
```json
// Request: {"messages": "not a list"}
// Error: Field 'messages' must be list
```

**Invalid Literal**:
```json
// Request: {"action": "invalid_action"}
// Error: Field 'action' must be one of: create, update, rewrite, chat
```

---

## Usage in Routes

### Chat Endpoint

```python
@router.post("/chat")
async def chat_endpoint(input_data: RunAgentInput, request: Request):
    # Pydantic automatically validates input_data
    # Access fields with type safety
    thread_id = input_data.thread_id
    messages = input_data.messages
    model = input_data.model  # May be None
    
    # Create agent with optional model
    agent = ChatAgent(model=model)
    ...
```

### Canvas Endpoint

```python
@router.post("/canvas/stream")
async def canvas_stream_endpoint(input_data: CanvasMessageRequest, request: Request):
    # Access fields
    artifact = input_data.artifact
    selected_text = input_data.selectedText
    action = input_data.action
    model = input_data.model
    
    # Create agent with optional model
    if action == "artifact_action":
        agent = CanvasAgent(model=model)
    else:
        agent = ChatAgent(model=model)
    ...
```

---

## Best Practices

1. **Always Use Type Hints**
   - Leverage Pydantic's automatic validation
   - Get IDE autocomplete and type checking

2. **Optional Fields**
   - Use `Optional[T] = None` for optional fields
   - Provide sensible defaults when possible

3. **Field Factories**
   - Use `default_factory` for dynamic defaults (UUIDs, timestamps)
   - Don't use mutable defaults directly

4. **Validation**
   - Trust Pydantic validation for basic checks
   - Add custom validators for complex business logic

5. **Model Selection**
   - Always support `model` field in request models
   - Fall back to config default if not provided
   - Validate model exists via `/api/models` on frontend

---

## Related Documentation

- [API Routes](routes.md) - Endpoint implementations
- [LLM Providers](../llm/providers.md) - Model selection and providers
- [AG-UI Protocol](../../agui-protocol/protocol-spec.md) - Event streaming
