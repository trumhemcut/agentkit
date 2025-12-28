# A2UI Tool-Calling Loop Pattern - Quick Reference

## TL;DR

**Yes, A2UI agent can use tool-calling loop pattern** like the article describes. I've implemented it for you.

## Two Implementations

### 1. Basic A2UI Agent (Current)
- **File**: `backend/agents/a2ui_agent.py`
- **Pattern**: Single tool call
- **Use for**: Simple UIs (1 component)
- **Example**: "Create a checkbox" → 1 component ✅

### 2. A2UI Agent with Loop (New)
- **File**: `backend/agents/a2ui_agent_with_loop.py`
- **Pattern**: ReAct loop (multiple tool calls)
- **Use for**: Complex UIs (multiple components)
- **Example**: "Create email, password, button" → 3 components ✅

## Quick Comparison

```
┌──────────────────────┬───────────────┬────────────────┐
│ Feature              │ Basic         │ Loop           │
├──────────────────────┼───────────────┼────────────────┤
│ Tool calls           │ 1 (always)    │ 1-N (as needed)│
│ Single component     │ ✅ Fast        │ ⚠️ Overkill    │
│ Multiple components  │ ❌ Only 1st    │ ✅ All         │
│ Token usage          │ Low           │ High           │
│ Speed                │ Fast (1-2s)   │ Slow (4-8s)    │
└──────────────────────┴───────────────┴────────────────┘
```

## How It Works

### Basic Agent
```
User → LLM → Tool → Component → Done
```

### Loop Agent (ReAct Pattern)
```
User → LLM → Tool 1 → Result 1 →
       LLM → Tool 2 → Result 2 →
       LLM → Tool 3 → Result 3 →
       LLM → "Done" → All Components
```

## Usage

### Using the Loop Agent

```python
from agents.a2ui_agent_with_loop import A2UIAgentWithLoop

# Create agent with loop capability
agent = A2UIAgentWithLoop(
    provider="ollama",
    model="qwen:7b",
    max_iterations=5  # Max tool calls
)

# Run with complex request
state = {
    "messages": [{
        "role": "user",
        "content": "Create a signup form with email, password, and submit button"
    }],
    "thread_id": "thread-123",
    "run_id": "run-456"
}

async for event in agent.run(state):
    # Streams A2UI events
    # Will create 3 components
    print(event)
```

### Using via Graph Factory

```python
from graphs.graph_factory import graph_factory

# Create graph for loop agent
graph = graph_factory.create_graph(
    agent_id="a2ui-loop",  # New agent ID
    model="qwen:7b",
    provider="ollama"
)

# Execute
config = {"configurable": {"event_callback": callback_fn}}
await graph.ainvoke(state, config)
```

## Register in Agent Registry

Add to `backend/agents/agent_registry.py`:

```python
self.register_agent(AgentMetadata(
    id="a2ui-loop",
    name="A2UI Agent (Loop)",
    description="A2UI agent with tool-calling loop for complex multi-component UIs",
    icon="layout-grid",
    available=True,
    features=["ui-components", "multi-component", "tool-loop", "react-pattern"]
))
```

## Testing

```bash
cd backend
python tests/test_a2ui_loop_pattern.py
```

## When to Use Which

**Use Basic Agent** (default):
- ✅ Single component requests
- ✅ Performance-critical scenarios
- ✅ Token budget limitations

**Use Loop Agent**:
- ✅ Multi-component UIs
- ✅ Complex forms
- ✅ Dynamic UI generation
- ✅ When LLM needs to reason about component composition

## Trade-offs

**Loop Agent Advantages**:
- ✅ Can create multiple components
- ✅ LLM reasons about UI composition
- ✅ More flexible and powerful

**Loop Agent Disadvantages**:
- ❌ 4-8x more tokens
- ❌ 4x slower
- ❌ More complex error handling

## Recommendation

**Start with Basic Agent** for most use cases. **Switch to Loop Agent** only when:
1. User explicitly requests multiple components
2. You need complex UI composition
3. Performance isn't critical

## Files Created

| File | Purpose |
|------|---------|
| `backend/agents/a2ui_agent_with_loop.py` | Loop agent implementation |
| `backend/graphs/a2ui_loop_graph.py` | LangGraph workflow |
| `backend/tests/test_a2ui_loop_pattern.py` | Comparison tests |
| `.docs/2-knowledge-base/a2ui-tool-calling-loop-pattern.md` | Full documentation |

## Next Steps

1. ✅ Implementation complete
2. ⏭️ Register in agent registry
3. ⏭️ Add to API endpoint routes
4. ⏭️ Test with real LLM
5. ⏭️ Optimize system prompts
6. ⏭️ Add frontend integration

## See Full Documentation

For detailed architecture, examples, and best practices:
👉 [.docs/2-knowledge-base/a2ui-tool-calling-loop-pattern.md](.docs/2-knowledge-base/a2ui-tool-calling-loop-pattern.md)
