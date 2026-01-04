# Database Persistence - Thread Creation Flow

## Câu hỏi: Khi nào frontend gọi backend để tạo thread?

## Trả lời chi tiết

### 📍 Thời điểm gọi

Thread được tạo và sync lên backend khi:

1. **User clicks nút "New Chat"** trong UI
   - Vị trí: Header hoặc Sidebar
   - Action: `handleNewChat()` được trigger

2. **Auto-create thread đầu tiên**
   - Khi app khởi động và không có thread nào
   - `useChatThreads` hook tự động tạo thread đầu tiên

### 🔄 Flow chi tiết

```
User Action
    ↓
[ChatApp] handleNewChat()
    ↓
[useChatThreads] createThread()
    ↓
1. Tạo thread object với crypto.randomUUID()
2. Lưu vào LocalStorage (ngay lập tức)
3. Update UI state (setThreads, setCurrentThreadId)
    ↓
4. StorageService.syncThreadToServer() 🚀
    ↓
5. threadsApi.create() → POST /api/threads
    ↓
Backend Database ✅
```

### 📝 Code Flow

#### 1. ChatApp.tsx (Line 127)
```typescript
const handleNewChat = useCallback(() => {
  // ...
  if (hasNoThread || hasMessages) {
    const newThread = createThread(); // ← Gọi ở đây
    // ...
  }
}, [currentThread, createThread, deactivateCanvas]);
```

#### 2. useChatThreads.ts (Line 61-78)
```typescript
const createThread = useCallback(() => {
  const newThread: Thread = {
    id: crypto.randomUUID(),
    title: 'New Chat',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  // Bước 1: Lưu local (blocking, immediate)
  StorageService.saveThread(newThread);
  setThreads(StorageService.getThreads());
  setCurrentThreadId(newThread.id);
  
  // Bước 2: Sync server (non-blocking, background)
  StorageService.syncThreadToServer(newThread, agentId, model, provider);
  
  return newThread;
}, [agentId, model, provider]);
```

#### 3. storage.ts (Line 150-163)
```typescript
static async syncThreadToServer(
  thread: Thread, 
  agentId: string, 
  model: string, 
  provider: string
): Promise<void> {
  try {
    await threadsApi.create({
      agent_id: agentId,
      model: model,
      provider: provider,
      title: thread.title,
    });
    console.log('[StorageService] ✅ Thread synced to server:', thread.id);
  } catch (error) {
    console.error('[StorageService] ⚠️ Failed to sync (non-blocking):', error);
  }
}
```

#### 4. api.ts (Line 645-663)
```typescript
export const threadsApi = {
  create: async (data: CreateThreadRequest): Promise<Thread> => {
    const params = new URLSearchParams();
    params.append('agent_type', data.agent_type);
    params.append('model', data.model);
    params.append('provider', data.provider);
    if (data.title) {
      params.append('title', data.title);
    }

    const response = await fetch(
      `${API_BASE_URL}/api/threads?${params.toString()}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    return response.json();
  },
}
```

### ✅ Fix đã áp dụng (Jan 4, 2026)

**Vấn đề trước đây:**
- `useChatThreads()` được gọi KHÔNG có tham số
- Luôn dùng default: `'chat'`, `'qwen:7b'`, `'ollama'`
- Bất kể user chọn agent/model gì trong UI

**Giải pháp:**
```typescript
// ChatApp.tsx
const selectedModel = useModelStore((state) => state.selectedModel);
const selectedProvider = useModelStore((state) => state.selectedProvider);
const selectedAgent = useAgentStore((state) => state.selectedAgent);

const { createThread, ... } = useChatThreads(
  initialThreadId,
  selectedAgent || 'chat',      // ✅ Dùng agent thực tế
  selectedModel || 'qwen:7b',   // ✅ Dùng model thực tế
  selectedProvider || 'ollama'  // ✅ Dùng provider thực tế
);
```

### 🎯 Request gửi lên backend

**Endpoint:** `POST /api/threads`

**Request Body:**
```json
{
  "agent_id": "canvas",
  "model": "gemini-2.5-flash",
  "provider": "gemini",
  "title": "New Chat"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "New Chat",
  "agent_id": "canvas",
  "model": "gemini-2.5-flash",
  "provider": "gemini",
  "created_at": "2026-01-04T10:30:00.000Z",
  "updated_at": "2026-01-04T10:30:00.000Z"
}
```

### ⚙️ Đặc điểm kỹ thuật

#### Non-Blocking
- Thread được tạo trong LocalStorage **trước**
- UI update **ngay lập tức**
- API call chạy **background** (async)
- Nếu API fail → UI vẫn hoạt động bình thường

#### Error Handling
```typescript
try {
  await threadsApi.create(data);
  console.log('✅ Thread synced');
} catch (error) {
  console.error('⚠️ Failed to sync (non-blocking):', error);
  // Không throw error → UI không bị ảnh hưởng
}
```

### 🧪 Cách test

#### 1. Monitor Console
```javascript
// Mở browser console, sẽ thấy:
[StorageService] saveThread: <id> with 0 messages CREATE
[StorageService] ✅ Thread synced to server: <id>
```

#### 2. Monitor Network Tab
```
POST /api/threads?agent_type=chat&model=qwen:7b&provider=ollama&title=New+Chat
Status: 200 OK
```

#### 3. Check Database
```bash
# Backend
cd backend
sqlite3 agentkit.db
SELECT * FROM threads ORDER BY created_at DESC LIMIT 1;
```

### 📊 Timing

```
Action         | Time  | Blocking?
---------------|-------|----------
Click "New"    | 0ms   | -
Create UUID    | <1ms  | Yes
Save Local     | ~5ms  | Yes
Update UI      | ~10ms | Yes
API Request    | 50-200ms | No (async)
DB Insert      | 10-50ms  | No (server side)
```

**User sees:** Thread xuất hiện sau ~15ms  
**Server receives:** Request sau ~100ms

### 🔮 Phase 2 (Tương lai)

Phase 2 sẽ thay đổi:
- Fetch threads từ server khi load app
- LocalStorage = cache only
- Sync conflicts resolution
- Offline queue

## Summary

**Khi nào gọi backend?**
→ **Ngay khi user clicks "New Chat"** hoặc **app tạo thread đầu tiên**

**Blocking không?**
→ **Không**, UI update ngay, API call chạy background

**Dữ liệu gửi gì?**
→ **Agent type, model, provider, title** (từ UI selection, không phải hardcoded)

**Nếu backend down?**
→ **App vẫn hoạt động bình thường**, chỉ console log warning
