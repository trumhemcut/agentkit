# Database Persistence Layer

## Overview

The frontend integrates with the backend database persistence layer to store threads and messages on the server. This implementation follows a **Phase 1 approach**: LocalStorage remains the primary data source, while data is synced to the server in the background for persistence.

## Architecture

### Phase 1: Write-Only Background Sync

In Phase 1, the frontend:
- **Reads** from LocalStorage (existing behavior)
- **Writes** to both LocalStorage AND server (background sync)
- Does not block UI if server sync fails
- Accepts temporary duplicates (will be resolved in Phase 2)

### Data Flow

```
User Action → LocalStorage (immediate) → UI Update
    ↓
Background Sync → Server API (non-blocking)
```

## Implementation

### 1. TypeScript Types (`/types/database.ts`)

Database-specific types for API communication:

```typescript
interface Thread {
  id: string;
  title: string;
  agent_id: string;    // "chat" | "canvas" | "salary_viewer"
  model: string;
  provider: string;
  created_at: string;
  updated_at: string;
}

interface Message {
  id: string;
  thread_id: string;
  role: "user" | "assistant";
  content: string | null;
  artifact_data: Record<string, any> | null;
  metadata: Record<string, any> | null;
  created_at: string;
}
```

### 2. API Client (`/services/api.ts`)

#### Thread API

**Create Thread**:
```typescript
await threadsApi.create({
  agent_id: 'chat',
  model: 'qwen:7b',
  provider: 'ollama',
  title: 'New Chat',
});
```

**Request:**
```http
POST /api/threads
Content-Type: application/json

{
  "agent_id": "chat",
  "model": "qwen:7b",
  "provider": "ollama",
  "title": "New Chat"
}
```

**List Threads**:
```typescript
const { threads } = await threadsApi.list(50, 0);
```

**Get Thread**:
```typescript
const thread = await threadsApi.get('thread-id');
```

**Update Thread**:
```typescript
await threadsApi.update('thread-id', { title: 'Updated Title' });
```

**Delete Thread**:
```typescript
await threadsApi.delete('thread-id');
```

#### Message API

**Create Message**:
```typescript
await messagesApi.create('thread-id', {
  role: 'user',
  content: 'Hello, world!',
  artifact_data: { type: 'code', language: 'python' },
  metadata: { timestamp: Date.now() },
});
```

**List Messages**:
```typescript
const { messages } = await messagesApi.list('thread-id');
```

**Delete Message**:
```typescript
await messagesApi.delete('message-id');
```

### 3. Storage Service with Background Sync (`/services/storage.ts`)

Enhanced `StorageService` class with background sync methods:

#### Sync Thread to Server

```typescript
StorageService.syncThreadToServer(
  thread,
  'chat',      // agentId
  'qwen:7b',   // model
  'ollama'     // provider
);
```

- Non-blocking operation
- Logs success/failure without throwing errors
- Does not affect UI if sync fails

#### Sync Message to Server

```typescript
StorageService.syncMessageToServer(threadId, message);
```

- Converts frontend message format to backend format
- Maps `role: 'agent'` to `role: 'assistant'`
- Extracts artifact data and metadata
- Non-blocking operation

#### Sync Thread Title

```typescript
StorageService.syncThreadTitleToServer(threadId, 'New Title');
```

#### Sync Thread Deletion

```typescript
StorageService.syncThreadDeleteToServer(threadId);
```

### 4. Hooks with Background Sync

#### useChatThreads Hook

Updated to accept agent/model/provider parameters:

```typescript
const {
  threads,
  currentThread,
  createThread,
  deleteThread,
  updateThreadTitle,
} = useChatThreads(
  initialThreadId,
  'chat',      // agentId
  'qwen:7b',   // model
  'ollama'     // provider
);
```

**Enhanced Methods**:

- `createThread()`: Creates locally + syncs to server
- `deleteThread()`: Deletes locally + syncs deletion to server
- `updateThreadTitle()`: Updates locally + syncs title to server

#### useMessages Hook

No parameter changes required:

