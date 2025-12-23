# Backend Architecture

**Date**: December 23, 2025
**Status**: Implemented

## Overview

The backend implements a multi-agent AI system using LangGraph for orchestration and AG-UI protocol for real-time agent-frontend communication via SSE streaming.

## Technology Stack

- **LangGraph**: Multi-agent workflow orchestration framework
- **AG-UI Protocol**: Real-time agent-frontend communication
- **FastAPI**: HTTP server with streaming endpoints
- **Ollama**: LLM provider with `qwen:7b` model
- **Python 3.12**: Backend implementation language

## Project Structure

```
/backend
  /agents          # Agent implementations
    base_agent.py  # BaseAgent abstract class with AgentState
    chat_agent.py  # ChatAgent with SSE streaming
  /api             # API endpoints
    models.py      # Pydantic request/response models
    routes.py      # FastAPI route handlers with SSE
  /graphs          # LangGraph workflow definitions
    chat_graph.py  # Chat agent state graph
  /llm             # LLM provider integrations
    ollama_provider.py    # Ollama provider implementation
    provider_factory.py   # Factory pattern for providers
  /protocols       # AG-UI protocol implementation
    event_types.py        # AG-UI event type definitions
    event_encoder.py      # SSE event encoder
  /observability   # Logging and monitoring
  /tests           # Test suite
  main.py          # FastAPI application entry point
  config.py        # Configuration management with pydantic-settings
  requirements.txt # Python dependencies
```

## Core Components

### 1. Configuration Management (`config.py`)

Uses `pydantic-settings` for environment-based configuration:

```python
class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen:7b"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
```

**Key Features**:
- Environment variable support via `.env` file
- Type-safe configuration with Pydantic
- Default values for all settings

### 2. AG-UI Protocol Implementation

#### Event Types (`protocols/event_types.py`)

```python
# Re-export EventType from official AG-UI SDK
from ag_ui.core import EventType
```

#### Event Encoder (`protocols/event_encoder.py`)

Encodes events as Server-Sent Events (SSE):

```python
# Re-export EventEncoder from official AG-UI SDK
from ag_ui.encoder import EventEncoder
```

**Event Flow**:
1. `RUN_STARTED` - Agent run begins
2. `TEXT_MESSAGE_START` - Message generation starts
3. `TEXT_MESSAGE_CONTENT` - Streamed content chunks (multiple)
4. `TEXT_MESSAGE_END` - Message generation completes
5. `RUN_FINISHED` - Agent run completes

### 3. LLM Provider Integration

#### Factory Pattern (`llm/provider_factory.py`)

```python
class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_type: str = "ollama"):
        if provider_type == "ollama":
            return OllamaProvider()
        raise ValueError(f"Unknown provider: {provider_type}")
```

#### Ollama Provider (`llm/ollama_provider.py`)

```python
class OllamaProvider:
    def __init__(self):
        self.model = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            streaming=True
        )
```

**Key Features**:
- Streaming support enabled by default
- Configurable via environment variables
- Extensible to other providers (OpenAI, Anthropic, etc.)

### 4. Agent Architecture

#### Base Agent (`agents/base_agent.py`)

```python
class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    thread_id: str
    run_id: str

class BaseAgent(ABC):
    @abstractmethod
    async def run(self, state: AgentState):
        """Execute agent logic"""
        pass
```

#### Chat Agent (`agents/chat_agent.py`)

Implements streaming chat with AG-UI events:

```python
from ag_ui.core import EventType, TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent

class ChatAgent(BaseAgent):
    async def run(self, state: AgentState) -> AsyncGenerator[BaseEvent, None]:
        message_id = str(uuid.uuid4())
        
        # Emit TEXT_MESSAGE_START using official AG-UI event class
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant"
        )
        
        # Stream LLM response chunk by chunk
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=chunk.content
                )
        
        # Emit TEXT_MESSAGE_END using official AG-UI event class
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
```

