# Stop Streaming & Graceful Disconnection

## Overview

The backend supports graceful handling of client disconnections during streaming responses. When a user clicks the "Stop" button or aborts a request, the backend detects the disconnection and cleans up resources appropriately.

## Implementation

### FastAPI StreamingResponse Behavior

FastAPI's `StreamingResponse` natively handles client disconnections:
- When a client closes the connection, the async generator automatically receives a `GeneratorExit` exception
- The generator stops producing events and cleans up
- No explicit cancellation mechanism is needed from the backend

### Backend Implementation (api/routes.py)

All streaming endpoints have been updated with try-except-GeneratorExit pattern:

```python
async def event_generator():
    try:
        # Send RUN_STARTED event
        yield encoder.encode(RunStartedEvent(...))
        
        # Stream events...
        async for event in graph.astream(state):
            yield encoder.encode(event)
        
        # Send RUN_FINISHED event
        yield encoder.encode(RunFinishedEvent(...))
    
    except GeneratorExit:
        # Client disconnected (e.g., user clicked Stop button)
        logger.info(f"[ROUTES] Client disconnected for run_id={input_data.run_id}")
        # FastAPI handles cleanup automatically
    
    except Exception as e:
        # Handle other errors
        logger.error(f"[ROUTES] Error: {e}")
        yield encoder.encode(RunErrorEvent(...))
```

### Endpoints with Graceful Disconnection

The following endpoints support graceful disconnection:

1. **`POST /api/chat/{agent_id}`** - Main chat endpoint for all agents
   - Logs: `Client disconnected for agent={agent_id}, run_id={run_id}`

2. **`POST /api/agents/{agent_id}/action`** - A2UI action handling
   - Logs: `Client disconnected for agent={agent_id}, action={action_name}, run_id={run_id}`

3. **`POST /api/canvas/stream`** - Deprecated canvas endpoint
   - Logs: `Client disconnected for canvas endpoint, run_id={run_id}`

### Logging

When a client disconnects, the backend logs:
```
[ROUTES] Client disconnected for agent=chat, run_id=abc123, thread_id=thread456
```

This helps with:
- Debugging streaming issues
- Monitoring user behavior (how often responses are stopped)
- Detecting patterns in request cancellations

## Frontend Integration

### AbortController Usage

The frontend uses the browser's native `AbortController` API:

```typescript
const abortController = new AbortController();

const response = await fetch('/api/chat/chat', {
  method: 'POST',
  body: JSON.stringify(request),
  signal: abortController.signal  // Connect abort signal
});

// Later, when user clicks Stop:
abortController.abort();  // Closes connection, triggers GeneratorExit in backend
```

### User Actions that Trigger Disconnection

1. **Stop Button Click** - User explicitly stops streaming
2. **New Message During Streaming** - User sends new message, aborting current stream
3. **Navigation Away** - Browser closes connection when leaving page
4. **Network Issues** - Connection loss triggers same cleanup

## LangGraph Behavior

When the generator exits:
- LangGraph's `astream()` stops producing events
- The async task continues briefly but stops yielding
- No explicit cancellation of LLM calls (passive cleanup)
- Memory and resources are garbage collected

### Future Enhancement: Active LLM Cancellation

Currently, LangGraph workflows stop passively. For active cancellation:

```python
# Option 1: Use configurable run_id for tracking
graph = graph.with_config({
    "configurable": {
        "run_id": run_id,
        "checkpoint_ns": f"run_{run_id}"
    }
})

# Option 2: Implement custom cancellation logic
# Track active LLM requests and cancel them explicitly
```

This is optional as costs are minimal with quick disconnection handling.

## Testing

### Manual Testing

Run the test script to verify graceful disconnection:

```bash
cd backend
python tests/test_graceful_disconnection.py
```

Expected output:
- `[ROUTES] Client disconnected` log messages
- No errors or exceptions
- Clean shutdown for all requests

### Test Cases

1. **Abort During Text Streaming** - Stop while agent is responding
2. **Abort During A2UI Action** - Stop during component interaction
3. **Normal Completion** - Baseline test (no abort)

## Error Handling

### Client-Side Abort (DOMException)

Frontend catches `AbortError`:
```typescript
try {
  // ... fetch with signal ...
} catch (error) {
  if (error instanceof DOMException && error.name === 'AbortError') {
    console.log('Request aborted by user');
    // Update UI to show interrupted state
  }
}
```

### Network Errors

Network disconnections trigger same `GeneratorExit` behavior:
- No special handling needed
- Backend logs disconnection
- Frontend handles as network error

## Best Practices

### Backend

1. **Always wrap generators in try-except-GeneratorExit**
   - Ensures clean logging and resource cleanup
   - Prevents unhandled exceptions

2. **Log disconnections at INFO level**
   - Normal user behavior, not an error
   - Helps with monitoring and analytics

3. **Don't try to send events after GeneratorExit**
   - Connection is closed, events won't be received
   - Let FastAPI handle cleanup

### Frontend

1. **Store AbortController reference**
   - Keep reference to abort later
   - Clear reference after completion

2. **Provide immediate UI feedback**
   - Don't wait for server response
   - Update UI state immediately on abort

3. **Handle Enter key during streaming**
   - Stop current stream
   - Wait briefly (100-150ms) for cleanup
   - Send new message

## Monitoring

### Metrics to Track

- **Disconnection rate**: How often users stop responses
- **Time to disconnection**: How long before users abort
- **Agents with most stops**: Which agents get interrupted most

### Log Analysis

Search logs for disconnection patterns:
```bash
grep "Client disconnected" backend/logs/*.log | wc -l
```

Analyze by agent:
```bash
grep "Client disconnected" backend/logs/*.log | grep -o "agent=[^,]*" | sort | uniq -c
```

## Architecture Diagram

```
┌─────────────┐
│  Frontend   │
│             │
│  [Stop Btn] │──────────┐
│             │          │
│ AbortCtrl   │          │ .abort()
└─────────────┘          │
                         ↓
                   HTTP Connection
                      Closed
                         │
┌────────────────────────┼────────────┐
│  Backend              ↓             │
│                                     │
│  StreamingResponse                  │
│    ↓                                │
│  async generator                    │
│    ↓                                │
│  GeneratorExit ← Connection closed  │
│    ↓                                │
│  Log disconnection                  │
│    ↓                                │
│  Cleanup (automatic)                │
└─────────────────────────────────────┘
```

## Related Documentation

- Frontend implementation: [frontend/components/ChatInput.tsx]
- AG-UI protocol: [backend/protocols/README.md]
- LangGraph patterns: [backend/graphs/README.md]

## FAQ

**Q: Does stopping waste API tokens?**
A: Minimal waste. The LLM may complete the current token generation, but stops before generating more.

**Q: Can backend detect stop vs network error?**
A: No difference - both trigger GeneratorExit. This is by design (simple, reliable).

**Q: What happens to partial responses?**
A: Frontend marks message as interrupted: `"[Response interrupted by user]"`

**Q: Does this work with all agents?**
A: Yes - all agents use the same streaming infrastructure.

**Q: Performance impact?**
A: None - native browser and FastAPI behavior, no additional overhead.
