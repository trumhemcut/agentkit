# A2UI User Actions - Frontend Implementation

**Implementation Date**: December 30, 2025  
**Plan**: [025-handling-events-for-components-plan.md](../../1-implementation-plans/025-handling-events-for-components-plan.md)  
**Status**: ✅ Complete (Frontend Phase 3)

## Overview

Implemented **bidirectional communication** for A2UI protocol in the frontend, enabling user interactions (button clicks, form submissions, checkbox toggles) to be sent back to agents for processing. This completes the client-to-server flow defined in the A2UI v0.9 specification.

## What Was Built

### 1. User Action Service
**File**: `frontend/services/a2uiActionService.ts`

- `A2UIUserActionService` class with static methods
- `sendAction()` - Sends user actions to backend via POST `/api/agents/{agentId}/action`
- Processes SSE stream responses from backend
- `createUserAction()` - Creates properly formatted UserAction objects per A2UI v0.9 spec

**Key Features**:
- Async SSE streaming response handling
- AbortController support for cancellation
- Event callback for processing AG-UI events from action responses

### 2. Updated Types
**File**: `frontend/types/a2ui.ts`

Added A2UI v0.9 compliant types:
```typescript
interface UserAction {
  name: string;                  // Action name from component
  surfaceId: string;            // Surface where action occurred
  sourceComponentId: string;    // Component that triggered action
  timestamp: string;            // ISO 8601 timestamp
  context: Record<string, any>; // Resolved context data
}

interface UserActionRequest {
  userAction: UserAction;
  threadId: string;
  runId: string;
}
```

### 3. Enhanced A2UIStore
**File**: `frontend/stores/a2uiStore.ts`

Added path-based value operations for two-way binding:
- `getValueAtPath(surfaceId, path)` - Get value from data model using JSON Pointer
- `setValueAtPath(surfaceId, path, value)` - Set value in data model (for input components)

### 4. A2UIManager Integration
**File**: `frontend/lib/a2ui/A2UIManager.ts`

Already had all necessary methods:
- `handleComponentAction()` - Called by components when user interacts
- `resolveActionContext()` - Resolves path references to actual values
- `updateDataModelValue()` - Updates local data model for two-way binding
- `onAction()` - Registers callbacks for when actions occur

### 5. Updated A2UI Components
**Files**: 
- `frontend/components/A2UI/components/A2UIButton.tsx`
- `frontend/components/A2UI/components/A2UICheckbox.tsx`
- `frontend/components/A2UI/components/A2UIInput.tsx`
- `frontend/components/A2UI/components/A2UITextInput.tsx`

**A2UIButton**:
- Supports both new `action` prop (A2UI v0.9) and legacy `onClick` prop
- Calls `a2uiManager.handleComponentAction()` on click
- Action context resolved from data model before sending

**A2UICheckbox**:
- Two-way binding via `setValueAtPath()`
- Optional `onChange` action support
- Updates data model immediately on check/uncheck

**A2UIInput & A2UITextInput**:
- Two-way binding via `setValueAtPath()`
- Updates data model on every keystroke
- No action needed for typing - actions are for form submission

### 6. Chat Interface Integration
**Files**:
- `frontend/components/AgentMessageBubble.tsx`
- `frontend/components/ChatContainer.tsx`
- `frontend/components/MessageHistory.tsx`
- `frontend/components/MessageBubble.tsx`

**AgentMessageBubble**:
- Registers action handler with `a2uiManager` for each message's surfaces
- When action occurs, sends to backend via `A2UIUserActionService.sendAction()`
- Processes SSE stream responses through parent `onActionEvent` callback

**ChatContainer**:
- Added `handleA2UIActionEvent()` callback
- Processes A2UI action events through same AGUI client as chat messages
- Passes callback down through message components

**Flow**:
```
User clicks Button in A2UI
  → Component calls a2uiManager.handleComponentAction()
  → Manager resolves context and creates UserAction
  → Manager calls registered callback (from AgentMessageBubble)
  → AgentMessageBubble sends to backend via API
  → Backend streams back AG-UI events + A2UI updates
  → Events processed through ChatContainer's AGUI client
  → UI updates rendered
```

### 7. Tests
**File**: `frontend/tests/a2ui/userActions.test.ts`

Comprehensive unit tests covering:
- Context resolution from data model paths
- Action callback triggering
- Wildcard action handlers
- UserAction object creation
- Two-way binding data model updates
- Nested path handling

## A2UI v0.9 Protocol Compliance

### Client-to-Server Messages

✅ **UserAction Message Structure**:
```json
{
  "userAction": {
    "name": "submit_form",
    "surfaceId": "contact_form_1",
    "sourceComponentId": "submit_button",
    "timestamp": "2025-12-30T10:30:00Z",
    "context": {
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
}
```

✅ **Two-Way Binding Pattern**:
1. Input components (TextField, CheckBox) update client-side data model immediately
2. Updates are local only (no automatic network requests)
3. Button with action resolves paths from data model
4. UserAction sent to server with resolved values
5. Agent processes and sends back UI updates

