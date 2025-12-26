This is the finding in the architecture review session:
---
### Finding 3: **LangGraph Workflows Are Not Used for Streaming**
**Severity:** High  
**Impact:** LangGraph is defined but bypassed; code duplication; inconsistent execution paths

**Evidence:**
```python
# backend/api/routes.py lines 107-133
if agent_id == "chat":
    from agents.chat_agent import ChatAgent
    chat_agent = ChatAgent(model=input_data.model)
    async for event in chat_agent.run(state):
        yield encoder.encode(event)
```
Agents are instantiated directly in routes, bypassing `create_chat_graph()` and `create_canvas_graph()`.

```python
# backend/graphs/chat_graph.py
def create_chat_graph(model: str = None):
    # This is never called from routes
```

**Recommendation:**
1. Either use LangGraph properly with streaming callbacks (chosen)
2. Or remove the graphs entirely and simplify architecture
3. Don't maintain two execution paths

**Better Pattern (Option A - Use LangGraph):**
```python
# Route events through LangGraph with streaming callback
async def chat_endpoint(...):
    graph = create_chat_graph(model=input_data.model)
    
    async def event_callback(event):
        yield encoder.encode(event)
    
    config = {"configurable": {"event_callback": event_callback}}
    await graph.ainvoke(state, config)
```

Suggestion:
- Don't if else, is there anyway to create the graph based on the id?