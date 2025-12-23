# AG-UI Integration Guide

## Overview

AG-UI (Agent UI Protocol) is a standardized protocol for real-time communication between frontend applications and LangGraph agent backends using Server-Sent Events (SSE).

## Architecture

```
┌─────────────┐         SSE Stream          ┌──────────────┐
│             │ ────────────────────────────▶│              │
│  Frontend   │                              │   Backend    │
│  (AG-UI     │◀─────────────────────────────│  (LangGraph  │
│   Client)   │   AG-UI Protocol Events      │   Agents)    │
└─────────────┘                              └──────────────┘
```

## AG-UI Client

**Location**: `services/agui-client.ts`

### Class: AGUIClient

Singleton client for managing SSE connections to backend agents.

#### Methods

##### `connect(endpoint: string): void`
Establishes SSE connection to the specified endpoint.

**Example**:
```typescript
const client = getAGUIClient();
client.connect('http://localhost:8000/api/agent/stream?threadId=123');
```

##### `disconnect(): void`
Closes the SSE connection.

##### `on(eventType: string, callback: (event: AGUIEvent) => void): void`
Registers an event listener.

**Example**:
```typescript
client.on('TEXT_MESSAGE_CHUNK', (event) => {
  console.log('Chunk received:', event.data.content);
});
```

##### `off(eventType: string, callback: (event: AGUIEvent) => void): void`
Removes an event listener.

##### `isConnected(): boolean`
Returns current connection status.

##### `getConnectionState(): ConnectionState`
Returns detailed connection state including error information.

---

## Event Types

### RUN_STARTED

**Description**: Agent run begins processing.

**Event Data**:
```typescript
{
  type: 'RUN_STARTED',
  data: {
    runId: string;
    agentName?: string;
  },
  timestamp: number
}
```

**Usage**:
```typescript
on('RUN_STARTED', (event) => {
  console.log(`Agent ${event.agentName} started`);
  // Show "Agent is thinking..." indicator
});
```

---

### TEXT_MESSAGE_CHUNK

**Description**: Streaming text chunk from agent.

**Event Data**:
```typescript
{
  type: 'TEXT_MESSAGE_CHUNK',
  data: {
    content: string;
    isComplete?: boolean;
  },
  timestamp: number,
  agentName?: string
}
```

**Usage**:
```typescript
on('TEXT_MESSAGE_CHUNK', (event) => {
  // Append chunk to current message
  currentContent += event.data.content;
  updateMessage(messageId, { content: currentContent });
});
```

---

### RUN_FINISHED

**Description**: Agent run completes successfully.

**Event Data**:
```typescript
{
  type: 'RUN_FINISHED',
  data: {
    runId: string;
    message?: string;
  },
  timestamp: number
}
```

**Usage**:
```typescript
on('RUN_FINISHED', (event) => {
  console.log('Agent finished');
  // Mark message as complete
  updateMessage(messageId, { isStreaming: false });
});
```

---

### THINKING

**Description**: Agent is processing/thinking.

**Event Data**:
```typescript
{
  type: 'THINKING',
  data: {
    message: string;
  },
  timestamp: number
}
```

---

### EXECUTING

**Description**: Agent is executing an action/tool.

**Event Data**:
```typescript
{
  type: 'EXECUTING',
  data: {
    action: string;
    tool?: string;
  },
  timestamp: number
}
```

---

### ERROR

**Description**: Error occurred during agent run.

**Event Data**:
```typescript
{
  type: 'ERROR',
  data: {
    message: string;
    code?: string;
  },
  timestamp: number
}
```

**Usage**:
```typescript
on('ERROR', (event) => {
  console.error('Agent error:', event.data.message);
  // Display error to user
  showError(event.data.message);
});
```

---

## Integration Pattern

### Complete Example

