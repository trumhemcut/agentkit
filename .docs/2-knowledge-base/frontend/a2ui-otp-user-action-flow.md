# A2UI OTP User Action Flow - Frontend Implementation

**Status**: Implemented  
**Date**: January 1, 2026  
**Related**: Implementation Plan 026 - Improve Salary Viewer Agent with User Action Handling

## Overview

The frontend has been updated to support the bidirectional A2UI protocol for handling user actions from interactive components like OTP input forms. This enables agents to receive user input when buttons are clicked on A2UI surfaces.

## Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│              Frontend User Action Flow                              │
└─────────────────────────────────────────────────────────────────────┘

1. User enters OTP in A2UIOTPInput component
   ↓
2. User clicks "Verify" button
   ↓
3. A2UIOTPInput.handleSubmit() called
   ↓
4. a2uiManager.handleComponentAction() invoked
   - Resolves context paths from data model
   - Creates UserAction object
   ↓
5. a2uiManager triggers registered callback
   ↓
6. AgentMessageBubble's handleUserAction() receives action
   ↓
7. A2UIUserActionService.sendAction() sends POST to backend
   - Endpoint: /api/agents/{agentId}/action
   - Includes: userAction, threadId, runId, model, provider
   ↓
8. Backend processes action and streams response via SSE
   ↓
9. Frontend processes SSE events through AGUI client
   ↓
10. Agent's response appears in chat (e.g., "You entered OTP: 123456")
```

## Key Components Modified

### 1. A2UIOTPInput Component

**File**: `frontend/components/A2UI/components/A2UIOTPInput.tsx`

**Changes**:
- Added import for `a2uiManager`
- Added `buttonAction` prop to component interface
- Updated `handleSubmit()` to use `a2uiManager.handleComponentAction()` instead of legacy `onAction` callback
- Maintains backward compatibility with legacy pattern

**Key Code**:
```typescript
const handleSubmit = () => {
  // New A2UI v0.9 pattern: use buttonAction from props
  if (props.buttonAction) {
    a2uiManager.handleComponentAction(
      surfaceId,
      id,
      props.buttonAction.name,
      props.buttonAction.context || {}
    )
  } 
  // Legacy support
  else if (onAction) {
    onAction("otp_submit", { ... })
  }
}
```

### 2. AgentMessageBubble Component

**File**: `frontend/components/AgentMessageBubble.tsx`

**Changes**:
- Updated to use `message.agentId` if available, falling back to prop or default
- Ensures correct agent ID is sent when processing user actions
- This allows Salary Viewer agent to receive actions at `/api/agents/salary-viewer/action`

**Key Code**:
```typescript
const effectiveAgentId = message.agentId || agentId || 'a2ui-loop';

const handleUserAction = async (action: UserAction) => {
  await A2UIUserActionService.sendAction(
    effectiveAgentId,  // Uses message.agentId if available
    action,
    threadId,
    runId,
    (event) => { ... }
  );
};

// Register for all surfaces in this message
currentSurfaces.forEach(surface => {
  a2uiManager.onAction(surface.id, handleUserAction);
});
```

## Component Action Structure

### Backend OTP Component Definition

The backend's `OTPInputTool` should generate a component with this structure:

```python
{
  "type": "OTPInput",
  "id": "otp_verification_component",
  "props": {
    "title": { "literalString": "Enter Verification Code" },
    "description": { "literalString": "Please enter the OTP sent to your device" },
    "maxLength": 6,
    "patternType": "digits",
    "buttonText": { "literalString": "Verify" },
    "buttonAction": {
      "name": "verify_otp",
      "context": {
        "code": { "path": "/otp_verification/code" }
      }
    },
    "value": { "path": "/otp_verification/code" }
  }
}
```

**Key Fields**:
- `buttonAction.name`: Action identifier sent to backend (e.g., "verify_otp")
- `buttonAction.context.code.path`: JSON Pointer to OTP value in data model
- Frontend resolves path and sends actual value in `userAction.context`

## Data Flow

### Step-by-Step Execution

1. **Agent generates OTP component**:
   ```json
   {
     "type": "surfaceUpdate",
     "surfaceId": "salary_viewer_surface",
     "components": [
       {
         "id": "otp_component",
         "component": { "OTPInput": { ... } }
       }
     ]
   }
   ```

2. **User enters OTP "123456" and clicks Verify**

3. **Frontend resolves context**:
   - Reads value from `/otp_verification/code` in data model
   - Value: "123456"

4. **Frontend sends UserAction**:
   ```json
   {
     "userAction": {
       "name": "verify_otp",
       "surfaceId": "salary_viewer_surface",
       "sourceComponentId": "otp_component",
       "timestamp": "2026-01-01T10:00:00Z",
       "context": {
         "code": "123456"  // Resolved from path
       }
     },
     "threadId": "thread-abc",
     "runId": "run-123",
     "model": "qwen:7b",
     "provider": "ollama"
   }
   ```

5. **Backend receives action at `/api/agents/salary-viewer/action`**

6. **Salary Viewer Agent processes**:
   - Extracts OTP: `action_context.get("code")`
   - Echoes OTP: "You entered OTP: 123456"
   - Reveals salary information

7. **Frontend displays agent's response in chat**

## Testing Instructions

### Manual Test Flow

1. **Start backend and frontend servers**:
   ```bash
   # Terminal 1: Backend
   cd backend
   python -m uvicorn main:app --reload
   
   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

