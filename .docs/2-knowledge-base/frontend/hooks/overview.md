# React Hooks Guide

## useChatThreads

**Location**: `hooks/useChatThreads.ts`

**Purpose**: Manages chat thread state and operations.

### API

```typescript
const {
  threads,           // All chat threads
  currentThread,     // Currently selected thread
  currentThreadId,   // ID of current thread
  isLoading,         // Loading state
  createThread,      // Create new thread
  deleteThread,      // Delete a thread
  selectThread,      // Select a thread
  updateThreadTitle, // Update thread title
  refreshThreads,    // Refresh from storage
} = useChatThreads();
```

### Methods

#### `createThread()`
Creates a new thread and selects it automatically.

**Returns**: `Thread`

**Example**:
```typescript
const newThread = createThread();
// Thread is automatically selected
```

#### `deleteThread(threadId: string)`
Deletes a thread by ID. If the deleted thread is currently selected, clears the selection.

**Example**:
```typescript
deleteThread('thread-123');
```

#### `selectThread(threadId: string)`
Selects a thread by ID.

**Example**:
```typescript
selectThread('thread-456');
```

#### `updateThreadTitle(threadId: string, title: string)`
Updates the title of a thread.

**Example**:
```typescript
updateThreadTitle('thread-789', 'New conversation about AI');
```

#### `refreshThreads()`
Refreshes thread list from LocalStorage (useful after external changes).

---

## useMessages

**Location**: `hooks/useMessages.ts`

**Purpose**: Manages message state for a specific thread.

### API

```typescript
const {
  messages,       // All messages in thread
  isLoading,      // Loading state
  addMessage,     // Add new message
  updateMessage,  // Update existing message
  clearMessages,  // Clear all messages
  scrollToBottom, // Scroll to bottom
  scrollRef,      // Ref for scroll container
} = useMessages(threadId);
```

### Methods

#### `addMessage(message: Message)`
Adds a new message to the thread and saves to storage.

**Example**:
```typescript
addMessage({
  id: 'msg-123',
  threadId: 'thread-456',
  role: 'user',
  content: 'Hello, agent!',
  timestamp: Date.now(),
});
```

#### `updateMessage(messageId: string, updates: Partial<Message>)`
Updates an existing message (useful for streaming).

**Example**:
```typescript
updateMessage('msg-123', { 
  content: 'Updated content',
  isStreaming: false 
});
```

#### `clearMessages()`
Clears all messages for the current thread (local state only).

#### `scrollToBottom()`
Scrolls to the bottom of the message list.

### Scroll Behavior

The hook provides a `scrollRef` that should be attached to the scrollable container:

```typescript
<div ref={scrollRef}>
  {messages.map(msg => <MessageBubble message={msg} />)}
</div>
```

Auto-scroll is triggered when new messages are added.

---

## useAGUI

**Location**: `hooks/useAGUI.ts`

**Purpose**: Integrates with AG-UI event stream from backend.

### API

```typescript
const {
  isConnected,   // Connection status
  currentEvent,  // Latest event received
  error,         // Connection error (if any)
  on,            // Register event listener
  disconnect,    // Disconnect from stream
} = useAGUI(threadId);
```

### Methods

#### `on(eventType: string, callback: (event: AGUIEvent) => void)`
Registers an event listener for a specific AG-UI event type.

**Returns**: Cleanup function

**Example**:
```typescript
useEffect(() => {
  const cleanup = on('TEXT_MESSAGE_CHUNK', (event) => {
    console.log('New chunk:', event.data.content);
  });
  
  return cleanup; // Cleanup on unmount
}, [on]);
```

#### `disconnect()`
Manually disconnects from the AG-UI stream.

### Event Types

- `RUN_STARTED`: Agent run begins
- `TEXT_MESSAGE_CHUNK`: Streaming message chunk
- `RUN_FINISHED`: Agent run completes
- `THINKING`: Agent is thinking/processing
- `EXECUTING`: Agent is executing action
- `COMPLETE`: Action completed
- `ERROR`: Error occurred
- `*`: Catch-all for any event

### Connection Management

The hook automatically:
- Connects when threadId changes
- Disconnects when threadId becomes null
- Reconnects on errors (via AGUIClient)
- Cleans up on unmount

### Example: Handling Streaming Messages

```typescript
const { on, isConnected } = useAGUI(threadId);
const [streamingContent, setStreamingContent] = useState('');

useEffect(() => {
  if (!isConnected) return;

  // Handle chunks
  const unsubscribeChunk = on('TEXT_MESSAGE_CHUNK', (event) => {
    setStreamingContent(prev => prev + event.data.content);
  });

  // Handle completion
  const unsubscribeFinish = on('RUN_FINISHED', (event) => {
    console.log('Stream finished');
    setStreamingContent('');
  });

  return () => {
    unsubscribeChunk();
    unsubscribeFinish();
  };
}, [on, isConnected]);
```

---

## useAgentSelection

⚠️ **DEPRECATED**: This hook has been migrated to `AgentSelectionContext` for proper state sharing.

**Migration**: Use `useAgentSelection` from `@/contexts/AgentSelectionContext` instead.

**Why Changed**: Multiple components using this hook created separate state instances, causing bugs where the UI showed one agent but sent API requests with a different agent.

**See**: [State Management Guide](../state-management.md) for details on the Context migration.

---

## Hook Composition Pattern

These hooks are designed to work together:

```typescript
function ChatPage() {
  // Thread management
  const { 
    threads, 
    currentThreadId, 
    createThread 
  } = useChatThreads();

  // Message management for current thread
  const { 
    messages, 
    addMessage, 
    updateMessage 
  } = useMessages(currentThreadId);

  // AG-UI integration for current thread
  const { 
    isConnected, 
    on 
  } = useAGUI(currentThreadId);

  // Handle events
  useEffect(() => {
    const cleanup = on('TEXT_MESSAGE_CHUNK', (event) => {
      // Update message with new chunk
      updateMessage(currentMessageId, {
        content: currentContent + event.data.content
      });
    });
    
    return cleanup;
  }, [on, updateMessage]);

  // ... rest of component
}
```

---

## Best Practices

1. **Cleanup**: Always return cleanup functions from `useEffect` when using event listeners
2. **Dependencies**: Include all hook dependencies in `useEffect` dependency arrays
3. **Null Checks**: Handle null threadId cases (e.g., no thread selected)
4. **Error Handling**: Monitor `error` states from hooks
5. **Performance**: Use `useCallback` for event handlers passed to hooks
6. **Testing**: Mock hooks in component tests for isolation
