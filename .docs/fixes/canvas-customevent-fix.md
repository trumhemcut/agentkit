# Canvas CustomEvent Fix - December 23, 2025

## Problem

Frontend was receiving validation errors when backend sent custom canvas events:

```
Error in canvas agent, falling back to chat: 3 validation errors for CustomEvent
type
  Input should be <EventType.CUSTOM: 'CUSTOM'> [type=literal_error, input_value='thinking', input_type=str]
name
  Field required [type=missing, input_value={'type': 'thinking', 'dat...ing create request...'}}, input_type=dict]
value
  Field required [type=missing, input_value={'type': 'thinking', 'dat...ing create request...'}}, input_type=dict]
```

## Root Cause

The `CustomEvent` class from `ag-ui.core` requires a specific structure:
- `type`: Must be `EventType.CUSTOM` (not a custom string)
- `name`: The actual event name (e.g., "thinking", "artifact_created")
- `value`: The event data payload

The canvas agent was incorrectly creating events like:
```python
CustomEvent(
    type="thinking",  # ❌ Wrong - should be EventType.CUSTOM
    data={...}        # ❌ Wrong - should be 'value'
)
```

## Solution

### Backend Changes

**File: `backend/agents/canvas_agent.py`**

Fixed all CustomEvent usages to follow the correct structure:

```python
# Before (incorrect)
yield CustomEvent(
    type="thinking",
    data={"message": "Processing..."}
)

# After (correct)
yield CustomEvent(
    type=EventType.CUSTOM,
    name="thinking",
    value={"message": "Processing..."}
)
```

Applied this fix to all 7 custom events:
1. `thinking` - Agent processing notification
2. `artifact_streaming_start` - Begin artifact generation
3. `artifact_streaming` - Streaming content chunks
4. `artifact_created` - New artifact created
5. `artifact_updated` - Artifact updated
6. `artifact_streaming_start` (update mode) - Begin artifact update
7. `artifact_streaming` (update mode) - Update content chunks

### Frontend Changes

**File: `frontend/types/agui.ts`**

Added CUSTOM event type and interface:

```typescript
export enum EventType {
  // ... existing events
  CUSTOM = 'CUSTOM',  // ← Added
}

export interface CustomEvent extends BaseEvent {
  type: EventType.CUSTOM;
  name: string;
  value: any;
}
```

**File: `frontend/components/Canvas/CanvasChatContainer.tsx`**

Added handler for custom canvas events:

```typescript
const unsubscribeCustom = on(EventType.CUSTOM, (event) => {
  const customEvent = event as any;
  const eventName = customEvent.name;
  const eventValue = customEvent.value;
  
  switch (eventName) {
    case 'thinking':
      // Handle thinking event
      break;
    case 'artifact_streaming_start':
      setIsArtifactStreaming(true);
      clearStreamingContent();
      break;
    case 'artifact_streaming':
      appendStreamingContent(eventValue.contentDelta || '');
      break;
    case 'artifact_created':
      setArtifact(eventValue.artifact);
      setIsArtifactStreaming(false);
      break;
    case 'artifact_updated':
      setArtifact(eventValue.artifact);
      setIsArtifactStreaming(false);
      break;
  }
});
```

## Testing

### Backend Test

Created `backend/tests/test_custom_event.py` to verify CustomEvent structure:

```bash
$ python tests/test_custom_event.py
============================================================
CustomEvent Structure Tests
============================================================
Testing CustomEvent structure...
✓ CustomEvent structure is correct
✓ CustomEvent with artifact data is correct

============================================================
✓ All tests passed!
============================================================
```

### Integration Test

All existing canvas tests still pass:

```bash
$ python tests/test_canvas.py
============================================================
Canvas Feature Backend Tests
============================================================
...
✓ All tests passed!
============================================================
```

## Event Flow (After Fix)

### Backend → Frontend

1. **Backend creates event:**
```python
CustomEvent(
    type=EventType.CUSTOM,
    name="artifact_created",
    value={"artifact": {...}}
)
```

2. **ag-ui encodes to JSON:**
```json
{
  "type": "CUSTOM",
  "name": "artifact_created",
  "value": {
    "artifact": {
      "currentIndex": 1,
      "contents": [...]
    }
  }
}
```

3. **Frontend receives SSE:**
```
data: {"type":"CUSTOM","name":"artifact_created","value":{...}}
```

4. **Frontend processes:**
```typescript
// AGUI client receives event
// Emits to EventType.CUSTOM listeners
// CanvasChatContainer handles by event.name
```

## Files Modified

### Backend
- ✅ `backend/agents/canvas_agent.py` - Fixed all 7 CustomEvent usages
- ✅ `backend/tests/test_custom_event.py` - New test file

### Frontend
- ✅ `frontend/types/agui.ts` - Added CUSTOM event type and interface
- ✅ `frontend/components/Canvas/CanvasChatContainer.tsx` - Added custom event handler

## Verification Steps

1. **Start backend:**
```bash
cd backend
source ../.venv/bin/activate
uvicorn main:app --reload
```

2. **Start frontend:**
```bash
cd frontend
npm run dev
```

3. **Test canvas:**
- Navigate to Canvas mode
- Send: "Write a Python function to calculate factorial"
- Verify: Artifact appears on the right side
- Verify: No validation errors in console

## Result

✅ **Fixed** - Canvas feature now works correctly with proper CustomEvent structure
✅ **Tested** - All tests passing
✅ **Compatible** - Follows ag-ui-protocol specification
✅ **Complete** - Both backend and frontend updated

## Related Documentation

- AG-UI Protocol: https://github.com/ag-grid/ag-ui-protocol
- Implementation Plan: `.docs/1-implementation-plans/canvas-feature.md`
- Canvas Backend: `backend/CANVAS_README.md`
- Canvas Quickstart: `.docs/2-knowledge-base/canvas-backend-quickstart.md`