```typescript
const { messages, addMessage } = useMessages(threadId);
```

**Enhanced Methods**:

- `addMessage()`: Adds to LocalStorage + syncs to server

## Testing

### Test Coverage

All API client methods are tested with mocked fetch:

```bash
npm test -- tests/services/api-database.test.ts
```

**Test Results**: 15/15 tests passing ✅

### Test Categories

1. **Thread API Tests**:
   - Create, list, get, update, delete operations
   - Error handling
   - Pagination

2. **Message API Tests**:
   - Create (text and artifact messages)
   - List messages
   - Delete messages
   - Error handling

## Error Handling

### Non-Blocking Sync

All sync operations are wrapped in try-catch blocks:

```typescript
try {
  await threadsApi.create(data);
  console.log('✅ Thread synced to server');
} catch (error) {
  console.error('⚠️ Failed to sync (non-blocking):', error);
  // Don't throw - UI continues normally
}
```

### User Experience

- **Success**: Background sync happens silently
- **Failure**: Error logged to console, UI unaffected
- **Offline**: Sync fails gracefully, data remains in LocalStorage

## Usage Examples

### Creating a New Thread

```typescript
// In a component
const { createThread } = useChatThreads(
  undefined,
  'chat',
  'qwen:7b',
  'ollama'
);

// User clicks "New Chat"
const newThread = createThread();
// → Saved to LocalStorage immediately
// → Synced to server in background
```

### Adding a Message

```typescript
const { addMessage } = useMessages(threadId);

// User sends a message
addMessage({
  id: crypto.randomUUID(),
  threadId,
  role: 'user',
  content: 'Hello!',
  timestamp: Date.now(),
});
// → Added to LocalStorage immediately
// → Synced to server in background
```

### Updating Thread Title

```typescript
const { updateThreadTitle } = useChatThreads();

// User renames thread
updateThreadTitle(threadId, 'My Important Chat');
// → Updated in LocalStorage immediately
// → Synced to server in background
```

## API Endpoints

### Backend Endpoints Used

- `POST /api/threads` - Create thread
- `GET /api/threads` - List threads
- `GET /api/threads/{id}` - Get thread
- `PATCH /api/threads/{id}` - Update thread
- `DELETE /api/threads/{id}` - Delete thread
- `POST /api/threads/{id}/messages` - Create message
- `GET /api/threads/{id}/messages` - List messages
- `DELETE /api/messages/{id}` - Delete message

### Request/Response Formats

See [types/database.ts](../../types/database.ts) for complete type definitions.

## Future: Phase 2

Phase 2 will implement:

1. **Read from Server**: Fetch threads/messages from server on load
2. **Conflict Resolution**: Handle LocalStorage vs Server discrepancies
3. **Offline Sync**: Queue operations when offline, sync on reconnect
4. **LocalStorage as Cache**: Transition to server as source of truth

### Migration Path

```
Phase 1 (Current):
  LocalStorage → Primary Source
  Server → Backup/Persistence

Phase 2 (Future):
  Server → Primary Source
  LocalStorage → Cache
```

## Configuration

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Default Values

- Agent Type: `'chat'`
- Model: `'qwen:7b'`
- Provider: `'ollama'`

## Troubleshooting

### Messages Not Syncing

Check browser console for sync errors:

```
✅ Message synced to server: message-123
⚠️ Failed to sync message to server (non-blocking): Network error
```

### Backend Connection Issues

If backend is not running:
- Frontend continues to work with LocalStorage
- Sync operations fail silently
- Check `NEXT_PUBLIC_API_URL` environment variable

### Testing Sync

Monitor network tab in browser DevTools:
- Look for POST/PATCH/DELETE requests to `/api/threads` and `/api/messages`
- Check request payload and response status

## Related Documentation

- [Backend Database Layer](../../../backend/DATABASE.md)
- [API Implementation Plan](../../../.docs/1-implementation-plans/030-database-persistence-layer-plan.md)
- [Storage Service](./storage-service.md)
- [API Client](./api-client.md)
