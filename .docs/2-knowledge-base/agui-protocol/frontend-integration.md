# Frontend SSE Integration Fix

## Problem
The frontend was experiencing AG-UI SSE connection errors because:
1. It was trying to connect to `/api/agent/stream` endpoint using `EventSource` (GET)
2. The backend only provides `/api/chat` endpoint (POST) that streams SSE responses
3. `EventSource` API only supports GET requests, incompatible with POST-based streaming

## Additional Issue: Second Chat Failure
After initial implementation, the second chat would fail because:
1. Event handlers were registered in a `useEffect` with `threadId` as dependency
2. The AGUIClient is a singleton that persists across re-renders
3. Every time threadId changed, old handlers would unsubscribe but new ones would stack up
4. Stale closures caused handlers to reference old state values
5. `addMessage` and `updateMessage` were being recreated on each thread change

## Solution Architecture

### Key Changes

#### 1. API Client (`services/api.ts`)
**Before**: Separate REST endpoint for sending messages
**After**: Streaming fetch-based approach

```typescript
export async function sendChatMessage(
  messages: Message[],
  threadId: string,
  runId: string,
  onEvent: (event: any) => void
): Promise<void>
```

**Features**:
- Uses `fetch` with `Accept: text/event-stream` header
- Processes streaming response using ReadableStream
- Parses SSE format (lines starting with `data:`)
- Calls `onEvent` callback for each parsed event
- Sends full message history to maintain conversation context

#### 2. AG-UI Client (`services/agui-client.ts`)
**Before**: Used `EventSource` to establish persistent SSE connection
**After**: Event processor without connection management

**Key Methods**:
- `processEvent(aguiEvent: AGUIEvent)`: Process incoming events from stream
- `setConnected(connected, error)`: Update connection state
- `on(eventType, callback)`: Register event listeners (returns unsubscribe function)

**Removed**:
- `connect(endpoint)`: No longer auto-connects
- `disconnect()`: No persistent connection to close
- EventSource instance management

#### 3. useAGUI Hook (`hooks/useAGUI.ts`)
**Before**: Auto-connected when threadId changed
**After**: Provides client access without auto-connection

```typescript
export function useAGUI() {
  return {
    isConnected,
    on,              // Register event listeners
    getClient,       // Get AG-UI client instance
    setConnectionState, // Update connection state
  };
}
```

**Removed**: Thread-based auto-connection logic

#### 4. ChatContainer (`components/ChatContainer.tsx`)
**Before**: Separate message sending and event listening
**After**: Integrated message sending with event streaming

**Flow**:
1. User sends message → `handleSendMessage`
2. Create user message and add to UI
3. Build full message history (including new message)
4. Call `sendChatMessage` with event callback
5. Events flow through AG-UI client → listeners → UI updates

```typescript
await sendChatMessage(
  apiMessages,
  threadId,
  runId,
  (event) => {
    // Process each event through the AGUI client
    client.processEvent(event);
  }
);
```

## Data Flow

```
User Input
    ↓
ChatContainer.handleSendMessage
    ↓
api.sendChatMessage (POST /api/chat with streaming)
    ↓
Backend streams SSE events
    ↓
Parse SSE format in sendChatMessage
    ↓
onEvent callback → client.processEvent
    ↓
AGUI event listeners (RUN_STARTED, TEXT_MESSAGE_CHUNK, etc.)
    ↓
UI updates (streaming message display)
```

## Backend API Contract

### Endpoint: `POST /api/chat`

**Request**:
```typescript
{
  thread_id: string,
  run_id: string,
  messages: Array<{
    role: string,
    content: string
  }>
}
```

**Response**: SSE stream with AG-UI events
```
data: {"type": "RUN_STARTED", "thread_id": "...", "run_id": "..."}

data: {"type": "TEXT_MESSAGE_CHUNK", "data": {"content": "Hello"}, ...}

data: {"type": "RUN_FINISHED", "thread_id": "...", "run_id": "..."}
```

## Key Benefits

1. **Aligned with Backend**: Uses actual backend endpoint structure
2. **Standards Compliant**: Proper SSE format parsing
3. **Full Context**: Sends entire message history for proper agent context
4. **Error Handling**: Graceful error handling with user feedback
5. **Type Safety**: Strong TypeScript types throughout
6. **Cleaner Architecture**: Single request handles both message delivery and response streaming
7. **Stable Event Handlers**: Event listeners registered once, not re-created per thread
8. **No Stale Closures**: Uses refs for mutable state to avoid closure issues

## Critical Implementation Details

### Event Handler Registration
Event handlers MUST be registered only once in a useEffect without `threadId` dependency:
```typescript
// ❌ WRONG - Re-registers handlers every thread change
useEffect(() => {
  const unsubscribe = on('TEXT_MESSAGE_CONTENT', handler);
  return unsubscribe;
}, [threadId, on]); // threadId causes re-registration!

// ✅ CORRECT - Registers once, uses ref for threadId
const threadIdRef = useRef(threadId);
useEffect(() => {
  threadIdRef.current = threadId;
}, [threadId]);

useEffect(() => {
  const unsubscribe = on('TEXT_MESSAGE_CONTENT', (event) => {
    const currentThreadId = threadIdRef.current; // Access current value
    // handler logic
  });
  return unsubscribe;
}, [on]); // No threadId!
```

### Stable Callbacks in useMessages
`addMessage` and `updateMessage` must be stable (not recreated):
```typescript
// Use empty dependency array and capture threadId via closure
const addMessage = useCallback((message: Message) => {
  setMessages(prev => [...prev, message]);
  const currentThreadId = threadId; // Closure captures current value
  if (currentThreadId) {
    StorageService.addMessage(currentThreadId, message);
  }
}, []); // Empty deps = stable function
```

### Using Refs for Mutable State
Current message being streamed must use ref, not state:
```typescript
// ❌ WRONG - State triggers re-renders and dependency changes
const [currentMessage, setCurrentMessage] = useState(null);

// ✅ CORRECT - Ref is mutable without triggering effects
const currentMessageRef = useRef(null);
currentMessageRef.current = updatedMessage; // Direct mutation
```

## Testing Checklist

- [ ] Backend server running on port 8000
- [ ] Send first message creates thread
- [ ] Agent response streams in real-time
- [ ] **Multiple messages maintain context** ← Critical for second chat
- [ ] **Second and third messages work correctly** ← Was broken before
- [ ] Error states display properly
- [ ] Connection indicators work correctly
- [ ] Event handlers don't stack up (check AGUIClient listener count in console)
