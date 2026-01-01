# Implementation Plan: Improve Salary Viewer Agent with User Action Handling

**Requirement**: [026-improve-salary-reviewer-agent.md](../0-requirements/026-improve-salary-reviewer-agent.md)  
**Created**: January 1, 2026  
**Status**: Planning  
**Dependencies**: 
- [024-salary-viewer-agent-plan.md](024-salary-viewer-agent-plan.md) - Base Salary Viewer Agent
- [025-handling-events-for-components-plan.md](025-handling-events-for-components-plan.md) - User Action Protocol

## Executive Summary

The Salary Viewer Agent currently supports streaming OTP components to the frontend but does not handle user actions from the frontend. This plan implements **bidirectional communication** to enable the agent to receive and process user actions when the "Verify" button is clicked on the OTP component.

**Current State**: 
- ✅ Agent generates OTP input component → Frontend renders
- ✅ User can enter OTP digits in frontend
- ❌ No handler for "Verify" button click → Agent doesn't receive user input

**Target State**:
- ✅ Agent generates OTP input component → Frontend renders
- ✅ User enters OTP and clicks "Verify" → Agent receives action
- ✅ Agent echoes OTP back in chat: "You entered OTP: {code}"

**Key Protocol**: A2UI v0.9 `userAction` messages (client-to-server)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│              SALARY VIEWER USER ACTION FLOW                         │
└─────────────────────────────────────────────────────────────────────┘

Frontend (React)                Backend (FastAPI)         Salary Viewer Agent
─────────────────               ──────────────────        ───────────────────
                                                                
1. User enters OTP digits                                        
   (e.g., "123456")                                              
                                                                
2. User clicks "Verify"  ─────>                                        
   button                                                               
                                                                        
3. A2UIManager collects  ─────>                                        
   OTP from data model                                              
   (/otp_verification/code)                                             
                                                                        
4. POST /agents/salary-viewer/action ──> 5. Route receives               
   Body:                               userAction payload                   
   {                                                                        
     "userAction": {                                                        
       "name": "verify_otp",      6. Parse & validate    ────>  7. Agent receives
       "surfaceId": "otp_form",      userAction                    action event
       "context": {                                                          
         "code": "123456"                                            8. Process:
       }                                                               - Extract OTP
     }                                                                 - Update state
   }                                                                   - Generate response
                                                                        
                                9. Stream response      <────  10. Agent echoes:
                                   (TEXT_MESSAGE_CHUNK)            "You entered OTP:
                                                                    123456"
                                                                        
11. Receive & display    <─────                                11. Then reveals
    chat message                                                   salary info
```

---

## Implementation Plan

### Phase 1: Update Salary Viewer Agent to Handle User Actions

**Owner**: Backend Agent  
**File**: `backend/agents/salary_viewer_agent.py`

#### 1.1 Modify `run()` Method to Check for User Actions

Currently, the agent checks `state.get("user_input")` but this is not the A2UI protocol standard. Update to use `state.get("user_action")`.

**Current Code**:
```python
async def run(self, state: AgentState) -> AsyncGenerator[str, None]:
    user_input = state.get("user_input")
    
    if user_input:
        logger.info(f"User provided OTP input: {user_input}")
        self.verification_status = "verified"
        
        # Send confirmation and reveal salary
        async for event in self._reveal_salary_info():
            yield event
        return
```

**Updated Code**:
```python
async def run(self, state: AgentState) -> AsyncGenerator[str, None]:
    """
    Handle salary inquiry with OTP verification.
    
    Flow:
    1. Check if this is first message → request OTP
    2. If OTP tool called → wait for user input
    3. If user action received → echo OTP and reveal salary
    
    Args:
        state: Agent state
            
    Yields:
        SSE-formatted A2UI and AG-UI events
    """
    messages = state.get("messages", [])
    thread_id = state["thread_id"]
    run_id = state["run_id"]
    user_action = state.get("user_action")  # A2UI protocol user action
    
    user_message = messages[-1].get("content", "") if messages else ""
    logger.info(f"Salary Viewer Agent - thread: {thread_id}, user: '{user_message}', user_action: {user_action}")
    
    # Check if user action received (Verify button clicked)
    if user_action:
        action_name = user_action.get("name")
        action_context = user_action.get("context", {})
        
        logger.info(f"User action received: {action_name}, context: {action_context}")
        
        # Extract OTP from action context
        otp_code = action_context.get("code", "")
        
        if action_name == "verify_otp" and otp_code:
            self.verification_status = "verified"
            
            # Echo OTP back to user
            async for event in self._echo_otp_message(otp_code):
                yield event
            
            # Reveal salary information
            async for event in self._reveal_salary_info():
                yield event
            return
        else:
            # Unknown action or missing OTP
            async for event in self._send_error_message(
                "Invalid verification attempt. Please try again."
            ):
                yield event
            return
    
    # ... rest of the existing code for initial OTP request ...
