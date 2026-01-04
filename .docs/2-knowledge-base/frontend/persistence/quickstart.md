# Database Persistence - Quick Start Guide

## What Changed?

The frontend now syncs threads and messages to the backend database in the background. This is **Phase 1** implementation - LocalStorage remains the primary data source.

## For Developers

### No Breaking Changes

Existing code continues to work without modification. The sync happens automatically in the background.

### Optional: Pass Agent/Model Info

For better server sync, you can now pass agent type, model, and provider to `useChatThreads`:

**Before:**
```typescript
const { createThread } = useChatThreads();
```

**After (Optional):**
```typescript
const { createThread } = useChatThreads(
  initialThreadId,
  'chat',      // agentId
  'qwen:7b',   // model
  'ollama'     // provider
);
```

### What Happens Now?

1. **Create Thread**: Saved to LocalStorage → Synced to server in background
2. **Add Message**: Saved to LocalStorage → Synced to server in background
3. **Update Title**: Updated in LocalStorage → Synced to server in background
4. **Delete Thread**: Deleted from LocalStorage → Synced to server in background

### Non-Blocking

All sync operations are non-blocking:
- ✅ UI updates immediately
- ✅ Server sync happens in background
- ✅ Failures logged to console (no UI impact)

## Testing

### Check Sync Status

Open browser console and look for:

```
✅ Thread synced to server: thread-123
✅ Message synced to server: message-456
```

Or if sync fails:

```
⚠️ Failed to sync thread to server (non-blocking): Network error
```

### Monitor Network

Open DevTools → Network tab:
- Look for POST/PATCH/DELETE requests to `/api/threads` and `/api/messages`
- Status 200 = successful sync

## API Endpoints

The frontend now uses these additional endpoints:

- `POST /api/threads` - Create thread
- `GET /api/threads` - List threads
- `PATCH /api/threads/{id}` - Update thread
- `DELETE /api/threads/{id}` - Delete thread
- `POST /api/threads/{id}/messages` - Create message
- `GET /api/threads/{id}/messages` - List messages
- `DELETE /api/messages/{id}` - Delete message

## Environment Configuration

Make sure your `.env.local` has:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## FAQ

### Q: What if the backend is down?
**A**: Frontend continues to work normally with LocalStorage. Sync operations fail silently.

### Q: Will I see duplicates?
**A**: In Phase 1, yes. LocalStorage and server might have duplicates. Phase 2 will resolve this.

### Q: Can I disable sync?
**A**: Currently no. Sync is always attempted but never blocks the UI.

### Q: How do I test sync?
**A**: 
1. Open DevTools console
2. Create a new thread
3. Look for "✅ Thread synced to server" message
4. Check Network tab for POST request to `/api/threads`

### Q: Where is the data stored?
**A**: 
- **LocalStorage**: Browser storage (immediate, primary source)
- **Server**: SQLite database in `backend/agentkit.db`

## Troubleshooting

### No sync messages in console

Check:
1. Backend is running at `http://localhost:8000`
2. `NEXT_PUBLIC_API_URL` is set correctly
3. CORS is enabled on backend

### Sync failing with 404

Backend might not have the persistence endpoints. Check:
```bash
cd backend
python migrate.py  # Run migrations
python main.py     # Start backend
```

### LocalStorage vs Server mismatch

In Phase 1, this is expected. Phase 2 will add conflict resolution.

## What's Next?

**Phase 2** will implement:
- Read from server on load
- LocalStorage as cache only
- Conflict resolution
- Offline sync queue

## Related Docs

- [Complete Integration Guide](database-integration.md)
- [Backend Database Layer](../../../backend/DATABASE.md)
- [Implementation Plan](../../../.docs/1-implementation-plans/030-database-persistence-layer-plan.md)