## Example Usage

### Button with Action
```typescript
// Backend sends this component:
{
  id: "submit_button",
  component: {
    Button: {
      label: { literalString: "Submit" },
      action: {
        name: "submit_form",
        context: {
          email: { path: "/user/email" },
          name: { path: "/user/name" }
        }
      }
    }
  }
}

// User clicks button:
// 1. Frontend resolves paths: { email: "user@example.com", name: "John Doe" }
// 2. Sends UserAction to POST /api/agents/a2ui-loop/action
// 3. Backend validates and processes
// 4. Backend sends back success/error UI updates
```

### TextField Two-Way Binding
```typescript
// TextField bound to /user/email
// User types → data model updates immediately
// No action triggered until Button is clicked
```

## Architecture Patterns

### Action Handler Registration
```typescript
// In AgentMessageBubble useEffect:
const handleUserAction = async (action: UserAction) => {
  const runId = `run-${Date.now()}`;
  await A2UIUserActionService.sendAction(
    agentId,
    action,
    threadId,
    runId,
    (event) => onActionEvent(event)
  );
};

a2uiManager.onAction(surfaceId, handleUserAction);
```

### Context Resolution
```typescript
// Component definition has paths:
action: {
  name: "book_restaurant",
  context: {
    restaurantName: "The Gourmet",  // Literal value
    partySize: { path: "/booking/partySize" },  // From data model
    time: { path: "/booking/time" }
  }
}

// Manager resolves before sending:
a2uiManager.resolveActionContext(surfaceId, action.context)
// Returns: { restaurantName: "The Gourmet", partySize: "4", time: "7:00 PM" }
```

## Testing

Run tests:
```bash
cd frontend
npm test -- tests/a2ui/userActions.test.ts
```

## Integration Points

### With Backend
- Backend endpoint: `POST /api/agents/{agentId}/action`
- Backend must implement `UserActionRequest` handler
- Backend streams back AG-UI events + A2UI messages
- See backend implementation in [025-handling-events-for-components-plan.md](../../1-implementation-plans/025-handling-events-for-components-plan.md)

### With Existing Chat
- Integrated into ChatContainer's event processing flow
- Uses same AGUI client for action responses
- A2UI updates processed through existing `processA2UIMessage()`

## Next Steps

### Phase 1: Backend Implementation (Pending)
- Implement `POST /agents/{agent_id}/action` endpoint
- Add `UserAction` types to backend
- Update `a2ui_agent_with_loop.py` to handle user actions
- Update `a2ui_loop_graph.py` with action routing

### Phase 2: Testing & Validation
- E2E tests with real backend
- Test form submission flow
- Test validation and error handling
- Test multiple action types

### Phase 3: Extension to Other Agents
- Extend to Canvas agent
- Extend to Salary Viewer agent
- Update all A2UI-enabled agents

## Key Files Modified

Frontend (Phase 3 - ✅ Complete):
- ✅ `frontend/types/a2ui.ts` - UserAction types
- ✅ `frontend/services/a2uiActionService.ts` - Action service
- ✅ `frontend/stores/a2uiStore.ts` - Path operations
- ✅ `frontend/lib/a2ui/A2UIManager.ts` - Already had methods
- ✅ `frontend/components/A2UI/components/A2UIButton.tsx` - Action handling
- ✅ `frontend/components/A2UI/components/A2UICheckbox.tsx` - Two-way binding
- ✅ `frontend/components/A2UI/components/A2UIInput.tsx` - Two-way binding
- ✅ `frontend/components/A2UI/components/A2UITextInput.tsx` - Two-way binding
- ✅ `frontend/components/AgentMessageBubble.tsx` - Action registration
- ✅ `frontend/components/ChatContainer.tsx` - Event handling
- ✅ `frontend/components/MessageHistory.tsx` - Pass through callbacks
- ✅ `frontend/components/MessageBubble.tsx` - Pass through callbacks
- ✅ `frontend/tests/a2ui/userActions.test.ts` - Unit tests

Backend (Phase 1 - ⏳ Pending):
- ⏳ `backend/protocols/a2ui_types.py` - UserAction models
- ⏳ `backend/api/routes.py` - Action endpoint
- ⏳ `backend/api/models.py` - UserActionRequest
- ⏳ `backend/agents/base_agent.py` - AgentState update
- ⏳ `backend/agents/a2ui_agent_with_loop.py` - Action handler
- ⏳ `backend/graphs/a2ui_loop_graph.py` - Action routing

## References

- [A2UI v0.9 Specification - Client-to-Server Messages](https://a2ui.org/specification/v0.9-a2ui/#client-to-server-messages)
- [Implementation Plan](../../1-implementation-plans/025-handling-events-for-components-plan.md)
- [Backend Agent Guide](../../../.github/agents/backend.agent.md)
- [Frontend AG-UI Guide](../../../.github/agents/frontend.agent.md)
