# Backend Documentation

**Last Updated**: December 23, 2025

## Overview

The backend is a **Python-based multi-agent system** using **LangGraph** for orchestration and **FastAPI** for HTTP/SSE APIs. It implements the **AG-UI protocol** for real-time streaming communication with the frontend.

## Quick Links

- [Architecture Overview](../architecture/backend-architecture.md) - Detailed backend architecture
- [Agent Discovery System](agent-discovery.md) - Agent registry and discovery
- [Agents](agents/base-agent.md) - Agent development patterns
- [API Routes](api/routes.md) - FastAPI endpoint documentation
- [LLM Providers](llm/providers.md) - Language model integration
- [LangGraph Workflows](graphs/chat-graph.md) - Agent orchestration

## Project Structure

```
/backend
├── agents/              # Agent implementations
│   ├── base_agent.py   # BaseAgent abstract class
│   └── chat_agent.py   # ChatAgent with SSE streaming
├── api/                # FastAPI endpoints
│   ├── models.py       # Pydantic request/response models
│   └── routes.py       # Route handlers with SSE
├── graphs/             # LangGraph workflow definitions
│   └── chat_graph.py   # Chat agent state graph
├── llm/                # LLM provider integrations
│   ├── ollama_provider.py    # Ollama implementation
│   └── provider_factory.py   # Provider factory
├── protocols/          # AG-UI protocol implementation
│   ├── event_types.py        # AG-UI event definitions
│   └── event_encoder.py      # SSE event encoder
├── observability/      # Logging and monitoring
├── tests/              # Test suite
├── main.py             # FastAPI application entry
├── config.py           # Configuration management
└── requirements.txt    # Python dependencies
```

## Core Components

### 1. Agents (`/agents`)

**Purpose**: Implement AI agents using LangGraph

**Key Files**:
- [`base_agent.py`](agents/base-agent.md) - Abstract base class for all agents
  - AgentState TypedDict for type-safe state
  - AG-UI event emission methods
  - LangGraph integration patterns
  
- [`chat_agent.py`](agents/chat-agent.md) - Conversational agent
  - Streaming chat responses
  - Message history management
  - LLM integration

**Pattern**:
```python
from agents.base_agent import BaseAgent, AgentState

class MyAgent(BaseAgent):
    async def process(self, state: AgentState) -> AgentState:
        # Emit AG-UI events
        await self.emit_thinking("Analyzing input...")
        
        # Process with LLM
        response = await self.llm.generate(state["messages"])
        
        # Update state
        state["messages"].append(response)
        return state
```

### 2. API Layer (`/api`)

**Purpose**: HTTP endpoints and request/response handling

**Key Files**:
- [`routes.py`](api/routes.md) - FastAPI route definitions
  - POST /api/chat - Chat endpoint with SSE streaming
  - GET /health - Health check
  
- [`models.py`](api/models.md) - Pydantic models
  - Request validation
  - Response serialization
  - Type safety

**Pattern**:
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

@router.post("/chat")
async def chat_endpoint(input_data: ChatInput):
    async def event_generator():
        async for event in agent.run(state):
            yield encoder.encode(event)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

### 3. LangGraph Workflows (`/graphs`)

**Purpose**: Multi-agent orchestration and routing

**Key Files**:
- [`chat_graph.py`](graphs/chat-graph.md) - Chat workflow definition
  - State graph configuration
  - Conditional routing logic
  - Agent node definitions

**Pattern**:
```python
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)
workflow.add_node("agent", chat_agent.process)
workflow.add_edge("agent", END)
workflow.set_entry_point("agent")

graph = workflow.compile()
```

### 4. LLM Integration (`/llm`)

**Purpose**: Language model provider abstraction

**Key Files**:
- [`provider_factory.py`](llm/providers.md) - Factory for LLM providers
- [`ollama_provider.py`](llm/ollama.md) - Ollama implementation

**Pattern**:
```python
from llm.provider_factory import LLMProviderFactory

# Get provider from factory
llm = LLMProviderFactory.get_provider(
    provider="ollama",
    model="qwen:7b"
)

# Use provider
response = await llm.generate(messages)
```

### 5. AG-UI Protocol (`/protocols`)

**Purpose**: Real-time event streaming to frontend

**Key Files**:
- `event_types.py` - AG-UI event type definitions
- `event_encoder.py` - SSE format encoder

