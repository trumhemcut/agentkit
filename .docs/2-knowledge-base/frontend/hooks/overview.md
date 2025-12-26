# React Hooks Guide

> **Note**: As of December 26, 2025, agent and model selection have been migrated to **Zustand stores**. See [State Management Guide](../state-management.md) for details.

## Active Hooks

### useAutoScroll

**Location**: `hooks/useAutoScroll.ts`

**Purpose**: Manages intelligent auto-scroll behavior for chat messages.

**Features**:
- Auto-scrolls when user is near bottom and new messages arrive
- Preserves scroll position when user manually scrolls up
- Skips auto-scroll on initial thread history load
- Configurable scroll threshold (default: 100px from bottom)

### API

```typescript
const {
  scrollRef,        // Ref to attach to scrollable container
  handleScroll,     // Scroll event handler
  scrollToBottom,   // Function to manually scroll to bottom
  shouldAutoScroll, // Whether auto-scroll is enabled
  isNearBottom,     // Function to check if near bottom
} = useAutoScroll([messages], { 
  isInitialLoad: false,
  scrollThreshold: 100 
});
```

**See**: [useAutoScroll.md](./useAutoScroll.md) for detailed documentation.

---

### useChatThreads

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

**Purpose**: Manages message state for a specific thread. Integrates with `useAutoScroll` for intelligent scroll behavior.

### API

```typescript
const {
  messages,         // All messages in thread
  isLoading,        // Loading state
  addMessage,       // Add new message
  updateMessage,    // Update existing message
  removeMessage,    // Remove a message
  clearMessages,    // Clear all messages
  scrollToBottom,   // Scroll to bottom (from useAutoScroll)
  scrollRef,        // Ref for scroll container (from useAutoScroll)
  handleScroll,     // Scroll event handler (from useAutoScroll)
  shouldAutoScroll, // Whether auto-scroll is enabled (from useAutoScroll)
} = useMessages(threadId, { onArtifactDetected });
```

### Auto-Scroll Integration

The hook automatically integrates `useAutoScroll` to provide:
- Auto-scroll when new messages arrive (user or agent)
- Preserved scroll position when user scrolls up
- No auto-scroll on initial thread load or thread switching

**Implementation**:
```typescript
// Inside useMessages
const [isInitialLoad, setIsInitialLoad] = useState(true);

const { scrollRef, handleScroll, scrollToBottom } = useAutoScroll(
  [messages],
  { isInitialLoad }
);

// When thread changes, mark as initial load
useEffect(() => {
  if (!threadId) return;
  
  setIsInitialLoad(true);
  // Load messages...
  
  setTimeout(() => setIsInitialLoad(false), 100);
}, [threadId]);
```

### Methods

#### `addMessage(message: Message)`
Adds a new message to the thread and saves to storage. Auto-scroll will trigger if user is near bottom.

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
Updates an existing message (useful for streaming). Auto-scroll will trigger during streaming if user is near bottom.

**Example**:
```typescript
updateMessage('msg-123', { 
  content: 'Updated content',
  isStreaming: false 
});
```

#### `removeMessage(messageId: string)`
Removes a message from the thread and storage.

**Example**:
```typescript
removeMessage('msg-123');
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

⚠️ **DEPRECATED - MIGRATED TO ZUSTAND**: This hook has been replaced by Zustand stores for better performance and simpler state management.

**Old Location**: `hooks/useAgentSelection.ts`  
**New Location**: `stores/agentStore.ts`

**Migration**: Use `useAgentStore` from `@/stores/agentStore` instead.

```typescript
// ❌ OLD - React Hook (Deprecated)
import { useAgentSelection } from '@/hooks/useAgentSelection';
const { selectedAgent, availableAgents, setSelectedAgent, loading } = useAgentSelection();

// ✅ NEW - Zustand Store
import { useAgentStore, initializeAgentStore } from '@/stores/agentStore';

useEffect(() => {
  initializeAgentStore(); // Initialize on mount
}, []);

const selectedAgent = useAgentStore((state) => state.selectedAgent);
const availableAgents = useAgentStore((state) => state.availableAgents);
const setSelectedAgent = useAgentStore((state) => state.setSelectedAgent);
const loading = useAgentStore((state) => state.loading);
```

**Why Changed**: 
- **Performance**: Zustand provides selective re-renders - components only update when subscribed state changes
- **Simplicity**: No Provider wrappers needed, stores are global singletons
- **Consistency**: Multiple components accessing the hook created separate state instances, causing sync issues

**See**: [State Management Guide](../state-management.md) for full Zustand documentation.

---

## useModelSelection

⚠️ **DEPRECATED - MIGRATED TO ZUSTAND**: This hook has been replaced by Zustand stores for better performance and simpler state management.

**Old Location**: `hooks/useModelSelection.ts`  
**New Location**: `stores/modelStore.ts`

**Migration**: Use `useModelStore` from `@/stores/modelStore` instead.

```typescript
// ❌ OLD - React Hook (Deprecated)
import { useModelSelection } from '@/hooks/useModelSelection';
const { selectedModel, models, selectModel, loading } = useModelSelection();

