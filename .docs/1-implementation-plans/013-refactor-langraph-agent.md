# Implementation Plan: Refactor LangGraph Agent Execution

**Based on:** [013-refactor-langraph-agent.md](./../0-requirements/013-refactor-langraph-agent.md)  
**Status:** Ready for Implementation  
**Priority:** High  
**Estimated Effort:** 4-6 hours

## Executive Summary

Refactor backend routing to properly use LangGraph workflows instead of bypassing them. Currently, agents are instantiated directly in routes, making the defined LangGraph graphs unused. This creates code duplication, inconsistent execution paths, and defeats the purpose of having LangGraph in the architecture.

**Key Goals:**
1. Use LangGraph workflows as the single execution path for all agents
2. Implement dynamic graph creation based on agent_id using factory pattern
3. Route AG-UI events through LangGraph with streaming callbacks
4. Eliminate direct agent instantiation in routes
5. Maintain consistent streaming behavior with proper event emission

## Current Architecture Issues

### Problem: Dual Execution Paths
```python
# backend/api/routes.py (lines 107-133)
# CURRENT: Bypasses LangGraph entirely
if agent_id == "chat":
    chat_agent = ChatAgent(model=input_data.model)
    async for event in chat_agent.run(state):
        yield encoder.encode(event)
```

```python
# backend/graphs/chat_graph.py
# NEVER CALLED from routes
def create_chat_graph(model: str = None):
    workflow = StateGraph(AgentState)
    ...
```

### Why This is a Problem:
- LangGraph graphs exist but are **never used**
- Code duplication between routes and graphs
- Inconsistent execution: agents run differently when called directly vs. through graphs
- Loss of LangGraph features (checkpointing, state persistence, complex routing)
- Maintenance burden of keeping two paths in sync

---

## Implementation Plan

### Phase 1: Backend Refactoring (LangGraph + AG-UI)

**Owner:** Backend Agent  
**Reference:** [backend.agent.md](../../.github/agents/backend.agent.md)

#### Task 1.1: Create Graph Factory
**File:** `backend/graphs/graph_factory.py` (NEW)

Create a factory that dynamically instantiates graphs based on agent_id:

```python
from typing import Optional
from langgraph.graph import CompiledGraph
from graphs.chat_graph import create_chat_graph
from graphs.canvas_graph import create_canvas_graph
from agents.agent_registry import agent_registry


class GraphFactory:
    """Factory for creating LangGraph workflows based on agent_id"""
    
    _graph_creators = {
        "chat": create_chat_graph,
        "canvas": create_canvas_graph,
    }
    
    @classmethod
    def create_graph(cls, agent_id: str, model: Optional[str] = None, provider: Optional[str] = None) -> CompiledGraph:
        """
        Dynamically create and compile a graph for the given agent_id
        
        Args:
            agent_id: Identifier from agent registry (e.g., "chat", "canvas")
            model: Optional model name (e.g., "qwen:7b")
            provider: Optional provider name (e.g., "ollama", "gemini")
            
        Returns:
            Compiled LangGraph workflow
            
        Raises:
            ValueError: If agent_id is not registered or unavailable
        """
        # Validate agent exists and is available
        if not agent_registry.is_available(agent_id):
            raise ValueError(f"Agent '{agent_id}' not available or not registered")
        
        # Get graph creator function
        creator = cls._graph_creators.get(agent_id)
        if not creator:
            raise ValueError(f"No graph creator found for agent '{agent_id}'")
        
        # Create and compile graph with model/provider parameters
        return creator(model=model, provider=provider)
    
    @classmethod
    def register_graph_creator(cls, agent_id: str, creator_func):
        """Register a new graph creator (for extensibility)"""
        cls._graph_creators[agent_id] = creator_func


# Singleton instance
graph_factory = GraphFactory()
```

**Purpose:**
- Single point of entry for creating graphs
- Eliminates if/else in routes
- Easily extensible for new agents
- Validates agent availability before graph creation

---