**Pattern**:
```python
from ag_ui.core import TextMessageContentEvent, EventType
from ag_ui.encoder import EventEncoder

encoder = EventEncoder(accept="text/event-stream")

event = TextMessageContentEvent(
    type=EventType.TEXT_MESSAGE_CONTENT,
    message_id="msg-123",
    delta="Hello, world!"
)

sse_formatted = encoder.encode(event)
# Returns: "data: {...}\n\n"
```

## Development Workflow

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Install Ollama (if using local LLM)
# Follow: https://ollama.ai/download
ollama pull qwen:7b
```

### Running

```bash
# Start backend server
cd backend
uvicorn main:app --reload --port 8000

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run specific test
pytest tests/test_chat_agent.py
```

## Configuration

### Environment Variables (`config.py`)

```python
# LLM Configuration
LLM_PROVIDER=ollama              # Provider: ollama, openai, anthropic
LLM_MODEL=qwen:7b               # Model name
OLLAMA_BASE_URL=http://localhost:11434

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]

# Observability (Optional)
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

### Settings Management

```python
from config import settings

# Access settings
print(settings.LLM_PROVIDER)
print(settings.OLLAMA_BASE_URL)
```

## Common Tasks

### Adding a New Agent

1. Create agent class in `/agents`:
```python
# agents/my_agent.py
from agents.base_agent import BaseAgent, AgentState

class MyAgent(BaseAgent):
    async def process(self, state: AgentState) -> AgentState:
        # Implementation
        return state
```

2. Add to graph workflow:
```python
# graphs/my_graph.py
from agents.my_agent import MyAgent

agent = MyAgent(llm)
workflow.add_node("my_agent", agent.process)
```

3. Update routing logic if needed

### Adding a New LLM Provider

1. Create provider implementation:
```python
# llm/my_provider.py
class MyProvider:
    async def generate(self, messages):
        # Implementation
        pass
```

2. Register in factory:
```python
# llm/provider_factory.py
if provider == "myprovider":
    return MyProvider(model=model)
```

### Adding a New API Endpoint

1. Define Pydantic models:
```python
# api/models.py
class MyRequest(BaseModel):
    field: str

class MyResponse(BaseModel):
    result: str
```

2. Create route handler:
```python
# api/routes.py
@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest) -> MyResponse:
    # Implementation
    return MyResponse(result="...")
```

## Best Practices

### Agent Development
- ✅ Inherit from `BaseAgent`
- ✅ Use typed `AgentState` for state management
- ✅ Emit AG-UI events for UI visibility
- ✅ Handle errors gracefully with try/except
- ✅ Keep agents focused and composable

### LangGraph Workflows
- ✅ Define clear state schemas
- ✅ Use conditional edges for routing
- ✅ Keep node functions pure when possible
- ✅ Document workflow logic

### API Design
- ✅ Use Pydantic for validation
- ✅ Return proper HTTP status codes
- ✅ Stream responses with SSE when appropriate
- ✅ Handle CORS properly
- ✅ Add comprehensive error handling

### LLM Integration
- ✅ Use provider factory for flexibility
- ✅ Configure via environment variables
- ✅ Handle rate limiting and retries
- ✅ Log LLM calls for debugging

## Troubleshooting

### Common Issues

**Issue**: Ollama connection refused
```bash
# Solution: Start Ollama service
ollama serve
```

**Issue**: CORS errors from frontend
```python
# Solution: Add frontend origin to CORS_ORIGINS in config.py
CORS_ORIGINS=["http://localhost:3000"]
```

**Issue**: SSE events not received
```python
# Solution: Ensure proper SSE headers
return StreamingResponse(
    generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
)
```

**Issue**: Import errors
```bash
# Solution: Ensure virtual environment is activated
source .venv/bin/activate
pip install -r requirements.txt
```

## Related Documentation

- [System Architecture](../architecture/overview.md) - High-level system design
- [AG-UI Protocol](../agui-protocol/README.md) - Event streaming protocol
- [Frontend Integration](../frontend/README.md) - Frontend documentation

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [AG-UI Protocol Spec](https://github.com/example/ag-ui)
- [Ollama Documentation](https://ollama.ai/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

*For detailed implementation guides, see subdirectories: agents/, api/, graphs/, llm/*
