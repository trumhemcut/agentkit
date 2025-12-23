# Services Layer Documentation

## Overview

The services layer provides abstraction for external integrations and data persistence:

- **StorageService**: LocalStorage operations for chat threads
- **AGUIClient**: Server-Sent Events client for AG-UI protocol
- **API Client**: REST API communication with backend

---

## StorageService

**Location**: `services/storage.ts`

### Purpose

Manages chat thread and message persistence using browser LocalStorage.

### API

#### Static Methods

##### `getThreads(): Thread[]`
Retrieves all threads from localStorage.

**Returns**: Array of Thread objects

**Example**:
```typescript
const threads = StorageService.getThreads();
console.log(`Found ${threads.length} threads`);
```

##### `getThread(threadId: string): Thread | null`
Retrieves a specific thread by ID.

**Returns**: Thread object or null if not found

**Example**:
```typescript
const thread = StorageService.getThread('thread-123');
if (thread) {
  console.log('Thread found:', thread.title);
}
```

##### `saveThread(thread: Thread): void`
Saves a thread (creates or updates).

**Example**:
```typescript
const newThread: Thread = {
  id: 'thread-123',
  title: 'New conversation',
  messages: [],
  createdAt: Date.now(),
  updatedAt: Date.now(),
};
StorageService.saveThread(newThread);
```

##### `deleteThread(threadId: string): void`
Deletes a thread by ID.

**Example**:
```typescript
StorageService.deleteThread('thread-123');
```

##### `addMessage(threadId: string, message: Message): void`
Adds a message to a thread.

**Example**:
```typescript
const message: Message = {
  id: 'msg-456',
  threadId: 'thread-123',
  role: 'user',
  content: 'Hello!',
  timestamp: Date.now(),
};
StorageService.addMessage('thread-123', message);
```

##### `updateMessage(threadId: string, messageId: string, updates: Partial<Message>): void`
Updates a message in a thread.

**Example**:
```typescript
StorageService.updateMessage('thread-123', 'msg-456', {
  content: 'Updated content',
  isStreaming: false,
});
```

##### `clearAll(): void`
Clears all threads (useful for testing).

**Example**:
```typescript
StorageService.clearAll();
```

### Storage Key

Data is stored under the key: `agentkit_threads`

### Data Format

```json
[
  {
    "id": "thread-123",
    "title": "Conversation about AI",
    "messages": [
      {
        "id": "msg-456",
        "threadId": "thread-123",
        "role": "user",
        "content": "Hello!",
        "timestamp": 1234567890
      }
    ],
    "createdAt": 1234567890,
    "updatedAt": 1234567895
  }
]
```

### Error Handling

All methods include try-catch blocks and log errors to console. Operations fail silently to prevent app crashes.

---

## AGUIClient

**Location**: `services/agui-client.ts`

### Purpose

Manages Server-Sent Events (SSE) connection to backend for AG-UI protocol.

### Class: AGUIClient

#### Constructor

Creates a new AG-UI client instance (typically used as singleton).

#### Instance Methods

##### `connect(endpoint: string): void`
Establishes SSE connection.

**Parameters**:
- `endpoint`: SSE endpoint URL

**Example**:
```typescript
const client = new AGUIClient();
client.connect('http://localhost:8000/api/agent/stream?threadId=123');
```

##### `disconnect(): void`
Closes the SSE connection and cleans up resources.

##### `on(eventType: string, callback: (event: AGUIEvent) => void): void`
Registers an event listener.

**Parameters**:
- `eventType`: Event type to listen for (or '*' for all events)
- `callback`: Function to call when event is received

**Example**:
```typescript
client.on('TEXT_MESSAGE_CHUNK', (event) => {
  console.log('Chunk:', event.data.content);
});
```

##### `off(eventType: string, callback: (event: AGUIEvent) => void): void`
Removes an event listener.

##### `isConnected(): boolean`
Returns current connection status.

##### `getConnectionState(): ConnectionState`
Returns detailed connection state.

**Returns**:
```typescript
{
  isConnected: boolean;
  error: string | null;
  lastEventTime: number | null;
}
```

### Singleton Pattern

Use the `getAGUIClient()` function to get the singleton instance:

```typescript
import { getAGUIClient } from '@/services/agui-client';

const client = getAGUIClient();
client.connect(endpoint);
```

### Event Handling

The client emits these internal events:
- `connection`: Connection established
- `error`: Connection error
- `*`: All AG-UI protocol events

### Automatic Reconnection

The EventSource API handles reconnection automatically. Monitor connection state to detect issues.

---

## API Client

**Location**: `services/api.ts`

### Purpose

Provides typed functions for backend REST API calls.

### Functions

#### `sendChatMessage(request: SendMessageRequest): Promise<SendMessageResponse>`

Sends a user message to the backend.

**Request**:
```typescript
interface SendMessageRequest {
  message: string;
  threadId: string;
}
```

**Response**:
```typescript
interface SendMessageResponse {
  success: boolean;
  messageId: string;
  error?: string;
}
```

**Example**:
```typescript
const response = await sendChatMessage({
  message: 'Hello, agent!',
  threadId: 'thread-123',
});

if (response.success) {
  console.log('Message sent:', response.messageId);
} else {
  console.error('Error:', response.error);
}
```

#### `getAgentStatus(agentId: string): Promise<AgentStatusResponse | null>`

Gets the status of an agent.

**Response**:
```typescript
interface AgentStatusResponse {
  agentId: string;
  status: string;
  lastUpdate: number;
}
```

**Example**:
```typescript
const status = await getAgentStatus('agent-456');
if (status) {
  console.log('Agent status:', status.status);
}
```

#### `getAGUIEndpoint(threadId: string): string`

Constructs the AG-UI SSE endpoint URL.

**Returns**: Full endpoint URL

**Example**:
```typescript
const endpoint = getAGUIEndpoint('thread-123');
// Returns: 'http://localhost:8000/api/agent/stream?threadId=thread-123'
```

### Configuration

Set the API base URL via environment variable:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Default: `http://localhost:8000`

### Error Handling

All API functions include error handling and return error information in the response. Never throws exceptions.

---

## Best Practices

### StorageService

1. **Data Validation**: Validate data before saving
2. **Size Limits**: Monitor localStorage size (typically 5-10MB limit)
3. **Serialization**: Ensure data is JSON-serializable
4. **Browser Compatibility**: Check localStorage availability
5. **Backup**: Consider syncing to backend for persistence

### AGUIClient

1. **Connection Management**: Always disconnect on component unmount
2. **Event Cleanup**: Remove event listeners when no longer needed
3. **Error Recovery**: Monitor connection state and handle errors
4. **Memory Leaks**: Avoid registering duplicate listeners
5. **Testing**: Mock AGUIClient for component tests

### API Client

1. **Error Handling**: Always check response.success before proceeding
2. **Loading States**: Show loading indicators during API calls
3. **Retry Logic**: Implement retry for failed requests
4. **Timeout**: Set appropriate request timeouts
5. **Type Safety**: Use TypeScript interfaces for all requests/responses

---

## Testing

### Mock StorageService

```typescript
// Mock localStorage
const mockStorage: { [key: string]: string } = {};
global.localStorage = {
  getItem: (key) => mockStorage[key] || null,
  setItem: (key, value) => { mockStorage[key] = value; },
  removeItem: (key) => { delete mockStorage[key]; },
  clear: () => { Object.keys(mockStorage).forEach(k => delete mockStorage[k]); },
  length: 0,
  key: () => null,
};
```

### Mock AGUIClient

```typescript
const mockAGUIClient = {
  connect: jest.fn(),
  disconnect: jest.fn(),
  on: jest.fn(),
  off: jest.fn(),
  isConnected: jest.fn(() => true),
  getConnectionState: jest.fn(() => ({
    isConnected: true,
    error: null,
    lastEventTime: Date.now(),
  })),
};
```

### Mock API Client

```typescript
jest.mock('@/services/api', () => ({
  sendChatMessage: jest.fn(() => Promise.resolve({
    success: true,
    messageId: 'msg-123',
  })),
  getAgentStatus: jest.fn(() => Promise.resolve({
    agentId: 'agent-1',
    status: 'active',
    lastUpdate: Date.now(),
  })),
  getAGUIEndpoint: jest.fn((threadId) => 
    `http://localhost:8000/api/agent/stream?threadId=${threadId}`
  ),
}));
```