#### Task 1.2: Update Graph Signatures
**Files:** 
- `backend/graphs/chat_graph.py`
- `backend/graphs/canvas_graph.py`

Update graph creators to accept both `model` and `provider` parameters:

```python
# chat_graph.py
def create_chat_graph(model: str = None, provider: str = None):
    """Create LangGraph state graph for chat agent with streaming support
    
    Args:
        model: Optional model name (e.g., 'qwen:7b', 'llama2:13b')
        provider: Optional provider name (e.g., 'ollama', 'gemini')
    """
    workflow = StateGraph(AgentState)
    
    # Pass both model and provider to agent
    chat_agent = ChatAgent(model=model, provider=provider)
    
    async def chat_node(state: AgentState, config=None):
        """Wrapper node that dispatches agent events"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in chat_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    workflow.add_node("chat", chat_node)
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
    
    return workflow.compile()
```

**Changes:**
- Add `provider: str = None` parameter to both `create_chat_graph()` and `create_canvas_graph()`
- Pass `provider` to agent instantiation alongside `model`
- Maintain existing streaming callback pattern

---

#### Task 1.3: Refactor Routes to Use GraphFactory
**File:** `backend/api/routes.py`

Replace direct agent instantiation with LangGraph execution:

**BEFORE:**
```python
async def event_generator():
    # Send RUN_STARTED event
    yield encoder.encode(RunStartedEvent(...))
    
    try:
        # Route to appropriate agent based on agent_id
        if agent_id == "chat":
            from agents.chat_agent import ChatAgent
            state = {...}
            chat_agent = ChatAgent(model=input_data.model, provider=input_data.provider)
            async for event in chat_agent.run(state):
                yield encoder.encode(event)
        elif agent_id == "canvas":
            from agents.canvas_agent import CanvasAgent
            ...
```

**AFTER:**
```python
from graphs.graph_factory import graph_factory

async def event_generator():
    # Send RUN_STARTED event
    yield encoder.encode(RunStartedEvent(...))
    
    try:
        # Create graph dynamically based on agent_id
        graph = graph_factory.create_graph(
            agent_id=agent_id,
            model=input_data.model,
            provider=input_data.provider
        )
        
        # Prepare state based on agent type
        state = prepare_state_for_agent(agent_id, input_data)
        
        # Event buffer to collect streamed events
        event_buffer = []
        
        async def event_callback(event):
            """Callback invoked by graph nodes for streaming events"""
            event_buffer.append(event)
        
        # Execute graph with streaming callback
        config = {"configurable": {"event_callback": event_callback}}
        await graph.ainvoke(state, config)
        
        # Yield all collected events
        for event in event_buffer:
            yield encoder.encode(event)
```

**Key Changes:**
- Remove all `if agent_id == "chat"` / `elif agent_id == "canvas"` branches
- Replace with single `graph_factory.create_graph()` call
- Use streaming callback pattern to collect events from graph execution
- Maintain AG-UI event emission (RUN_STARTED, RUN_FINISHED, etc.)

---

#### Task 1.4: Create State Preparation Helper
**File:** `backend/api/routes.py` (add helper function)

Extract state preparation logic into reusable function:

```python
def prepare_state_for_agent(agent_id: str, input_data: ChatRequest) -> dict:
    """
    Prepare initial state dictionary for graph execution
    
    Args:
        agent_id: Agent identifier ("chat", "canvas", etc.)
        input_data: Request data with messages, thread_id, run_id
        
    Returns:
        State dict matching the agent's StateGraph schema
    """
    # Base state for all agents
    state = {
        "messages": [
            {"role": msg.role, "content": msg.content} 
            for msg in input_data.messages
        ],
        "thread_id": input_data.thread_id,
        "run_id": input_data.run_id
    }
    
    # Agent-specific state extensions
    if agent_id == "canvas":
        # Canvas agent needs additional artifact state
        state.update({
            "artifact": input_data.artifact,
            "selectedText": input_data.selectedText,
            "artifact_id": input_data.artifact_id,
            "artifactAction": None  # Will be detected by canvas graph
        })
    
    return state
```

