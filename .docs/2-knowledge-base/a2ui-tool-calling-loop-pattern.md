# A2UI Tool-Calling Loop Pattern

## Overview

This document explains the **tool-calling loop pattern** for A2UI agents, inspired by [Building Tool-Calling Agents with LangGraph](https://sangeethasaravanan.medium.com/building-tool-calling-agents-with-langgraph-a-complete-guide-ebdcdea8f475).

## What is the Tool-Calling Loop Pattern?

The tool-calling loop pattern (also known as **ReAct pattern**: Reason → Act → Observe → Repeat) allows an LLM agent to:

1. **Reason**: Analyze the request and decide which tool to call
2. **Act**: Execute the tool
3. **Observe**: See the tool's result
4. **Repeat**: Decide if more tools are needed or if the task is complete

This enables **sequential tool calling** where the agent can call tools multiple times based on previous results.

## Two Implementations

### 1. Basic A2UI Agent (Single Tool Call)

**File**: `backend/agents/a2ui_agent.py`

**Pattern**:
```
User Request → LLM → Tool Call → Component Generated → Done
```

**Example**:
```
User: "Create a checkbox for terms"
LLM:  Calls create_checkbox tool (1 time)
      ✅ Done
```

**Pros**:
- ✅ Simple and fast
- ✅ Lower token usage
- ✅ Sufficient for single-component UIs

**Cons**:
- ❌ Can only create ONE component per request
- ❌ Cannot handle complex multi-component UIs

---

### 2. A2UI Agent with Loop (Multiple Tool Calls)

**File**: `backend/agents/a2ui_agent_with_loop.py`

**Pattern**:
```
User Request → LLM → Tool Call 1 → Result 1 →
               LLM → Tool Call 2 → Result 2 →
               LLM → Tool Call 3 → Result 3 →
               LLM → "Done" → All Components Generated
```

**Example**:
```
User: "Create a signup form with email, password, and submit button"

Loop Iteration 1:
  LLM:  "I need to create email input"
        Calls create_textinput(label="Email", placeholder="Enter your email")
  Tool: Returns component_id: "textinput-abc123"
  
Loop Iteration 2:
  LLM:  "Now I'll add password input"
        Calls create_textinput(label="Password", placeholder="Enter password", multiline=false)
  Tool: Returns component_id: "textinput-def456"
  
Loop Iteration 3:
  LLM:  "Finally, I'll add submit button"
        Calls create_button(label="Sign Up", action="submit")
  Tool: Returns component_id: "button-ghi789"
  
Loop Iteration 4:
  LLM:  "All components created. Task complete."
        No tool calls → Loop ends
        
Result: 3 components in one surface
```

**Pros**:
- ✅ Can create multiple components in sequence
- ✅ LLM reasons about what components are needed
- ✅ Enables complex UI composition
- ✅ Flexible and extensible

**Cons**:
- ❌ Higher token usage (multiple LLM calls)
- ❌ Slower (especially for simple UIs)
- ❌ Requires careful max_iterations limit

## When to Use Each

| Scenario | Basic Agent | Loop Agent |
|----------|-------------|------------|
| Single component ("Create a checkbox") | ✅ **Recommended** | ⚠️ Overkill |
| Multiple known components ("3 checkboxes") | ✅ Use `create_checkboxes` tool | ⚠️ Overkill |
| Complex multi-component UI ("Signup form with email, password, button") | ❌ Only creates 1st | ✅ **Recommended** |
| Dynamic UI generation (agent decides what's needed) | ❌ Limited | ✅ **Recommended** |
| Performance-critical | ✅ Fast | ❌ Slower |
| Token budget-conscious | ✅ Low usage | ❌ High usage |

## Implementation Details

### Loop Agent Architecture

```python
class A2UIAgentWithLoop(BaseAgent):
    async def _tool_calling_loop(self, user_prompt: str):
        # Initialize conversation with system prompt
        conversation = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Get LLM with tools bound
        model_with_tools = self.llm_provider.get_model_with_tools(tool_schemas)
        
        # Loop until done or max_iterations
        iteration = 0
        components_data = []
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # 1. Call LLM
            response = await model_with_tools.ainvoke(conversation)
            conversation.append(response)
            
            # 2. Check if LLM called any tools
            if not response.tool_calls:
                break  # LLM is done
            
            # 3. Execute all tool calls
            for tool_call in response.tool_calls:
                tool_result = execute_tool(tool_call)
                components_data.append(tool_result)
                
                # 4. Add tool result back to conversation
                tool_message = ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"]
                )
                conversation.append(tool_message)
            
            # Loop continues: LLM sees tool results and decides next action
        
        return components_data
```

### Key Concepts

#### 1. Conversation History
The loop maintains a conversation with the LLM:
```python
[
    SystemMessage("You are a UI generator..."),
    HumanMessage("Create signup form..."),
    AIMessage(tool_calls=[{name: "create_textinput", ...}]),
    ToolMessage("Created textinput-abc123"),
    AIMessage(tool_calls=[{name: "create_button", ...}]),
    ToolMessage("Created button-def456"),
    AIMessage("All components created.")
]
```

#### 2. Tool Result Feedback
After each tool execution, the result is fed back to the LLM:
```python
tool_message = ToolMessage(
    content="Successfully created checkbox with ID: checkbox-123",
    tool_call_id=tool_call["id"]
)
conversation.append(tool_message)
```

This allows the LLM to:
- Verify the tool succeeded
- Use the component ID for future decisions
- Decide if more components are needed

#### 3. Termination Conditions
The loop ends when:
- LLM returns a message without tool calls (natural end)
- Max iterations reached (safety limit)
- Error occurs (with error handling)

## LangGraph Integration

### Basic Graph
```python
# backend/graphs/a2ui_loop_graph.py

def create_a2ui_loop_graph(model=None, provider=None, max_iterations=5):
    workflow = StateGraph(AgentState)
    
    agent = A2UIAgentWithLoop(provider=provider, model=model, max_iterations=max_iterations)
    
    async def agent_node(state, config=None):
        async for event in agent.run(state):
            # Stream events (includes internal loop)
            yield event
        return state
    
    workflow.add_node("agent", agent_node)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)
    
    return workflow.compile()
```

### Alternative: Explicit ToolNode Graph
For more control, you can model the loop explicitly in LangGraph:

```python
# Future implementation option
def create_a2ui_loop_graph_with_toolnode(model=None, provider=None):
    workflow = StateGraph(AgentState)
    
    # Define nodes
    workflow.add_node("agent", agent_node)      # Decides tool or finish
    workflow.add_node("tools", ToolNode(tools)) # Executes tools
    
    # Conditional routing
    def should_continue(state):
        return "tools" if state.get("tool_calls") else "end"
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END}
    )
    workflow.add_edge("tools", "agent")  # Loop back to agent
    
    return workflow.compile()
```

**Graph visualization**:
```
    START
      ↓
    agent ──→ should_continue?
      ↑           ↓           ↓
      │         tools        END
      └───────────┘
   (Loop until done)
```

## Usage Examples

### Example 1: Simple Request (Both Work)

```python
# Basic agent
agent = A2UIAgent()
state = {
    "messages": [{"role": "user", "content": "Create a checkbox"}],
    "thread_id": "thread-1",
    "run_id": "run-1"
}
async for event in agent.run(state):
    print(event)
# Result: 1 checkbox created ✅
```

```python
# Loop agent (same result, but more overhead)
agent = A2UIAgentWithLoop(max_iterations=5)
state = {
    "messages": [{"role": "user", "content": "Create a checkbox"}],
    "thread_id": "thread-1",
    "run_id": "run-1"
}
async for event in agent.run(state):
    print(event)
# Result: 1 checkbox created ✅
```

### Example 2: Complex Request (Only Loop Works Well)

```python
# Basic agent - LIMITATION
agent = A2UIAgent()
state = {
    "messages": [{"role": "user", "content": "Create email input, password input, and submit button"}],
    "thread_id": "thread-2",
    "run_id": "run-2"
}
async for event in agent.run(state):
    print(event)
# Result: Only 1 component created ❌ (whichever LLM calls first)
```

```python
# Loop agent - WORKS
agent = A2UIAgentWithLoop(max_iterations=5)
state = {
    "messages": [{"role": "user", "content": "Create email input, password input, and submit button"}],
    "thread_id": "thread-2",
    "run_id": "run-2"
}
async for event in agent.run(state):
    print(event)
# Result: 3 components created ✅
# - textinput (email)
# - textinput (password)
# - button (submit)
```

## Configuration

### Max Iterations
Control how many tool-calling loops are allowed:

```python
agent = A2UIAgentWithLoop(
    provider="ollama",
    model="qwen:7b",
    max_iterations=5  # Max 5 tool calls
)
```

**Recommendations**:
- Simple UIs: `max_iterations=3`
- Complex UIs: `max_iterations=5-7`
- Very complex: `max_iterations=10` (but watch token usage)

### System Prompt Tuning
Customize the system prompt to guide the agent:

```python
system_prompt = """You are a UI component generator.

Rules:
- Create components ONE AT A TIME
- After each component, assess if more are needed
- Be concise in your reasoning
- Stop when all requested components are created

Available tools: create_checkbox, create_textinput, create_button, etc.
"""
```

## Testing

Run the test suite to see both patterns in action:

```bash
cd backend
python tests/test_a2ui_loop_pattern.py
```

Expected output:
```
TEST 1: Basic A2UI Agent (Single Tool Call)
✓ Generated component event
✅ Basic agent test completed

TEST 2: Loop A2UI Agent - Simple Request  
✓ Generated component event
✅ Loop agent (simple) test completed

TEST 3: Loop A2UI Agent - Complex Request
✓ Surface created with components
✅ Loop agent (complex) test completed (3 components)

COMPARISON: Basic vs Loop Pattern
┌─────────────────────┬──────────────────────┬────────────────────┐
│ Single component    │ ✅ Works (1 tool)     │ ✅ Works (1 loop)   │
│ Multiple components │ ❌ Only creates 1st   │ ✅ Creates all      │
└─────────────────────┴──────────────────────┴────────────────────┘
```

## Performance Considerations

### Token Usage

**Basic Agent** (single component):
- 1 LLM call with tools
- ~500-1000 tokens

**Loop Agent** (3 components):
- 4+ LLM calls (1 initial + 3 with tool results + 1 finish)
- ~2000-4000 tokens
- **4-8x more tokens**

### Latency

**Basic Agent**:
- 1 LLM call: ~1-2 seconds

**Loop Agent**:
- 4 LLM calls: ~4-8 seconds
- **4x slower**

### Recommendations

1. **Default to basic agent** for most use cases
2. **Use loop agent only when**:
   - User explicitly requests multiple components
   - UI complexity requires sequential reasoning
   - You need dynamic component generation

3. **Consider hybrid approach**:
   ```python
   # Detect if request needs multiple components
   if requires_multiple_components(user_message):
       agent = A2UIAgentWithLoop(max_iterations=5)
   else:
       agent = A2UIAgent()  # Faster for simple cases
   ```

## Future Enhancements

### 1. Smart Tool Batching
Instead of sequential loops, call multiple tools in parallel:

```python
# Loop iteration 1
LLM: Calls [create_textinput, create_textinput, create_button] in parallel
Tools: All execute simultaneously
Result: 3 components in 1 iteration
```

### 2. Tool Result Summarization
Reduce token usage by summarizing tool results:

```python
# Instead of full component JSON
tool_message = ToolMessage(content="Created textinput-abc123")

# Use summary
tool_message = ToolMessage(content="✅ Email input created")
```

### 3. Streaming Tool Execution
Stream A2UI events during tool execution, not after:

```python
# Current: All components at end
# Future: Component-by-component streaming
for tool_call in tool_calls:
    component = execute_tool(tool_call)
    yield a2ui_encoder.encode(SurfaceUpdate(component))  # Stream immediately
```

## References

- [Building Tool-Calling Agents with LangGraph](https://sangeethasaravanan.medium.com/building-tool-calling-agents-with-langgraph-a-complete-guide-ebdcdea8f475)
- [LangGraph Tool Calling Documentation](https://python.langchain.com/docs/langgraph/concepts/tool_calling)
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- Backend Agent Guide: [.github/agents/backend.agent.md](../../../.github/agents/backend.agent.md)

## Summary

| Aspect | Basic Agent | Loop Agent |
|--------|-------------|------------|
| **Tool calls** | 1 | 1-N |
| **Use case** | Single component | Multiple components |
| **Token usage** | Low | High |
| **Latency** | Fast | Slower |
| **Complexity** | Simple | Complex |
| **Recommended for** | Most cases | Complex UIs only |

**Key Takeaway**: The loop pattern enables powerful multi-component UI generation, but comes with trade-offs in performance and token usage. Choose wisely based on your use case.
