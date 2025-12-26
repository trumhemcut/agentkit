# LangGraph Architecture and Graph Factory Pattern

## Overview

The AgentKit backend uses **LangGraph** for all agent orchestration. All agent execution flows through LangGraph state graphs - agents are never instantiated directly in routes or endpoints.

## Key Principle

**Single Execution Path:** Every agent request is routed through a compiled LangGraph workflow, ensuring consistent behavior, full feature utilization, and maintainable code.

## Graph Factory Pattern

### Purpose

The `GraphFactory` provides centralized, dynamic graph creation based on `agent_id`. This eliminates code duplication, enables type-safe agent execution, and makes adding new agents trivial.

### Usage

```python
from graphs.graph_factory import graph_factory

# Create graph dynamically
graph = graph_factory.create_graph(
    agent_id="chat",      # Agent identifier from registry
    model="qwen:7b",      # Optional model override
    provider="ollama"     # Optional provider override
)

# Execute with streaming
event_buffer = []

async def event_callback(event):
    """Collect events emitted by agent"""
    event_buffer.append(event)

config = {"configurable": {"event_callback": event_callback}}
result = await graph.ainvoke(state, config)

# Stream buffered events to client
for event in event_buffer:
    yield encoder.encode(event)
```

### Architecture

```
Client Request
    ↓
FastAPI Route (/chat/{agent_id})
    ↓
GraphFactory.create_graph(agent_id, model, provider)
    ↓
Compiled LangGraph Workflow
    ↓
Agent Nodes (with event_callback)
    ↓
Event Buffer
    ↓
SSE Stream to Client
```

## Streaming Pattern

All graphs implement the **event callback pattern** for AG-UI protocol compliance:

### In Graph Creator (`chat_graph.py`, `canvas_graph.py`)

```python
async def agent_node(state: AgentState, config=None):
    """Agent node with streaming callback support"""
    event_callback = config.get("configurable", {}).get("event_callback") if config else None
    
    # Agent emits AG-UI events (TEXT_MESSAGE, THINKING, etc.)
    async for event in agent.run(state):
        if event_callback:
            await event_callback(event)
    
    return state
```

### In Routes (`api/routes.py`)

```python
async def event_generator():
    yield encoder.encode(RunStartedEvent(...))
    
    # Create graph via factory
    graph = graph_factory.create_graph(agent_id, model, provider)
    state = prepare_state_for_agent(agent_id, input_data)
    
    # Event buffer
    event_buffer = []
    
    async def event_callback(event):
        event_buffer.append(event)
    
    # Execute graph
    config = {"configurable": {"event_callback": event_callback}}
    await graph.ainvoke(state, config)
    
    # Yield all events
    for event in event_buffer:
        yield encoder.encode(event)
    
    yield encoder.encode(RunFinishedEvent(...))
```

## Registered Agents

| Agent ID | Graph Creator | Purpose |
|----------|--------------|---------|
| `chat` | `create_chat_graph()` | Text-only conversations |
| `canvas` | `create_canvas_graph()` | Text + artifact generation/editing |

## Adding New Agents

### 1. Create Graph Creator

**File:** `backend/graphs/myagent_graph.py`

```python
from langgraph.graph import StateGraph, START, END
from agents.base_agent import AgentState
from agents.myagent_agent import MyAgent


def create_myagent_graph(model: str = None, provider: str = None):
    """Create workflow for MyAgent
    
    Args:
        model: Optional model name
        provider: Optional provider name
    """
    workflow = StateGraph(AgentState)
    agent = MyAgent(model=model, provider=provider)
    
    async def myagent_node(state: AgentState, config=None):
        """Node with streaming callback"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    workflow.add_node("myagent", myagent_node)
    workflow.add_edge(START, "myagent")
    workflow.add_edge("myagent", END)
    
    return workflow.compile()
```

### 2. Register in GraphFactory

**File:** `backend/graphs/graph_factory.py`

```python
from graphs.myagent_graph import create_myagent_graph

class GraphFactory:
    _graph_creators = {
        "chat": create_chat_graph,
        "canvas": create_canvas_graph,
        "myagent": create_myagent_graph,  # ← Add here
    }
```

### 3. Register in Agent Registry

**File:** `backend/agents/agent_registry.py`

```python
def _initialize_agents(self):
    # ... existing agents ...
    
    self.register_agent(AgentMetadata(
        id="myagent",
        name="My Agent",
        description="Description of capabilities",
        icon="icon-name",
        available=True,
        sub_agents=[],
        features=["feature1", "feature2"]
    ))
```

