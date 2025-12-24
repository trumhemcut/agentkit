# API Routes Documentation

## Overview

The backend provides RESTful API endpoints with Server-Sent Events (SSE) streaming for real-time agent communication. All endpoints follow the AG-UI protocol for consistent frontend integration.

## Endpoints

### Agent Discovery

#### GET /api/agents

List all available agents with their metadata.

**Response**:
```json
{
  "agents": [
    {
      "id": "chat",
      "name": "Chat Agent",
      "description": "General purpose conversational agent",
      "icon": "message-circle",
      "sub_agents": [],
      "features": ["conversation", "streaming"]
    },
    {
      "id": "canvas",
      "name": "Canvas Agent",
      "description": "Multi-agent system with artifact generation and editing",
      "icon": "layout",
      "sub_agents": ["generator", "editor"],
      "features": ["artifacts", "code-generation", "multi-step"]
    }
  ],
  "default": "chat"
}
```

**Status Codes**:
- `200 OK` - Success
- `500 Internal Server Error` - Registry error

**Usage**:
```python
response = requests.get("http://localhost:8000/api/agents")
data = response.json()
agents = data["agents"]
default_agent = data["default"]
```

---

### Model Management

#### GET /api/models

List available LLM models from the configured provider (Ollama).

**Response**:
```json
{
  "models": [
    {
      "name": "qwen:7b",
      "description": "Qwen 7B model"
    }
  ]
}
```

**Status Codes**:
- `200 OK` - Success
- `500 Internal Server Error` - Model provider error

---

### Chat

#### POST /api/chat

Chat endpoint with SSE streaming using selected agent.

**Request Body**:
```json
{
  "thread_id": "string",
  "run_id": "string",
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "model": "qwen:7b",  // Optional, defaults to configured model
  "agent": "chat"      // Optional, defaults to "chat"
}
```

**Response**: Server-Sent Events (SSE) stream

**AG-UI Event Flow**:
1. `RUN_STARTED` - Indicates run has started
2. `TEXT_MESSAGE_CHUNK` - Streamed text chunks
3. `RUN_FINISHED` - Indicates successful completion
4. `RUN_ERROR` - Indicates error occurred

**Example Events**:
```
event: run_started
data: {"type": "run_started", "thread_id": "...", "run_id": "..."}

event: text_message_chunk
data: {"type": "text_message_chunk", "chunk": "Hello"}

event: run_finished
data: {"type": "run_finished", "thread_id": "...", "run_id": "..."}
```

**Status Codes**:
- `200 OK` - Streaming started
- `400 Bad Request` - Invalid agent ID
- `500 Internal Server Error` - Graph execution error

**Agent Validation**:
- Validates agent ID before streaming
- Returns 400 if agent not available
- Dynamically routes to appropriate graph

**Usage**:
```python
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "thread_id": "test",
        "run_id": "test",
        "messages": [{"role": "user", "content": "Hello"}],
        "agent": "chat"
    },
    headers={"Accept": "text/event-stream"},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode())
```

---

### Canvas

#### POST /api/canvas/stream

Canvas agent endpoint with artifact streaming.

**Request Body**:
```json
{
  "thread_id": "string",
  "run_id": "string",
  "messages": [
    {
      "role": "user",
      "content": "Create a hello world script"
    }
  ],
  "artifact": {
    "currentIndex": 0,
    "contents": [...]
  },
  "selectedText": {
    "start": 0,
    "end": 10,
    "text": "selected"
  },
  "action": "create|update|rewrite|chat",
  "model": "qwen:7b",  // Optional
  "agent": "canvas"    // Optional, defaults to "canvas"
}
```

**Response**: Server-Sent Events (SSE) stream

**AG-UI Event Flow**:
1. `RUN_STARTED`
2. `ARTIFACT_CODE_CHUNK` / `ARTIFACT_TEXT_CHUNK` - Artifact content
3. `RUN_FINISHED` / `RUN_ERROR`

**Example Events**:
```
event: artifact_code_chunk
data: {"type": "artifact_code_chunk", "code": "print('hello')", "language": "python"}

event: run_finished
data: {"type": "run_finished", "thread_id": "...", "run_id": "..."}
```

**Status Codes**:
- `200 OK` - Streaming started
- `400 Bad Request` - Invalid agent ID or parameters
- `500 Internal Server Error` - Graph execution error

---

## Request Models

### RunAgentInput

Used for `/api/chat` endpoint.

```python
class RunAgentInput(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    model: Optional[str] = None
    agent: Optional[str] = "chat"
```

### CanvasMessageRequest

Used for `/api/canvas/stream` endpoint.

```python
class CanvasMessageRequest(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    artifact: Optional[ArtifactV3] = None
    selectedText: Optional[SelectedText] = None
    action: Optional[Literal["create", "update", "rewrite", "chat"]] = None
    model: Optional[str] = None
    agent: Optional[str] = "canvas"
```

## AG-UI Protocol

All endpoints follow the AG-UI protocol specification for consistent frontend integration.

### Event Types

See [AG-UI Protocol Documentation](../../agui-protocol/README.md) for complete event type documentation.

**Common Events**:
- `RUN_STARTED` - Run initialization
- `TEXT_MESSAGE_CHUNK` - Streaming text
- `ARTIFACT_CODE_CHUNK` - Streaming code artifact
- `ARTIFACT_TEXT_CHUNK` - Streaming text artifact
- `RUN_FINISHED` - Successful completion
- `RUN_ERROR` - Error occurred

### Content Type Negotiation

Endpoints support multiple content types via Accept header:

- `text/event-stream` - SSE format (default)
- `application/json-seq` - JSON sequence format

**Example**:
```python
headers = {"Accept": "text/event-stream"}
response = requests.post(url, json=data, headers=headers, stream=True)
```

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message"
}
```

### Common Errors

**400 Bad Request**:
- Invalid agent ID
- Missing required fields
- Invalid action type

**500 Internal Server Error**:
- Agent registry error
- Graph execution error
- Model provider error

### Error Events

Errors during streaming are sent as `RUN_ERROR` events:

```
event: run_error
data: {"type": "run_error", "thread_id": "...", "run_id": "...", "message": "Error details"}
```

## Testing

### Manual Testing with curl

**List agents**:
```bash
curl http://localhost:8000/api/agents
```

**Chat request**:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "thread_id": "test",
    "run_id": "test",
    "messages": [{"role": "user", "content": "Hello"}],
    "agent": "chat"
  }'
```

### Automated Testing

See test files:
- `tests/test_agents_api.py` - Agent discovery tests
- `tests/test_agent_selection.py` - Agent selection tests
- `tests/test_chat_graph.py` - Chat endpoint tests
- `tests/test_canvas.py` - Canvas endpoint tests

## CORS Configuration

CORS is configured to allow frontend access:

```python
# config.py
CORS_ORIGINS: List[str] = ["http://localhost:3000"]
```

Update `CORS_ORIGINS` to add allowed origins.

## Related Documentation

- [Agent Discovery](../agent-discovery.md) - Agent registry system
- [Request Models](models.md) - Pydantic model schemas
- [AG-UI Protocol](../../agui-protocol/README.md) - Event protocol details
- [Configuration](../README.md#configuration) - Backend configuration