```

**Changes**:
- Replace `user_input` check with `user_action` check
- Extract action name and context from user action payload
- Validate action name is "verify_otp"
- Extract OTP code from context
- Call new `_echo_otp_message()` method before revealing salary

---

#### 1.2 Create Echo OTP Message Method

Add new helper method to send a chat message echoing the OTP entered by user.

**New Method**:
```python
async def _echo_otp_message(self, otp_code: str) -> AsyncGenerator[str, None]:
    """
    Send message echoing the OTP code entered by user.
    
    Args:
        otp_code: The OTP code entered by user
        
    Yields:
        SSE-formatted AG-UI text message events
    """
    message_text = f"📩 Bạn đã nhập mã OTP: **{otp_code}**\n\nĐang xác thực..."
    message_id = f"msg-{uuid.uuid4().hex[:8]}"
    
    # Start message
    start_event = TextMessageStartEvent(
        type=EventType.TEXT_MESSAGE_START,
        message_id=message_id,
        role="assistant",
        metadata={"message_type": "text"}
    )
    yield self.agui_encoder.encode(start_event)
    
    # Content
    content_event = TextMessageContentEvent(
        type=EventType.TEXT_MESSAGE_CONTENT,
        message_id=message_id,
        delta=message_text
    )
    yield self.agui_encoder.encode(content_event)
    
    # End message
    end_event = TextMessageEndEvent(
        type=EventType.TEXT_MESSAGE_END,
        message_id=message_id
    )
    yield self.agui_encoder.encode(end_event)
```

**Location**: Add after `_send_confirmation_message()` method around line 360

---

#### 1.3 Update OTP Tool to Include Action

The OTP component needs to have an action defined on the Button component so that clicking "Verify" triggers a `userAction` message.

**File to Check**: `backend/tools/a2ui_tools.py` → `OTPInputTool.generate_component()`

**Current Button Component** (needs verification):
```python
{
    "type": "Button",
    "id": f"{component_id}-button",
    "text": button_text or "Verify",
    # Need to add action here
}
```

**Updated Button Component**:
```python
{
    "type": "Button",
    "id": f"{component_id}-button",
    "text": button_text or "Verify",
    "action": {
        "name": "verify_otp",
        "context": {
            "code": {
                "path": f"/{component_id}/code"  # Path to OTP value in data model
            }
        }
    }
}
```

**Action Details**:
- **name**: "verify_otp" - This will be sent in the userAction message
- **context.code.path**: Path to the OTP code in the data model (e.g., "/otp_verification/code")
- When button is clicked, the client resolves the path and sends the value

**Note**: Need to verify if `OTPInputTool` already has this action or if it needs to be added.

---

### Phase 2: Register Salary Viewer Agent with A2UI Features

**File**: `backend/agents/agent_registry.py`

Ensure the salary viewer agent is registered with A2UI protocol support so the `/agents/{agent_id}/action` endpoint accepts requests.

**Check Current Registration**:
```python
# Find salary viewer registration
agents = [
    AgentInfo(
        id="salary-viewer",
        name="Salary Viewer",
        # ...
        features=["a2ui", "otp-verification"]  # Ensure "a2ui" is present
    )
]
```

**Required Features**:
- `"a2ui"` or `"a2ui-protocol"` - Enables user action endpoint

If not present, add to the agent's features list.

---

### Phase 3: Update Salary Viewer Graph (If Needed)

**File**: `backend/graphs/salary_viewer_graph.py`

Current graph is simple: `START → salary_viewer_agent → END`

**Check**: Does the graph need modification to handle user actions?

**Answer**: **No changes needed** because:
1. User actions come through the same `/agents/{agent_id}/action` endpoint
2. The graph receives state with `user_action` field already populated
3. The agent's `run()` method handles the user action internally

The graph structure remains:
```python
START → salary_viewer_agent → END
```

User actions are just another type of input to the agent node.

---

### Phase 4: Testing

#### 4.1 Create Manual Test Script

**File**: `backend/tests/manual_test_salary_viewer_action.py`

```python
"""
Manual test for Salary Viewer Agent with User Action handling

This test simulates the complete flow:
1. User asks about salary
2. Agent generates OTP component
3. User enters OTP and clicks Verify
4. Agent echoes OTP and reveals salary
"""

import asyncio
import uuid
from agents.salary_viewer_agent import SalaryViewerAgent