2. **Navigate to chat interface**: http://localhost:3000

3. **Select Salary Viewer agent** from agent selector

4. **Send message**: "I'm the CEO, what's my salary increase?"

5. **Expected behavior**:
   - Agent responds with confirmation message
   - OTP input component appears with 6 digit boxes
   - "Verify" button shown below

6. **Enter OTP**: Type any 6 digits (e.g., "123456")

7. **Click "Verify" button**

8. **Expected behavior**:
   - Request sent to `/api/agents/salary-viewer/action`
   - Agent echoes OTP: "📩 Bạn đã nhập mã OTP: **123456**"
   - Agent reveals salary: "💰 Original Salary: 5,000,000 VND..."

### Browser Console Verification

Check console logs to verify the flow:

```
[A2UIOTPInput] Submit button clicked
[A2UIManager] handleComponentAction called
[AgentMessageBubble] User action triggered: verify_otp
[A2UIUserAction] Sending action: salary-viewer
[A2UIUserAction] Response status: 200
[A2UIUserAction] Received event: TEXT_MESSAGE_START
[A2UIUserAction] Received event: TEXT_MESSAGE_CONTENT
[ChatContainer] Text message content chunk
```

### Network Tab Verification

1. Open DevTools → Network tab
2. Filter: "action"
3. Click "Verify" button
4. Verify POST request to `/api/agents/salary-viewer/action`
5. Check request payload contains `userAction` with correct structure
6. Check response is SSE stream with agent messages

## Backend Integration Points

### Required Backend Implementation

For the frontend to work correctly, the backend must:

1. **Accept user actions at `/api/agents/{agent_id}/action` endpoint**
   - Defined in `backend/api/routes.py`
   - Already implemented

2. **Set agentId in TEXT_MESSAGE_START metadata** (CRITICAL):
   ```python
   start_event = TextMessageStartEvent(
       type=EventType.TEXT_MESSAGE_START,
       message_id=message_id,
       role="assistant",
       metadata={
           "message_type": "text",
           "agentId": "salary-viewer",    # Frontend uses this!
           "agentName": "Salary Viewer"    # Display name
       }
   )
   ```
   **Why this is critical**: The frontend's `AgentMessageBubble` reads `message.agentId` from this metadata to determine which endpoint to send user actions to. Without this, actions go to the wrong agent!

3. **Agent handles `user_action` in state**:
   ```python
   async def run(self, state: AgentState):
       user_action = state.get("user_action")
       if user_action:
           action_name = user_action.get("name")
           action_context = user_action.get("context", {})
           otp_code = action_context.get("code", "")
           # Process OTP...
   ```

4. **OTP tool includes buttonAction in component**:
   ```python
   "buttonAction": {
       "name": "verify_otp",
       "context": {
           "code": { "path": "/otp_verification/code" }
       }
   }
   ```

## Troubleshooting

### Issue: Button click does nothing

**Check**:
1. Console shows "No action defined for OTP submit button"
2. Component doesn't have `buttonAction` prop
3. Backend OTP tool not generating action in button component

**Solution**: Update backend `OTPInputTool.generate_component()` to include `buttonAction`

### Issue: Wrong agent receives action

**Check**:
1. Console shows action sent to wrong agent ID
2. Message doesn't have `agentId` field set

**Solution**: Ensure backend sets `agentId` in message metadata when streaming

### Issue: Context not resolved

**Check**:
1. Console shows path not resolved
2. Data model doesn't have value at path

**Solution**: Verify OTP input updates data model correctly with `updateDataModel()`

## Related Files

- `frontend/components/A2UI/components/A2UIOTPInput.tsx` - OTP input component
- `frontend/components/AgentMessageBubble.tsx` - Message bubble with action handling
- `frontend/lib/a2ui/A2UIManager.ts` - Central action manager
- `frontend/services/a2uiActionService.ts` - Action service for API calls
- `frontend/types/a2ui.ts` - Type definitions

## Future Enhancements

1. **Action Cleanup**: Add cleanup method in `a2uiManager` to unregister callbacks
2. **Error Handling**: Better error UI when actions fail
3. **Loading States**: Show loading indicator on button during action processing
4. **Action History**: Track action history for debugging
5. **Action Validation**: Validate action structure before sending

## References

- [A2UI v0.9 Protocol Specification](https://a2ui.org/specification/v0.9-a2ui/)
- [Implementation Plan 026](../../1-implementation-plans/026-improve-salary-viewer-agent-plan.md)
- [User Action Protocol Plan](../../1-implementation-plans/025-handling-events-for-components-plan.md)