```typescript
import { useEffect, useState } from 'react';
import { useAGUI } from '@/hooks/useAGUI';
import { Message } from '@/types/chat';

function ChatComponent({ threadId }: { threadId: string }) {
  const { isConnected, on, error } = useAGUI(threadId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentAgentMessage, setCurrentAgentMessage] = useState<Message | null>(null);

  useEffect(() => {
    if (!isConnected) return;

    // Handle run start
    const unsubStart = on('RUN_STARTED', (event) => {
      console.log('Agent started:', event.agentName);
    });

    // Handle streaming chunks
    const unsubChunk = on('TEXT_MESSAGE_CHUNK', (event) => {
      const chunk = event.data.content;
      
      if (!currentAgentMessage) {
        // Create new message
        const newMsg: Message = {
          id: `msg-${Date.now()}`,
          threadId,
          role: 'agent',
          content: chunk,
          timestamp: Date.now(),
          agentName: event.agentName,
          isStreaming: true,
        };
        setCurrentAgentMessage(newMsg);
        setMessages(prev => [...prev, newMsg]);
      } else {
        // Update existing message
        const updated = {
          ...currentAgentMessage,
          content: currentAgentMessage.content + chunk,
        };
        setCurrentAgentMessage(updated);
        setMessages(prev => 
          prev.map(m => m.id === updated.id ? updated : m)
        );
      }
    });

    // Handle completion
    const unsubFinish = on('RUN_FINISHED', (event) => {
      if (currentAgentMessage) {
        setMessages(prev =>
          prev.map(m => 
            m.id === currentAgentMessage.id 
              ? { ...m, isStreaming: false }
              : m
          )
        );
        setCurrentAgentMessage(null);
      }
    });

    // Handle errors
    const unsubError = on('ERROR', (event) => {
      console.error('Error:', event.data.message);
      setCurrentAgentMessage(null);
    });

    // Cleanup
    return () => {
      unsubStart();
      unsubChunk();
      unsubFinish();
      unsubError();
    };
  }, [isConnected, on, currentAgentMessage, threadId]);

  // Render messages
  return (
    <div>
      {messages.map(msg => (
        <div key={msg.id}>{msg.content}</div>
      ))}
      {error && <div>Error: {error}</div>}
    </div>
  );
}
```

---

## Backend API Contract

### Endpoint: GET /api/agent/stream

**Query Parameters**:
- `threadId` (required): Thread ID for the conversation

**Response**: Server-Sent Events stream

**Event Format**:
```
event: message
data: {"type":"TEXT_MESSAGE_CHUNK","data":{"content":"Hello"},"timestamp":1234567890}

event: message
data: {"type":"RUN_FINISHED","data":{},"timestamp":1234567891}
```

### Endpoint: POST /api/chat/message

**Request Body**:
```json
{
  "message": "User message content",
  "threadId": "thread-123"
}
```

**Response**:
```json
{
  "success": true,
  "messageId": "msg-456"
}
```

---

## Error Handling

### Connection Errors

The AG-UI client automatically handles connection errors:

```typescript
const { error, isConnected } = useAGUI(threadId);

if (error) {
  // Display error to user
  return <div>Connection error: {error}</div>;
}

if (!isConnected) {
  // Show connecting state
  return <div>Connecting to agent...</div>;
}
```

### Reconnection

The client attempts to reconnect automatically when the connection is lost. Monitor `isConnected` state for status updates.

---

## Best Practices

1. **Event Listener Cleanup**: Always unsubscribe from events on component unmount
2. **Null Checks**: Handle cases where threadId is null
3. **State Management**: Use local state for streaming messages, then persist on completion
4. **Error Display**: Show user-friendly error messages
5. **Loading States**: Display loading indicators during connection/processing
6. **Message Batching**: Consider batching small chunks for better performance
7. **Timeout Handling**: Implement timeout logic for long-running operations

---

## Debugging

### Enable Debug Logging

Add debug logging to the AG-UI client:

```typescript
client.on('*', (event) => {
  console.log('[AG-UI Event]', event.type, event.data);
});
```

### Monitor Connection State

```typescript
const state = client.getConnectionState();
console.log('Connection state:', state);
```

### Test Events

Manually trigger events for testing:

```typescript
// In development, you can manually emit events
const testEvent: AGUIEvent = {
  type: 'TEXT_MESSAGE_CHUNK',
  data: { content: 'Test chunk' },
  timestamp: Date.now(),
};
// Process event manually for testing UI behavior
```