### 4. Done!

Agent is now available at `POST /chat/myagent` - no route modifications needed.

## State Preparation

The `prepare_state_for_agent()` helper handles agent-specific state:

```python
def prepare_state_for_agent(agent_id: str, input_data: RunAgentInput) -> dict:
    """Prepare state for graph execution"""
    # Base state (all agents)
    state = {
        "messages": [...],
        "thread_id": input_data.thread_id,
        "run_id": input_data.run_id
    }
    
    # Agent-specific extensions
    if agent_id == "canvas":
        state.update({
            "artifact": input_data.artifact,
            "selectedText": input_data.selectedText,
            "artifact_id": input_data.artifact_id,
            "artifactAction": input_data.action
        })
    elif agent_id == "myagent":
        state.update({
            # Custom state fields
        })
    
    return state
```

## Benefits

### ✅ Consistency
All agents execute the same way - through LangGraph workflows.

### ✅ Maintainability
Adding agents doesn't require route modifications - just register in factory.

### ✅ Type Safety
Graph creators ensure proper state schema for each agent.

### ✅ LangGraph Features
Full access to checkpointing, state persistence, conditional routing, etc.

### ✅ Testability
Easy to test graph creation and execution in isolation.

### ✅ Extensibility
New agents integrate seamlessly via registration pattern.

## Testing

### Graph Creation Tests

```python
def test_create_agent_graph():
    """Test graph creation"""
    graph = graph_factory.create_graph("myagent", model="qwen:7b")
    assert graph is not None
```

### Graph Execution Tests

```python
@pytest.mark.asyncio
async def test_agent_execution():
    """Test graph execution"""
    graph = graph_factory.create_graph("myagent")
    state = {"messages": [...], "thread_id": "test", "run_id": "test"}
    result = await graph.ainvoke(state)
    assert result is not None
```

### Callback Tests

```python
@pytest.mark.asyncio
async def test_streaming_callback():
    """Test event streaming via callback"""
    graph = graph_factory.create_graph("myagent")
    event_buffer = []
    
    async def callback(event):
        event_buffer.append(event)
    
    config = {"configurable": {"event_callback": callback}}
    await graph.ainvoke(state, config)
    # Assert events were collected
```

## Common Patterns

### Multi-Step Workflows

Canvas agent demonstrates conditional routing:

```python
START → detect_intent → [artifact_action | chat_only] → END
```

Use conditional edges for complex routing:

```python
workflow.add_conditional_edges(
    "detect_intent",
    route_function,
    {
        "path_a": "node_a",
        "path_b": "node_b"
    }
)
```

### Error Handling

Wrap graph execution in try/except and emit RunErrorEvent:

```python
try:
    await graph.ainvoke(state, config)
except Exception as e:
    yield encoder.encode(RunErrorEvent(..., message=str(e)))
```

## Debugging

### Enable Graph Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Graph Structure

```python
graph = graph_factory.create_graph("chat")
print(graph.get_graph().nodes)
print(graph.get_graph().edges)
```

### Test Graph Directly

```python
from graphs.graph_factory import graph_factory

graph = graph_factory.create_graph("chat", model="qwen:7b")
state = {"messages": [...], "thread_id": "test", "run_id": "test"}
result = await graph.ainvoke(state)
print(result)
```

## Future Enhancements

### Checkpointing

Enable conversation persistence:

```python
from langgraph.checkpoint import MemorySaver

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

### Graph Caching

Cache compiled graphs for performance:

```python
from functools import lru_cache

@lru_cache(maxsize=10)
def get_cached_graph(agent_id, model, provider):
    return graph_factory.create_graph(agent_id, model, provider)
```

### Streaming Queue

Replace event buffer with async queue:

```python
import asyncio

async def stream_events():
    queue = asyncio.Queue()
    
    async def callback(event):
        await queue.put(event)
    
    # Consume queue in parallel with graph execution
```

## References

- GraphFactory Implementation: [backend/graphs/graph_factory.py](../../backend/graphs/graph_factory.py)
- Detailed Documentation: [backend/graphs/README.md](../../backend/graphs/README.md)
- Test Suite: [backend/tests/test_graph_factory.py](../../backend/tests/test_graph_factory.py)
- LangGraph Docs: https://langchain-ai.github.io/langgraph/
