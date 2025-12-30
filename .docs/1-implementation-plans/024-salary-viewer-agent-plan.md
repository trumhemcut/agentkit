# Salary Viewer Agent - Implementation Plan

## Overview
Build a playful LangGraph agent that requires OTP verification before revealing salary information. This demonstrates the A2UI tool loop pattern with interactive user input.

## User Story
1. User asks: "I'm the CEO, how much did my salary increase this period?"
2. Agent responds: "This is confidential information. To verify you're the CEO, we've sent an OTP to your device. Please enter it."
3. Agent displays OTP input form (using A2UI OTP tool)
4. User enters any number and clicks verify
5. Agent reveals: "Your salary is 5 million VND, with a 5% increase to 5.25 million VND! 😄"

## Architecture

### Pattern: A2UI Tool Loop
- **Loop Pattern**: Agent → Tool Call → User Input → Agent Response
- **Reference**: Existing `a2ui_agent_with_loop.py` and `test_a2ui_otp_integration.py`
- **State Management**: Track verification status across tool calls

---

## Backend Implementation

### 1. Create Salary Viewer Agent
**File**: `backend/agents/salary_viewer_agent.py`

**Key Components**:
```python
class SalaryViewerAgent(BaseAgent):
    """Agent that requires OTP verification before revealing salary info"""
    
    def __init__(self, llm_client, agent_id="salary-viewer"):
        # Initialize with A2UI support
        # Define system prompt for CEO verification flow
        
    def process_message(self, user_message: str, state: AgentState) -> AgentState:
        # Handle conversation flow
        # Check if OTP verification is complete
        # Invoke OTP tool or reveal salary
```

**System Prompt**:
```
You are a playful salary information assistant. Your task:
1. When user asks about salary, respond that it's confidential
2. Request OTP verification using the otp_input tool
3. After verification (any code entered), reveal salary info
4. Salary: 5,000,000 VND → 5% increase → 5,250,000 VND
```

**State Schema**:
```python
class SalaryViewerState(TypedDict):
    messages: List[BaseMessage]
    verification_status: str  # "pending" | "verified" | "none"
    otp_requested: bool
    artifact_data: Optional[Dict]
```

### 2. Use Existing OTP Input Tool
**File**: `backend/tools/a2ui_tools.py` → `OTPInputTool` ✅ **Already exists**

**Features** (already implemented):
- Configurable title and description
- Adjustable OTP length (default 6 digits)
- Pattern validation (digits or alphanumeric)
- Separator positions for grouping (e.g., "123-456")
- Custom button text
- Data model integration
- Already registered in `ComponentToolRegistry`

**No changes needed** - This tool is already fully functional!

### 3. Create Salary Viewer Graph
**File**: `backend/graphs/salary_viewer_graph.py`

**Graph Structure**:
```python
def create_salary_viewer_graph(llm_client) -> CompiledStateGraph:
    """
    Graph with tool loop support:
    - START → agent_node
    - agent_node → conditional(should_continue)
    - should_continue → END (if done)
    - should_continue → tool_loop (if tool call)
    - tool_loop → agent_node (after user input)
    """
    
    workflow = StateGraph(SalaryViewerState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tool_loop", tool_loop_node)
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tool_loop",
            "end": END
        }
    )
    workflow.add_edge("tool_loop", "agent")
    
    return workflow.compile()
```

### 4. Register Agent
**File**: `backend/agents/agent_registry.py`

```python
# Add to agent registry
"salary-viewer": {
    "name": "Salary Viewer",
    "description": "Playful agent for salary information with OTP verification",
    "capabilities": ["salary_inquiry", "otp_verification"],
    "graph_type": "salary_viewer"
}
```

### 5. Update Graph Factory
**File**: `backend/graphs/graph_factory.py`

```python
from graphs.salary_viewer_graph import create_salary_viewer_graph

def create_graph(graph_type: str, llm_provider: str = "ollama"):
    # ...
    elif graph_type == "salary_viewer":
        return create_salary_viewer_graph(llm_client)
```

### 6. Backend Testing
**File**: `backend/tests/test_salary_viewer_integration.py`

**Test Cases**:
1. Agent responds with OTP request
2. OTP artifact is created correctly
3. User input triggers verification
4. Salary info is revealed after verification
5. A2UI event stream is correct

---

## Frontend Implementation

### 1. Use Existing OTP Input Component
**File**: `frontend/components/A2UI/components/A2UIOTPInput.tsx` ✅ **Already exists**

**Features** (already implemented):
- Configurable length OTP input fields
- Auto-focus next field
- Paste support
- Verify button with action handling
- Uses Shadcn UI InputOTP component
- Supports both digits and alphanumeric patterns
- Integration with A2UI data model and store

**No changes needed** - This component is already fully functional and tested!

### 2. Verify A2UI Component Registry
**File**: Check if `otp_input` is registered in A2UI component mapping