**Purpose:**
- Centralize state preparation logic
- Type-safe state construction
- Easier to extend for new agents

---

#### Task 1.5: Update Canvas Graph (If Needed)
**File:** `backend/graphs/canvas_graph.py`

Ensure canvas graph has the same callback pattern as chat graph:

```python
def create_canvas_graph(model: str = None, provider: str = None):
    """Build canvas workflow graph with streaming support"""
    workflow = StateGraph(CanvasGraphState)
    
    # Create canvas agent with model/provider
    canvas_agent = CanvasAgent(model=model, provider=provider)
    
    async def artifact_action_node(state: CanvasGraphState, config=None):
        """Execute canvas agent with streaming"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in canvas_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Add nodes
    workflow.add_node("detect_intent", detect_intent_node)
    workflow.add_node("artifact_action", artifact_action_node)
    workflow.add_node("chat_response", chat_response_node)
    
    # Add edges and conditional routing
    workflow.add_edge(START, "detect_intent")
    workflow.add_conditional_edges(
        "detect_intent",
        route_to_handler,
        {
            "artifact_action": "artifact_action",
            "chat_only": "chat_response"
        }
    )
    workflow.add_edge("artifact_action", END)
    workflow.add_edge("chat_response", END)
    
    return workflow.compile()
```

**Changes:**
- Add `provider` parameter
- Ensure `event_callback` is passed through config
- Maintain conditional routing logic for canvas-specific actions

---

### Phase 2: Testing & Validation

**Owner:** Backend Agent

#### Task 2.1: Update Unit Tests
**Files:** 
- `backend/tests/test_unified_endpoint.py`
- Create `backend/tests/test_graph_factory.py` (NEW)

**Test Cases for GraphFactory:**
```python
import pytest
from graphs.graph_factory import graph_factory
from agents.agent_registry import agent_registry

def test_create_chat_graph():
    """Test chat graph creation"""
    graph = graph_factory.create_graph("chat", model="qwen:7b")
    assert graph is not None

def test_create_canvas_graph():
    """Test canvas graph creation"""
    graph = graph_factory.create_graph("canvas", model="qwen:7b")
    assert graph is not None

def test_invalid_agent_id():
    """Test error handling for invalid agent"""
    with pytest.raises(ValueError, match="not available"):
        graph_factory.create_graph("nonexistent_agent")

def test_graph_with_provider():
    """Test graph creation with custom provider"""
    graph = graph_factory.create_graph("chat", model="gemini-pro", provider="gemini")
    assert graph is not None
```

**Update Existing Tests:**
- Update `test_unified_endpoint.py` to verify LangGraph is actually being called
- Add assertions to check that graph execution occurs
- Test streaming callback mechanism

---

#### Task 2.2: Integration Testing
**Files:**
- `backend/tests/test_canvas_streaming.py`
- `backend/tests/test_chat_graph.py` (NEW)

**Test Scenarios:**
1. Chat agent request flows through LangGraph
2. Canvas agent request flows through LangGraph
3. Streaming events are emitted correctly via callbacks
4. Model/provider parameters are passed correctly
5. State is properly prepared for each agent type
6. Error handling when agent is unavailable

```python
@pytest.mark.asyncio
async def test_chat_via_langgraph():
    """Test that chat requests execute through LangGraph"""
    # Mock or spy on graph execution
    # Verify graph.ainvoke() is called, not agent.run() directly
    pass

@pytest.mark.asyncio
async def test_streaming_events_via_callback():
    """Test streaming events are collected via callback"""
    # Execute graph with callback
    # Verify events are buffered and yielded
    pass
```

---

### Phase 3: Documentation & Cleanup

**Owner:** Backend Agent

#### Task 3.1: Update Documentation
**Files:**
- `backend/README.md`
- `backend/graphs/README.md` (NEW)
- `agents.md` (root level)