async def test_salary_viewer_user_action():
    """Test complete flow with user action"""
    
    agent = SalaryViewerAgent(provider="ollama", model="qwen:7b")
    
    # Step 1: Initial request
    print("\n=== STEP 1: Initial Request ===")
    state1 = {
        "messages": [
            {"role": "user", "content": "Tôi là Tổng tài, cho hỏi lương kỳ này tăng bao nhiêu?"}
        ],
        "thread_id": f"test-thread-{uuid.uuid4().hex[:8]}",
        "run_id": f"test-run-{uuid.uuid4().hex[:8]}"
    }
    
    events1 = []
    async for event in agent.run(state1):
        events1.append(event)
        # Print events for debugging
        if "TEXT_MESSAGE_CONTENT" in event:
            print(f"Agent: {event}")
        elif "surfaceUpdate" in event:
            print(f"A2UI: Generated OTP component")
    
    print(f"\nTotal events in step 1: {len(events1)}")
    
    # Step 2: Simulate user action (Verify button clicked)
    print("\n=== STEP 2: User Action (Verify Button) ===")
    state2 = {
        "messages": [],
        "thread_id": state1["thread_id"],
        "run_id": f"test-run-{uuid.uuid4().hex[:8]}",
        "user_action": {
            "name": "verify_otp",
            "surfaceId": "otp_form",
            "sourceComponentId": "verify_button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {
                "code": "123456"  # OTP entered by user
            }
        }
    }
    
    events2 = []
    async for event in agent.run(state2):
        events2.append(event)
        # Print agent responses
        if "TEXT_MESSAGE_CONTENT" in event:
            print(f"Agent: {event}")
    
    print(f"\nTotal events in step 2: {len(events2)}")
    
    # Verify expectations
    print("\n=== VERIFICATION ===")
    
    # Step 1 should generate OTP component
    has_otp = any("OTPInput" in event for event in events1)
    print(f"✓ OTP component generated: {has_otp}")
    
    # Step 2 should echo OTP
    has_echo = any("123456" in event for event in events2)
    print(f"✓ OTP echoed in response: {has_echo}")
    
    # Step 2 should reveal salary
    has_salary = any("5,250,000" in event or "5.25" in event for event in events2)
    print(f"✓ Salary revealed: {has_salary}")
    
    if has_otp and has_echo and has_salary:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")


if __name__ == "__main__":
    asyncio.run(test_salary_viewer_user_action())
```

**Run Command**:
```bash
cd backend
python -m tests.manual_test_salary_viewer_action
```

---

#### 4.2 Create Integration Test

**File**: `backend/tests/test_salary_viewer_action.py`

```python
"""
Integration tests for Salary Viewer Agent with User Action handling
"""

import pytest
from agents.salary_viewer_agent import SalaryViewerAgent


@pytest.mark.asyncio
async def test_salary_viewer_initial_request_generates_otp():
    """Test that initial request generates OTP component"""
    agent = SalaryViewerAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [
            {"role": "user", "content": "I'm the CEO, what's my salary?"}
        ],
        "thread_id": "test-thread-1",
        "run_id": "test-run-1"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should generate OTP component
    has_otp = any("OTPInput" in event for event in events)
    assert has_otp, "OTP component should be generated"
    
    # Should send confirmation message
    has_confirmation = any(
        "verification" in event.lower() or "otp" in event.lower() 
        for event in events
    )
    assert has_confirmation


@pytest.mark.asyncio
async def test_salary_viewer_handles_verify_action():
    """Test that agent handles verify_otp user action"""
    agent = SalaryViewerAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [],
        "thread_id": "test-thread-2",
        "run_id": "test-run-2",
        "user_action": {
            "name": "verify_otp",
            "surfaceId": "otp_form",
            "sourceComponentId": "verify_button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {
                "code": "999888"
            }
        }
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should echo OTP back
    has_echo = any("999888" in event for event in events)
    assert has_echo, "Agent should echo the OTP code"
    
    # Should reveal salary info
    has_salary = any(
        "5,250,000" in event or "5.25" in event or "salary" in event.lower()
        for event in events
    )
    assert has_salary, "Agent should reveal salary information"


@pytest.mark.asyncio
async def test_salary_viewer_handles_invalid_action():
    """Test that agent handles invalid user actions gracefully"""
    agent = SalaryViewerAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [],
        "thread_id": "test-thread-3",
        "run_id": "test-run-3",
        "user_action": {
            "name": "unknown_action",
            "surfaceId": "form",
            "sourceComponentId": "button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {}
        }
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should send error message
    has_error = any("error" in event.lower() or "invalid" in event.lower() for event in events)
    assert has_error, "Agent should handle invalid actions gracefully"