**Key Features**:
- AsyncGenerator for streaming (returns BaseEvent objects)
- AG-UI compliant event emission using official event classes
- UUID-based message identification
- Chunk-by-chunk response delivery
- Type-safe with Pydantic models from ag_ui.core

### 5. LangGraph Integration

#### Chat Graph (`graphs/chat_graph.py`)

```python
def create_chat_graph():
    workflow = StateGraph(AgentState)
    chat_agent = ChatAgent()
    
    workflow.add_node("chat", chat_agent.run)
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
    
    return workflow.compile()
```

**Note**: Currently not used in routes due to direct streaming from agent for simplicity.

### 6. FastAPI Server

#### API Models (`api/models.py`)

```python
class Message(BaseModel):
    role: str
    content: str

class RunAgentInput(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
```

#### Routes (`api/routes.py`)

SSE streaming endpoint:

```python
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder

@router.post("/chat")
async def chat_endpoint(input_data: RunAgentInput, request: Request):
    encoder = EventEncoder(accept=request.headers.get("accept"))
    
    async def event_generator():
        # Use official AG-UI event classes
        yield encoder.encode(
            RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
        )
        
        # Stream from agent
        async for event in chat_agent.run(state):
            yield encoder.encode(event)
        
        yield encoder.encode(
            RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
        )
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Key Features**:
- SSE streaming with `StreamingResponse`
- AG-UI protocol compliance using official SDK
- Type-safe event classes (RunStartedEvent, TextMessageContentEvent, etc.)
- Error handling with `RUN_ERROR` events
- Thread and run ID tracking
- Proper camelCase field names (threadId, runId, messageId)

#### Main Application (`main.py`)

```python
app = FastAPI(title="AgentKit Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
```

## API Endpoints

### POST `/api/chat`
Chat with agent using AG-UI protocol

**Request**:
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

**Response**: SSE stream with AG-UI events

### GET `/health`
Health check endpoint

**Response**:
```json
{"status": "healthy"}
```

## Streaming Flow

1. Client sends POST request to `/api/chat`
2. Server sends `RUN_STARTED` event
3. Agent emits `TEXT_MESSAGE_START` event
4. Agent streams `TEXT_MESSAGE_CONTENT` events (chunks)
5. Agent emits `TEXT_MESSAGE_END` event
6. Server sends `RUN_FINISHED` event

## Setup & Running

### Prerequisites
- Python 3.10+
- Ollama installed with `qwen:7b` model

### Installation
```bash
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Running
```bash
python -m backend.main
```

Server starts at `http://0.0.0.0:8000`

### Testing
```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"messages":[{"role":"user","content":"Hello!"}]}'
```

## Design Patterns

### Factory Pattern
Used for LLM provider instantiation, making it easy to add new providers.

### Async Generator Pattern
Used for streaming responses from agents.

### TypedDict State Pattern
LangGraph state management with type safety.

### Middleware Pattern
CORS and future authentication middleware.

## Extension Points

### Adding New Agents
1. Create class inheriting from `BaseAgent`
2. Implement `run()` method with AG-UI events
3. Optionally create LangGraph workflow
4. Add route in `api/routes.py`

### Adding New LLM Providers
1. Create provider class in `llm/`
2. Implement `get_model()` method
3. Add to `LLMProviderFactory`
4. Update configuration

### Adding Tools
1. Create tool class in `tools/`
2. Integrate with agent in `run()` method
3. Emit appropriate AG-UI events for tool execution

## Best Practices

1. **Always emit AG-UI events** for frontend visibility
2. **Use AsyncGenerator** for streaming responses
3. **Type everything** with Pydantic and TypedDict
4. **Externalize configuration** via environment variables
5. **Handle errors gracefully** with RUN_ERROR events
6. **Stream chunk by chunk** for real-time UX
7. **Use factory patterns** for extensibility

## References

- [AG-UI Protocol](https://github.com/ag-ui-protocol/ag-ui)
- [LangGraph Docs](https://github.com/langchain-ai/langgraph)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
