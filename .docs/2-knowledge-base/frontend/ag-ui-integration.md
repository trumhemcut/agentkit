# AG-UI Integration in Frontend

## Overview

The frontend is now properly integrated with the AG-UI protocol for real-time agent communication. The AG-UI (Agent User Interaction) protocol is a lightweight, event-driven protocol that bridges AI agents and front-end applications.

## Architecture

### Backend → Frontend Flow

```
Backend (Python)          Frontend (TypeScript)
─────────────────        ──────────────────────
ag-ui-protocol     →     Custom AG-UI Client
   ↓                            ↓
FastAPI SSE        →     Fetch API + SSE
   ↓                            ↓
Event Stream       →     Event Handlers
   ↓                            ↓
EventEncoder       →     JSON Parsing
   ↓                            ↓
AG-UI Events       →     React Components
```

## AG-UI Protocol Implementation

### Event Types

The following AG-UI events are supported:

#### Run Lifecycle Events
- **`RUN_STARTED`** - Emitted when agent run begins
- **`RUN_FINISHED`** - Emitted when agent run completes successfully
- **`RUN_ERROR`** - Emitted when agent run encounters an error

#### Text Message Events
- **`TEXT_MESSAGE_START`** - Emitted when agent starts generating a message
- **`TEXT_MESSAGE_CONTENT`** - Emitted for each text chunk (streaming)
- **`TEXT_MESSAGE_END`** - Emitted when message generation is complete

#### Tool Call Events (Future)
- **`TOOL_CALL_START`** - When agent starts calling a tool
- **`TOOL_CALL_ARGS`** - Tool arguments being parsed
- **`TOOL_CALL_END`** - Tool call completed
- **`TOOL_CALL_RESULT`** - Tool execution result

### Key Files

#### 1. `/frontend/types/agui.ts`
Defines TypeScript types matching the AG-UI protocol:
- `EventType` enum - All supported event types
- Event interfaces (`RunStartedEvent`, `TextMessageContentEvent`, etc.)
- `ConnectionState` interface
- Union type `AGUIEvent` for all events

#### 2. `/frontend/services/agui-client.ts`
Custom AG-UI client implementation:
- **Purpose**: Process and distribute AG-UI events from backend
- **Pattern**: Event emitter with typed listeners
- **Singleton**: Single instance shared across app
- **Methods**:
  - `processEvent(event)` - Process incoming events from API
  - `on(eventType, callback)` - Register event listener
  - `off(eventType, callback)` - Remove event listener
  - `setConnected(connected, error?)` - Update connection state
  - `getConnectionState()` - Get current connection state

#### 3. `/frontend/services/api.ts`
Handles HTTP communication and SSE parsing:
- `sendChatMessage()` - POST to `/api/chat` with SSE streaming
- Parses SSE format: `data: <json>\n\n`
- Forwards parsed events to AG-UI client

#### 4. `/frontend/hooks/useAGUI.ts`
React hook for AG-UI integration:
- Provides access to singleton AG-UI client
- Manages connection state
- Exposes `on()` method for component event subscriptions

#### 5. `/frontend/components/ChatContainer.tsx`
Main UI component that consumes AG-UI events:
- Registers listeners for all AG-UI event types
- Creates/updates message UI based on events
- Handles streaming text with `TEXT_MESSAGE_CONTENT`
- Shows pending/streaming states

## How It Works

### 1. User Sends Message

```typescript
// ChatContainer.tsx
const handleSendMessage = async (content: string) => {
  // Add user message
  addMessage(userMessage);
  
  // Add pending agent message
  addMessage(pendingMessage);
  
  // Send to backend and process events
  await sendChatMessage(apiMessages, threadId, runId, (event) => {
    client.processEvent(event);
  });
};
```

### 2. Backend Streams Events

```python
# backend/api/routes.py
async def event_generator():
    # Start run
    yield encoder.encode(RunStartedEvent(...))
    
    # Stream agent response
    async for event in chat_agent.run(state):
        yield encoder.encode(event)
    
    # Finish run
    yield encoder.encode(RunFinishedEvent(...))
```

### 3. Frontend Receives & Processes

```typescript
// services/api.ts
for await (const line of lines) {
  if (line.startsWith('data: ')) {
    const event = JSON.parse(data);
    onEvent(event); // → client.processEvent(event)
  }
}
```

### 4. React Components React

```typescript
// ChatContainer.tsx
useEffect(() => {
  // Listen for TEXT_MESSAGE_CONTENT
  const unsubscribe = on(EventType.TEXT_MESSAGE_CONTENT, (event) => {
    // Update message with new chunk
    updateMessage(currentMsg.id, { 
      content: currentMsg.content + event.delta 
    });
  });
  
  return unsubscribe;
}, []);
```

## AG-UI Client Implementation