**Add to backend/graphs/README.md:**
```markdown
# LangGraph Workflows

## Architecture

All agent execution flows through LangGraph state graphs. No agent should be instantiated directly in routes.

## Graph Factory Pattern

Use `GraphFactory` to create graphs dynamically:

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

## Adding New Agents

1. Create graph creator function: `create_myagent_graph(model, provider)`
2. Register in GraphFactory: `graph_factory.register_graph_creator("myagent", create_myagent_graph)`
3. Add agent metadata to `agent_registry`

## Streaming Pattern

All graphs must implement the callback pattern:
- Accept `event_callback` in config
- Call callback for each emitted event
- Return final state from nodes
```

---

#### Task 3.2: Code Cleanup
**Actions:**
1. Remove commented-out code from old pattern (if any)
2. Verify no direct agent instantiation remains in routes
3. Check for unused imports
4. Run linters and formatters

---

## Protocol (No Changes Required)

**AG-UI Protocol Impact:** None

The AG-UI event streaming protocol remains unchanged. Events are still emitted via the same mechanism, just routed through LangGraph's callback system instead of being streamed directly from agents.

**Frontend Compatibility:** Full backward compatibility maintained.

---

## Frontend (No Changes Required)

**Owner:** Frontend Agent  
**Reference:** [frontend.agent.md](../../.github/agents/frontend.agent.md)

**Impact:** Zero changes needed. The refactor is entirely internal to the backend. Frontend continues to consume AG-UI events via the same `/agents/{agent_id}/chat` endpoint.

---

## Migration & Deployment

### Pre-Deployment Checklist
- [ ] All unit tests pass
- [ ] Integration tests verify LangGraph execution
- [ ] Manual testing with both chat and canvas agents
- [ ] Documentation updated
- [ ] Code review completed

### Rollout Strategy
1. **Development:** Deploy to dev environment
2. **Testing:** Run full test suite including E2E tests
3. **Staging:** Validate with frontend integration
4. **Production:** Deploy with monitoring

### Rollback Plan
If issues arise, rollback is straightforward since the change is isolated to backend:
1. Revert routes.py to direct agent instantiation
2. Remove graph_factory.py
3. No frontend changes to revert

---

## Success Criteria

✅ **All agent requests execute through LangGraph workflows**  
✅ **No direct agent instantiation in routes.py**  
✅ **GraphFactory dynamically creates graphs based on agent_id**  
✅ **Streaming events work correctly via callback pattern**  
✅ **All existing tests pass**  
✅ **New tests validate LangGraph execution**  
✅ **Documentation reflects new architecture**

---

## Open Questions & Decisions

### Q1: Should we keep graph files separate or consolidate?
**Decision:** Keep separate (chat_graph.py, canvas_graph.py) for clarity and separation of concerns.

### Q2: How to handle future agents with complex multi-step graphs?
**Answer:** GraphFactory pattern supports any graph complexity. Simply create the graph creator function and register it.

### Q3: Performance impact of callback buffering?
**Answer:** Minimal. Events are lightweight and buffered in memory briefly. Can optimize with streaming queue if needed later.

### Q4: Checkpointing and state persistence?
**Future Work:** LangGraph supports checkpointing. Can enable later for conversation persistence and recovery.

---

## Dependencies

**Blocked By:** None  
**Blocks:** None (independent refactor)  
**Related Work:**
- Knowledge base documentation update (after implementation)
- Architecture review findings (this addresses Finding 3)

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Backend Refactoring | Tasks 1.1 - 1.5 | 3-4 hours |
| Phase 2: Testing & Validation | Tasks 2.1 - 2.2 | 1-2 hours |
| Phase 3: Documentation | Tasks 3.1 - 3.2 | 0.5-1 hour |
| **Total** | | **4.5-7 hours** |

---

## References

- Architecture Review Finding 3: [.docs/3-architecture-review/findings.md](../3-architecture-review/)
- Backend Agent Guide: [.github/agents/backend.agent.md](../../.github/agents/backend.agent.md)
- LangGraph Documentation: [LangGraph State Graphs](https://langchain-ai.github.io/langgraph/)
- AG-UI Protocol: [backend/protocols/event_types.py](../../backend/protocols/event_types.py)