// ✅ NEW - Zustand Store
import { useModelStore, initializeModelStore } from '@/stores/modelStore';

useEffect(() => {
  initializeModelStore(); // Initialize on mount
}, []);

const selectedModel = useModelStore((state) => state.selectedModel);
const availableModels = useModelStore((state) => state.availableModels);
const setSelectedModel = useModelStore((state) => state.setSelectedModel);
const loading = useModelStore((state) => state.loading);
```

**Benefits**:
- **Better Performance**: Selective subscriptions prevent unnecessary re-renders
- **Persistence**: Built-in localStorage sync with persist middleware
- **Type Safety**: Excellent TypeScript inference
- **DevEx**: Less boilerplate, cleaner API

**See**: [State Management Guide](../state-management.md) for full Zustand documentation.

---

## Hook Composition Pattern

These hooks are designed to work together. Here's how to compose active hooks with Zustand stores:

```typescript
function ChatPage() {
  // Thread management (Hook)
  const { 
    threads, 
    currentThreadId, 
    createThread 
  } = useChatThreads();

  // Message management for current thread (Hook)
  const { 
    messages, 
    addMessage, 
    updateMessage 
  } = useMessages(currentThreadId);

  // AG-UI integration for current thread (Hook)
  const { 
    isConnected, 
    on 
  } = useAGUI(currentThreadId);

  // Agent selection (Zustand Store)
  const selectedAgent = useAgentStore((state) => state.selectedAgent);
  
  // Model selection (Zustand Store)
  const selectedModel = useModelStore((state) => state.selectedModel);

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

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              Application State                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  Zustand Stores (Global)                        │
│  ├─ agentStore     - Agent selection            │
│  └─ modelStore     - Model selection            │
│                                                  │
│  React Hooks (Component-scoped)                 │
│  ├─ useChatThreads - Thread management          │
│  ├─ useMessages    - Message operations         │
│  └─ useAGUI        - AG-UI event handling       │
│                                                  │
└─────────────────────────────────────────────────┘
```

**When to use Zustand Stores**:
- Global state that needs to be accessed by many components
- State that should persist across page reloads (localStorage)
- State that changes frequently (benefits from selective subscriptions)
- Examples: user preferences, selections, configuration

**When to use React Hooks**:
- Component-specific or thread-specific state
- State that doesn't need global access
- Complex async operations with local state
- Examples: messages, threads, event listeners

---

## Best Practices

### For React Hooks
1. **Cleanup**: Always return cleanup functions from `useEffect` when using event listeners
2. **Dependencies**: Include all hook dependencies in `useEffect` dependency arrays
3. **Null Checks**: Handle null threadId cases (e.g., no thread selected)
4. **Error Handling**: Monitor `error` states from hooks
5. **Performance**: Use `useCallback` for event handlers passed to hooks
6. **Testing**: Mock hooks in component tests for isolation

### For Zustand Stores
1. **Selective Subscriptions**: Only subscribe to the state you need
   ```typescript
   // ✅ Good - selective
   const selectedAgent = useAgentStore((state) => state.selectedAgent);
   
   // ❌ Bad - subscribes to everything
   const store = useAgentStore();
   ```
2. **Initialization**: Call initialization functions on mount
   ```typescript
   useEffect(() => {
     initializeAgentStore();
   }, []);
   ```
3. **Actions Outside Components**: Use `getState()` for non-React code
   ```typescript
   const currentAgent = useAgentStore.getState().selectedAgent;
   ```
4. **Type Safety**: Always use TypeScript interfaces for store state
5. **Persistence**: Only persist user selections, not derived/dynamic data

### Combined Usage
1. **Composition**: Combine hooks and stores for optimal architecture
2. **Separation of Concerns**: Use stores for global state, hooks for local/component state
3. **Performance**: Leverage Zustand's selective re-renders for frequently changing global state
4. **Consistency**: Follow the same patterns across the codebase

---

## Migration Status

| Feature | Old Implementation | New Implementation | Status |
|---------|-------------------|-------------------|---------|
| Agent Selection | `useAgentSelection` hook | `useAgentStore` Zustand store | ✅ Migrated |
| Model Selection | `useModelSelection` hook | `useModelStore` Zustand store | ✅ Migrated |
| Thread Management | `useChatThreads` hook | `useChatThreads` hook | ✅ Active |
| Message Management | `useMessages` hook | `useMessages` hook | ✅ Active |
| AG-UI Integration | `useAGUI` hook | `useAGUI` hook | ✅ Active |
| Canvas State | `CanvasContext` | `CanvasContext` | 🔄 Future migration |

---

## Related Documentation

- **[State Management Guide](../state-management.md)** - Complete Zustand documentation
- **[AG-UI Integration](../ag-ui-integration.md)** - AG-UI protocol details
- **[Component Architecture](../components/README.md)** - Component patterns

---

**Last Updated**: December 26, 2025  
**Migration to Zustand**: Completed for agent/model selection