### Current Implementation
The frontend uses a **custom AG-UI client implementation** that is fully compatible with the official AG-UI protocol used by the backend.

**Why Custom Implementation?**
- ✅ The official `@ag-ui/client` npm packages are not yet published
- ✅ Custom implementation provides full control and is lightweight
- ✅ Fully compatible with backend `ag-ui-protocol` Python package
- ✅ No external dependencies required
- ✅ Properly typed with TypeScript

**Features:**
- Event-driven architecture with typed event handlers
- Singleton pattern for app-wide event distribution
- Connection state management
- Support for all AG-UI protocol event types
- Detailed console logging for debugging

### Future Migration to Official SDK
When the official SDK becomes available on npm:
1. Install packages: `npm install @ag-ui/client @ag-ui/core rxjs`
2. Replace custom `AGUIClient` with official client
3. Update event handling to use Observables (if applicable)
4. Test thoroughly to ensure compatibility

## Benefits of AG-UI

1. **Real-time Streaming**: See agent responses as they're generated
2. **Event-Driven**: Reactive UI updates based on agent events
3. **Standardized Protocol**: Backend and frontend speak same language
4. **Extensible**: Easy to add new event types (tool calls, etc.)
5. **Decoupled**: Agent logic independent of UI implementation

## Testing AG-UI Integration

### 1. Check Console Logs
Look for AG-UI event logs:
```
[API] Sending chat request: { threadId, runId, messageCount }
[API] Received AG-UI event: RUN_STARTED
[API] Received AG-UI event: TEXT_MESSAGE_START
[API] Received AG-UI event: TEXT_MESSAGE_CONTENT
[AGUI] Processing event: TEXT_MESSAGE_CONTENT
[ChatContainer] Text message content chunk
[API] Stream completed
```

### 2. Verify Event Flow
1. Open browser DevTools console
2. Send a message
3. Watch for events in this order:
   - `RUN_STARTED`
   - `TEXT_MESSAGE_START`
   - Multiple `TEXT_MESSAGE_CONTENT` (streaming)
   - `TEXT_MESSAGE_END`
   - `RUN_FINISHED`

### 3. Test Error Handling
- Backend not running → `ERROR` event with connection error
- Backend error → `RUN_ERROR` event with error message

## Common Issues

### Events Not Received
**Symptom**: No events in console, no agent response
**Check**:
1. Backend running? `cd backend && uvicorn main:app --reload`
2. CORS configured? Check backend `main.py`
3. Correct API URL? Check `NEXT_PUBLIC_API_URL`

### Events Received but Not Processed
**Symptom**: Events in API logs but not in AGUI logs
**Check**:
1. Event format matches types in `types/agui.ts`
2. AG-UI client receiving events: Look for `[AGUI] Processing event`
3. Event listeners registered: Look for `[AGUI] Registered listener`

### Events Processed but UI Not Updating
**Symptom**: Events in AGUI logs but message not appearing
**Check**:
1. `currentAgentMessageRef` is set in `TEXT_MESSAGE_START`
2. `updateMessage` is being called in `TEXT_MESSAGE_CONTENT`
3. React state is updating (check React DevTools)

### Agent Stuck on "Thinking..." State
**Symptom**: Agent message shows "Thinking..." spinner indefinitely even after `RUN_FINISHED` event
**Root Cause**: The pending/streaming message with empty content is not being cleared when run finishes
**Fix Applied**:
1. Added `removeMessage` function to `useMessages` hook
2. In `RUN_FINISHED` handler, check if `currentAgentMessageRef` has empty content
3. If empty, remove the message entirely; otherwise mark as complete
4. This applies to both `ChatContainer` and `CanvasChatContainer`

**Implementation**:
```typescript
const unsubscribeFinish = on(EventType.RUN_FINISHED, (event) => {
  const currentMsg = currentAgentMessageRef.current;
  if (currentMsg) {
    if (currentMsg.content.trim() === '') {
      removeMessage(currentMsg.id); // Remove empty placeholder
    } else {
      updateMessage(currentMsg.id, { isPending: false, isStreaming: false });
    }
    currentAgentMessageRef.current = null;
  }
  setIsSending(false);
});
```

## Future Enhancements

1. **Tool Call Visualization**: Display when agent uses tools
2. **Thinking States**: Show agent reasoning process
3. **Multi-Agent Support**: Handle multiple agents in conversation
4. **Progress Indicators**: Show progress for long-running tasks
5. **Human-in-the-Loop**: Allow user feedback during agent execution

## References

- [AG-UI Documentation](https://docs.ag-ui.com)
- [AG-UI Protocol GitHub](https://github.com/ag-ui-protocol)
- Backend implementation: [backend/protocols/](../backend/protocols/)
- Python package: `ag-ui-protocol`
