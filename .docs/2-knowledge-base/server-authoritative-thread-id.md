# Server-Authoritative Thread ID Generation Pattern

**Implemented**: 2026-01-04  
**Status**: ✅ Active  
**Pattern**: Server-authoritative ID with optimistic UI

---

## Problem Solved

Previously, frontend and backend generated separate thread IDs that never reconciled:
- Frontend: `crypto.randomUUID()` → saved to localStorage → ID "abc-123"
- Backend: `uuid.uuid4()` → saved to database → ID "xyz-789"
- Result: Two threads with different IDs, never synced

This broke sync operations, created orphan records, and violated idempotency.

---

## Solution: Server-Authoritative Pattern

Backend generates the authoritative ID, frontend reconciles after creation:

```typescript
// 1. Create temporary thread (optimistic UI)
const tempId = crypto.randomUUID();
const tempThread = { id: tempId, ... };
StorageService.saveThread(tempThread);
setCurrentThreadId(tempId); // User sees thread immediately

// 2. Sync to backend and get real ID
const serverThread = await threadsApi.create({...});

// 3. Replace temp ID with server ID
StorageService.deleteThread(tempId);
const finalThread = { ...tempThread, id: serverThread.id };
StorageService.saveThread(finalThread);
setCurrentThreadId(serverThread.id);
```

**Benefits:**
- ✅ Single source of truth (backend)
- ✅ No duplicate IDs
- ✅ RESTful pattern
- ✅ Idempotent operations
- ✅ Offline-tolerant (fallback to temp ID)

---

## Implementation Details

### 1. Storage Service (`frontend/services/storage.ts`)

```typescript
/**
 * Sync a thread to the server and get server-generated ID
 * Returns the server thread with authoritative ID
 * Throws error if sync fails to enable proper error handling
 */
static async syncThreadToServer(
  thread: Thread, 
  agentId: string, 
  model: string, 
  provider: string
): Promise<Thread> {  // ⚠️ Changed from Promise<void>
  const serverThread = await threadsApi.create({
    agent_id: agentId,
    model: model,
    provider: provider,
    title: thread.title,
  });
  console.log('[StorageService] ✅ Thread created on server with ID:', serverThread.id);
  return serverThread;  // ⚠️ Return server response
}
```

**Key Changes:**
- Return type: `Promise<void>` → `Promise<Thread>`
- No try/catch wrapper (let caller handle errors)
- Return server response for ID reconciliation

---

### 2. Thread Hook (`frontend/hooks/useChatThreads.ts`)

```typescript
const createThread = useCallback(async () => {  // ⚠️ Now async
  // Step 1: Create temporary thread for optimistic UI
  const tempId = crypto.randomUUID();
  const tempThread: Thread = {
    id: tempId,
    title: 'New Chat',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  StorageService.saveThread(tempThread);
  setThreads(StorageService.getThreads());
  setCurrentThreadId(tempId);  // User sees thread immediately
  
  // Step 2: Sync to server and get authoritative ID
  try {
    const serverThread = await StorageService.syncThreadToServer(
      tempThread, agentId, model, provider
    );
    
    // Step 3: Replace temp ID with server ID
    StorageService.deleteThread(tempId);
    const finalThread: Thread = {
      ...tempThread,
      id: serverThread.id,
      createdAt: new Date(serverThread.created_at).getTime(),
      updatedAt: new Date(serverThread.updated_at).getTime(),
    };
    StorageService.saveThread(finalThread);
    setThreads(StorageService.getThreads());
    setCurrentThreadId(serverThread.id);
    
    console.log('[useChatThreads] ✅ Thread created with server ID:', serverThread.id);
    return finalThread;
  } catch (error) {
    console.error('[useChatThreads] ⚠️ Failed to sync thread to server:', error);
    // Keep temp thread and show warning to user
    console.warn('[useChatThreads] Using temporary thread ID (offline mode):', tempId);
    return tempThread;
  }
}, [agentId, model, provider]);
```

**Key Changes:**
- Callback is now `async`
- Three-step process: temp → sync → reconcile
- Error handling keeps temp thread if sync fails
- Returns `Promise<Thread>` instead of synchronous `Thread`

---

### 3. Component Updates (`frontend/components/ChatApp.tsx`)

```typescript
const handleNewChat = useCallback(async () => {  // ⚠️ Now async
  isCreatingNewThreadRef.current = true;
  deactivateCanvas();
  
  const hasNoThread = !currentThread;
  const hasMessages = currentThread && currentThread.messages.length > 0;
  
  if (hasNoThread || hasMessages) {
    const newThread = await createThread();  // ⚠️ Await promise
    
    if (newThread && newThread.id) {
      window.history.pushState({}, '', `/t/${newThread.id}`);
    }
    
    requestAnimationFrame(() => {
      isCreatingNewThreadRef.current = false;
      chatContainerRef.current?.focusInput();
    });
  }
}, [currentThread, createThread, deactivateCanvas]);
```

**Key Changes:**
- Handler is now `async`
- `await createThread()` to get final thread
- URL update uses server ID

---

### 4. Home Redirect (`frontend/components/HomeRedirect.tsx`)