@pytest.mark.asyncio
async def test_salary_viewer_handles_missing_otp():
    """Test that agent handles verify action without OTP code"""
    agent = SalaryViewerAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [],
        "thread_id": "test-thread-4",
        "run_id": "test-run-4",
        "user_action": {
            "name": "verify_otp",
            "surfaceId": "otp_form",
            "sourceComponentId": "verify_button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {}  # No code provided
        }
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should send error message
    has_error = any("error" in event.lower() or "invalid" in event.lower() for event in events)
    assert has_error, "Agent should handle missing OTP code"
```

**Run Command**:
```bash
cd backend
pytest tests/test_salary_viewer_action.py -v
```

---

### Phase 5: Verify OTP Tool Has Action Button

**File**: `backend/tools/a2ui_tools.py`

Check if the `OTPInputTool.generate_component()` method includes an action on the Button component.

**Search for**:
```python
class OTPInputTool:
    def generate_component(self, ...):
        # ...
        button_component = {
            "type": "Button",
            # ...
            "action": {...}  # Check if this exists
        }
```

**If action is missing**, add it:

```python
def generate_component(
    self,
    title: str = "Enter Verification Code",
    description: str = "Please enter the code sent to your device",
    max_length: int = 6,
    pattern_type: str = "numeric",
    groups: List[int] = None,
    button_text: str = "Verify",
    action_name: str = "verify_otp"  # New parameter
) -> Dict[str, Any]:
    """Generate OTP input component with Button action"""
    
    component_id = f"otp_{uuid.uuid4().hex[:8]}"
    
    # ... existing code ...
    
    # Button with action
    button = {
        "type": "Button",
        "id": f"{component_id}_button",
        "text": button_text,
        "variant": "primary",
        "action": {
            "name": action_name,
            "context": {
                "code": {
                    "path": f"/{component_id}/code"  # Path to OTP in data model
                }
            }
        }
    }
    
    # ... rest of code ...
```

---

## Summary of Changes

### Files to Modify

1. **`backend/agents/salary_viewer_agent.py`**
   - Update `run()` method to check for `user_action` instead of `user_input`
   - Add `_echo_otp_message()` method
   - Update verification flow logic

2. **`backend/tools/a2ui_tools.py`** (if needed)
   - Verify Button component has `action` property
   - Add if missing

3. **`backend/agents/agent_registry.py`** (if needed)
   - Ensure salary-viewer has "a2ui" feature

### Files to Create

4. **`backend/tests/manual_test_salary_viewer_action.py`**
   - Manual test for complete flow

5. **`backend/tests/test_salary_viewer_action.py`**
   - Integration tests for user action handling

---

## Testing Checklist

- [ ] Manual test runs successfully
- [ ] Integration tests pass
- [ ] OTP component is generated on initial request
- [ ] User action is received when Verify button clicked
- [ ] Agent echoes OTP code in chat
- [ ] Agent reveals salary information after OTP
- [ ] Error handling for invalid actions
- [ ] Error handling for missing OTP code

---

## Implementation Order

1. **Check OTP Tool Action** - Verify Button has action property
2. **Update Salary Viewer Agent** - Add user action handling
3. **Create Tests** - Manual and integration tests
4. **Run Tests** - Verify all tests pass
5. **Update Documentation** - Update knowledge base

---

## Expected Behavior

### Flow 1: Initial Request
```
User: "I'm the CEO, what's my salary increase?"
Agent: "This is confidential. Please enter the OTP sent to your device."
       [OTP Input Component with Verify button]
```

### Flow 2: User Action (Verify Button)
```
User: [Enters "123456" and clicks Verify]
Agent: "📩 You entered OTP: **123456**"
       "✅ Verification successful!"
       "💰 Original Salary: 5,000,000 VND"
       "📈 Increase: 5%"
       "✨ New Salary: 5,250,000 VND"
```

---

## Success Criteria

✅ User can request salary information  
✅ Agent generates OTP component with Verify button  
✅ User can click Verify button  
✅ Backend receives user action via `/agents/salary-viewer/action`  
✅ Agent echoes OTP code in chat  
✅ Agent reveals salary information  
✅ All tests pass  

---

## Notes

- This implementation follows the A2UI v0.9 protocol for client-to-server `userAction` messages
- The same pattern can be extended to other agents that need user action handling
- Consider adding this pattern to the knowledge base for future reference

---

## References

- [A2UI v0.9 Protocol Specification](https://a2ui.org/specification/v0.9-a2ui/)
- [025-handling-events-for-components-plan.md](025-handling-events-for-components-plan.md)
- [024-salary-viewer-agent-plan.md](024-salary-viewer-agent-plan.md)