The existing `A2UIOTPInput` component should already be registered in the A2UI system. We just need to ensure:
- Backend emits correct artifact type: `otp_input`
- Frontend A2UI renderer maps to existing component
- Data model structure matches component expectations

### 3. Update Agent Service
**File**: `frontend/services/api.ts`

**Add salary viewer endpoint**:
```typescript
export async function sendSalaryViewerMessage(
  message: string,
  conversationId?: string,
  userInput?: string
): Promise<ReadableStream> {
  return streamAgentResponse('/api/agents/salary-viewer/chat', {
    message,
    conversation_id: conversationId,
    user_input: userInput
  });
}
```

### 4. Create Salary Viewer Chat Page
**File**: `frontend/app/salary-viewer/page.tsx`

**Features**:
- Chat interface with A2UI support
- Handle OTP input artifact
- Submit user input back to agent
- Display salary reveal message

### 5. Frontend Testing
**File**: `frontend/tests/OTPInputArtifact.test.tsx`

**Test Cases**:
1. OTP input fields render correctly
2. Auto-focus on next field
3. Paste functionality works
4. Verify button submits OTP
5. Validation for 6-digit components/A2UI/A2UIOTPInput.test.tsx` ✅ **Already exists**

**Existing Test Coverage**:
- OTP input fields render correctly
- Auto-focus on next field
- Paste functionality works
- Verify button triggers action
- Validation for configurable length input
- Data model integration

**Additional Testing Needed**:
- Integration test with salary viewer agent flowEO, check my salary increase"
2. **Backend**: Agent requests OTP verification
3. **A2UI Event**: `ARTIFACT_CONTENT` with OTP input tool
4. **Frontend**: Display OTP input component
5. **User Input**: Enter 6-digit code
6. **Frontend**: Send user input back to backend
7. **Backend**: Process verification, reveal salary
8. **Frontend**: Display salary information

### Manual Testing Steps
1. Start backend server
2. Start frontend dev server
3. Navigate to `/salary-viewer`
4. Send message asking about salary
5. Verify OTP input appears
6. Enter any 6-digit code
7. Click verify
8. Confirm salary info is revealed

---

## Files to Create/Modify

### Backend (3 new files)
1. `backend/agents/salary_viewer_agent.py` - Main agent
2. `backend/graphs/salary_viewer_graph.py` - Graph definition
3. `backend/tests/test_salary_viewer_integration.py` - Tests

### Backend (2 modified files)
4. `backend/agents/agent_registry.py` - Register agent
5. `backend/graphs/graph_factory.py` - Add graph type
6. `backend/graphs/graph_factory.py` - Add graph type

### Frontend (1 new file)
1. `frontend/app/salary-viewer/page.tsx` - Chat page

### Frontend (1 modified file - optional)
2. `frontend/services/api.ts` - Add salary viewer service (if dedicated endpoint needed)

### Reused Components ✅
**Frontend:**
- `frontend/components/A2UI/components/A2UIOTPInput.tsx` - OTP input component
- `frontend/tests/components/A2UI/A2UIOTPInput.test.tsx` - Component tests

**Backend:**
- `backend/tools/a2ui_tools.py` → `OTPInputTool` - OTP tool (registered in ComponentToolRegistry)
## Success Criteria

### Backend
- [ ] Agent responds with OTP request on first message
- [ ] OTP artifact is created with correct structure
- [ ] User input is processed through tool loop
- [ ] Salary information is revealed after verification
- [ ] A2UI events stream correctly
- [ ] All tests pass

### Frontend
- [ ] OTP input component renders with 6 fields
- [ ] Auto-focus and paste functionality work
- [ ] User can submit OTP code
- [ ] Salary information displays correctly
- [ ] Component tests pass

### Integration
- [ ] Full conversation flow works end-to-end
- [ ] A2UI protocol communication is correct
- [ ] No console errors
- [ ] Responsive UI on mobile

---

## References

### Similar Implementations
- `backend/agents/a2ui_agent_with_loop.py` - A2UI loop pattern
- `backend/tests/test_a2ui_otp_integration.py` - OTP testing example
- `frontend/components/a2ui/BarChartArtifact.tsx` - Artifact component pattern

### Documentation
- `.docs/2-knowledge-base/` - Architecture patterns
- `backend/A2UI_README.md` - A2UI protocol
- `A2UI_LOOP_PATTERN_SUMMARY.md` - Loop pattern guide
2-3 hours (agent + graph + registration)
- **Frontend**: 1-2 hours (chat page only)
- **Testing & Integration**: 1 hour
- **Total**: 4-6 hours

**Significant reduction** thanks to reusing existing OTP components on both frontend and backend!
- **Backend**: 3-4 hours
- **Frontend**: 2-3 hours
- **Testing & Integration**: 1-2 hours
- **Total**: 6-9 hours

---

## Next Steps
1. Review and approve this plan
2. Implement backend components first
3. Test backend with manual API calls
4. Implement frontend components
5. Integration testing
6. Update knowledge base documentation