```typescript
useEffect(() => {
  const initializeThread = async () => {
    const threads = StorageService.getThreads();
    
    if (threads.length > 0) {
      router.replace(`/t/${threads[0].id}`);
    } else {
      try {
        const serverThread = await threadsApi.create({
          agent_id: 'chat',
          model: 'qwen:7b',
          provider: 'ollama',
          title: 'New Chat',
        });
        
        const newThread = {
          id: serverThread.id,  // ⚠️ Use server ID
          title: serverThread.title,
          messages: [],
          createdAt: new Date(serverThread.created_at).getTime(),
          updatedAt: new Date(serverThread.updated_at).getTime(),
        };
        StorageService.saveThread(newThread);
        router.replace(`/t/${serverThread.id}`);
      } catch (error) {
        console.error('Failed to create thread:', error);
        // Fallback to temp thread if server fails
        const tempThread = { id: crypto.randomUUID(), ... };
        StorageService.saveThread(tempThread);
        router.replace(`/t/${tempThread.id}`);
      }
    }
  };
  
  initializeThread();
}, [router]);
```

**Key Changes:**
- Direct backend call instead of client-side generation
- Fallback to temp ID if backend fails
- Save server thread to localStorage

---

## Backend (No Changes Required)

Backend already generates UUIDs correctly:

```python
# backend/database/models.py
class Thread(Base):
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
```

```python
# backend/services/thread_service.py
@staticmethod
async def create_thread(db: AsyncSession, agent_id: str, model: str, 
                       provider: str, title: str = None) -> Thread:
    thread = Thread(
        agent_id=agent_id,
        model=model,
        provider=provider,
        title=title or f"New {agent_id} conversation"
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return thread
```

Backend automatically generates ID and returns it in response. Frontend now uses this ID.

---

## User Experience

### Before (Broken)
```
User clicks "New Chat"
↓
Frontend: Creates thread with ID "abc-123"
↓
Shows thread immediately ✅
↓
Background: Syncs to server (ignored response)
↓
Backend: Creates thread with ID "xyz-789"
↓
Result: Two threads, never synced ❌
```

### After (Fixed)
```
User clicks "New Chat"
↓
Frontend: Creates temp thread with ID "temp-123"
↓
Shows thread immediately ✅ (optimistic UI)
↓
Syncs to server and waits for response
↓
Backend: Creates thread with ID "server-456"
↓
Frontend: Replaces "temp-123" with "server-456"
↓
Result: One thread, synced correctly ✅
```

**UX Impact:**
- No visual delay (optimistic UI)
- Seamless ID swap (user doesn't notice)
- Offline tolerance (keeps temp ID if sync fails)

---

## Testing

### Unit Tests Updated

```typescript
// frontend/tests/components/ChatApp.test.tsx
mockCreateThread.mockResolvedValue({  // ⚠️ Changed from mockReturnValue
  id: 'new-thread-456',
  title: 'New Chat',
  messages: [],
  createdAt: Date.now(),
  updatedAt: Date.now(),
});
```

**Changed:**
- `mockReturnValue` → `mockResolvedValue` (async)
- All test assertions updated to handle promises

### Manual Testing Scenarios

1. **Normal Flow**:
   - Create thread → Verify localStorage ID matches backend ID
   - Reload page → Thread persists with correct ID

2. **Network Failure**:
   - Disconnect network → Create thread → Verify temp ID used
   - Reconnect → Next thread creation uses server ID

3. **Race Conditions**:
   - Create 3 threads rapidly → Verify all get unique server IDs
   - No duplicate threads in database

---

## Migration Strategy

### Existing Threads

No migration needed. Existing threads in localStorage work as-is because:
1. They already have IDs
2. Backend creates separate records on first message sync
3. Future operations use existing IDs

**Optional cleanup** (if needed):
```typescript
// Migrate existing threads to backend
const threads = StorageService.getThreads();
for (const thread of threads) {
  try {
    await threadsApi.create({
      agent_id: 'chat',
      model: 'qwen:7b',
      provider: 'ollama',
      title: thread.title,
    });
  } catch (error) {
    console.warn('Thread already synced or failed:', thread.id);
  }
}
```

---

## Future Enhancements

### Phase 2: Sync Status Indicator

```typescript
interface Thread {
  id: string;
  syncStatus?: 'synced' | 'pending' | 'failed';
  tempId?: string; // Original temp ID for debugging
}
```

Show sync status in UI:
- 🟢 Green dot: Synced
- 🟡 Yellow dot: Pending
- 🔴 Red dot: Failed (with retry button)

### Phase 3: Retry Queue

```typescript
class SyncQueue {
  private queue: Array<() => Promise<void>> = [];
  
  async retry(threadId: string) {
    // Retry failed sync
  }
}
```

### Phase 4: Conflict Resolution

If temp ID already synced (duplicate):
- Show merge UI
- Let user choose which to keep
- Migrate messages to chosen thread

---

## Related Files

### Frontend
- [hooks/useChatThreads.ts](../../frontend/hooks/useChatThreads.ts) - Thread CRUD hook
- [services/storage.ts](../../frontend/services/storage.ts) - Storage + sync service
- [components/ChatApp.tsx](../../frontend/components/ChatApp.tsx) - Main chat UI
- [components/HomeRedirect.tsx](../../frontend/components/HomeRedirect.tsx) - Initial redirect

### Backend
- [api/routes.py](../../backend/api/routes.py) - Thread endpoints
- [services/thread_service.py](../../backend/services/thread_service.py) - Thread logic
- [database/models.py](../../backend/database/models.py) - SQLAlchemy models

---

## Summary

**Pattern**: Server-authoritative ID generation with optimistic UI  
**Status**: ✅ Implemented and tested  
**Impact**: Fixes critical data integrity issue, enables reliable sync  
**UX**: No perceived delay, seamless experience  
**Maintainability**: Clear separation of concerns, testable  

This pattern is now the **standard** for all entity creation in the app (threads, messages, artifacts).
