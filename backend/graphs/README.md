# LangGraph Workflows

## Architecture Overview

All agent execution flows through **LangGraph state graphs**. Agents are never instantiated directly in routes or endpoints. This ensures:
- Consistent execution paths for all agents
- Full utilization of LangGraph features (checkpointing, state persistence, complex routing)
- Single source of truth for agent behavior
- Easier testing and debugging

## Graph Factory Pattern

The `GraphFactory` provides centralized, dynamic graph creation based on agent_id:

```python
from graphs.graph_factory import graph_factory

# Create graph for any registered agent
graph = graph_factory.create_graph(
    agent_id="chat",
    model="qwen:7b",
    provider="ollama"
)

# Execute with streaming
config = {"configurable": {"event_callback": callback_fn}}
result = await graph.ainvoke(state, config)
```

### Key Benefits

1. **No Direct Agent Instantiation**: Routes never import or instantiate agents directly
2. **Dynamic Routing**: Agent selection happens at runtime via agent_id
3. **Type Safety**: Graph creators ensure proper state schema for each agent
4. **Extensibility**: Adding new agents doesn't require modifying routes

## Streaming Pattern

All graphs implement the **event callback pattern** for AG-UI protocol compliance:

```python
async def my_agent_node(state: AgentState, config=None):
    """Agent node with streaming support"""
    event_callback = config.get("configurable", {}).get("event_callback") if config else None
    
    async for event in agent.run(state):
        if event_callback:
            await event_callback(event)
    
    return state
```

### How It Works

1. **Routes** pass an `event_callback` function in the graph config
2. **Graph nodes** extract the callback from config
3. **Agents** emit AG-UI events (TEXT_MESSAGE, THINKING, etc.)
4. **Callback** collects events in a buffer
5. **Routes** yield buffered events to client via SSE

## Graph Structure

### Chat Graph (`chat_graph.py`)

Simple linear workflow:
```
START → chat_node → END
```

### Canvas Graph (`canvas_graph.py`)

Multi-step workflow with conditional routing:
```
START → detect_intent → [artifact_action | chat_only] → END
                             ↓             ↓
                      canvas_agent    chat_response
                             ↓
                      update_artifact
```

## Adding New Agents

Follow these steps to add a new agent to the system:

### 1. Create Graph Creator Function

Create `backend/graphs/myagent_graph.py`:

```python
from langgraph.graph import StateGraph, START, END
from agents.base_agent import AgentState
from agents.myagent_agent import MyAgent


def create_myagent_graph(model: str = None, provider: str = None):
    """Create LangGraph workflow for MyAgent
    
    Args:
        model: Optional model name (e.g., 'qwen:7b')
        provider: Optional provider name (e.g., 'ollama', 'gemini')
    """
    workflow = StateGraph(AgentState)
    
    # Create agent with model/provider
    my_agent = MyAgent(model=model, provider=provider)
    
    async def myagent_node(state: AgentState, config=None):
        """Wrapper node with streaming callback support"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in my_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Build graph
    workflow.add_node("myagent", myagent_node)
    workflow.add_edge(START, "myagent")
    workflow.add_edge("myagent", END)
    
    return workflow.compile()
```

### 2. Register in GraphFactory

Add to `backend/graphs/graph_factory.py`:

```python
from graphs.myagent_graph import create_myagent_graph

class GraphFactory:
    _graph_creators = {
        "chat": create_chat_graph,
        "canvas": create_canvas_graph,
        "myagent": create_myagent_graph,  # Add new agent
    }
```

Or register dynamically:

```python
from graphs.graph_factory import graph_factory
from graphs.myagent_graph import create_myagent_graph

graph_factory.register_graph_creator("myagent", create_myagent_graph)
```

### 3. Register in Agent Registry

Update `backend/agents/agent_registry.py`:

```python
def _initialize_agents(self):
    # ... existing agents ...
    
    self.register_agent(AgentMetadata(
        id="myagent",
        name="My Agent",
        description="Description of my agent's capabilities",
        icon="icon-name",
        available=True,
        sub_agents=["sub1", "sub2"],  # If multi-agent
        features=["feature1", "feature2"]
    ))
```

### 4. That's It!

No changes needed to routes. The agent is automatically available at:
```
POST /chat/myagent
```

## State Preparation

The `prepare_state_for_agent()` helper in routes.py handles agent-specific state:

```python
def prepare_state_for_agent(agent_id: str, input_data: RunAgentInput) -> dict:
    """Prepare initial state for graph execution"""
    # Base state for all agents
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
            ...
        })
    
    return state
```

Add new cases for agents with custom state requirements.

## Testing

### Unit Tests

Test graph creation and execution:

```python
def test_create_myagent_graph():
    """Test graph creation"""
    graph = graph_factory.create_graph("myagent", model="qwen:7b")
    assert graph is not None

@pytest.mark.asyncio
async def test_myagent_execution():
    """Test graph execution"""
    graph = graph_factory.create_graph("myagent")
    state = {"messages": [...], "thread_id": "test", "run_id": "test"}
    result = await graph.ainvoke(state)
    assert result is not None
```

### Integration Tests

Test end-to-end flow through routes:

```python
@pytest.mark.asyncio
async def test_myagent_endpoint():
    """Test /chat/myagent endpoint"""
    response = await client.post("/chat/myagent", json={
        "messages": [{"role": "user", "content": "test"}],
        "thread_id": "test",
        "run_id": "test"
    })
    assert response.status_code == 200
```

## Debugging

### Enable Graph Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("graphs")
```

### Inspect Graph Structure

```python
from graphs.graph_factory import graph_factory

graph = graph_factory.create_graph("chat")
print(graph.get_graph().nodes)
print(graph.get_graph().edges)
```

### Test Graph Execution

```python
state = {"messages": [...], "thread_id": "test", "run_id": "test"}
result = await graph.ainvoke(state)
print(result)
```

## Performance Considerations

### Event Buffering

Events are collected in memory before streaming to client. For long-running agents:
- Consider streaming queue instead of list buffer
- Monitor memory usage with many concurrent requests

### Graph Compilation

Graphs are compiled on each request. For better performance:
- Consider caching compiled graphs (future enhancement)
- Use singleton pattern for expensive resources

### State Size

Keep state minimal to avoid serialization overhead:
- Don't store large artifacts in state
- Use artifact_id references instead
- Clean up state between nodes

## Future Enhancements

### Checkpointing

LangGraph supports checkpointing for conversation persistence:

```python
from langgraph.checkpoint import MemorySaver

checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

### Streaming Queue

Replace event buffer with async queue for true streaming:

```python
import asyncio

async def stream_events():
    queue = asyncio.Queue()
    
    async def callback(event):
        await queue.put(event)
    
    # Process queue in parallel
    ...
```

### Graph Caching

Cache compiled graphs for better performance:

```python
from functools import lru_cache

@lru_cache(maxsize=10)
def get_cached_graph(agent_id: str, model: str, provider: str):
    return graph_factory.create_graph(agent_id, model, provider)
```

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [AG-UI Protocol](../protocols/event_types.py)
- [Backend Agent Guide](../../.github/agents/backend.agent.md)
- [Agent Registry](../agents/agent_registry.py)
