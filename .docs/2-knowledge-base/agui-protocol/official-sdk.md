# AG-UI Protocol Implementation - Official SDK

**Date**: December 23, 2025  
**Status**: ✅ Implemented with Official SDK

## Summary

The backend now uses the **official AG-UI Python SDK** (`ag-ui-protocol` package) for all agent-frontend communication. This ensures full compliance with the AG-UI protocol specification and provides type-safe, well-documented event classes.

## Official Package

### Installation
```bash
pip install ag-ui-protocol
```

### Package Structure
- `ag_ui.core` - Core event types and models
- `ag_ui.encoder` - EventEncoder for SSE formatting

## Implementation Details

### 1. Event Types
We import EventType from the official SDK:

```python
from ag_ui.core import EventType
```

Available event types:
- `EventType.RUN_STARTED`
- `EventType.RUN_FINISHED`
- `EventType.RUN_ERROR`
- `EventType.TEXT_MESSAGE_START`
- `EventType.TEXT_MESSAGE_CONTENT`
- `EventType.TEXT_MESSAGE_END`

### 2. Event Encoder
We use the official EventEncoder:

```python
from ag_ui.encoder import EventEncoder

encoder = EventEncoder(accept="text/event-stream")
encoded = encoder.encode(event)  # Returns SSE formatted string
```

### 3. Event Classes
The official SDK provides Pydantic models for all events:

```python
from ag_ui.core import (
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    BaseEvent
)
```

## Code Examples

### FastAPI Route Handler
```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import EventType, RunStartedEvent, RunFinishedEvent, RunErrorEvent
from ag_ui.encoder import EventEncoder

@router.post("/chat")
async def chat_endpoint(input_data: RunAgentInput, request: Request):
    encoder = EventEncoder(accept=request.headers.get("accept"))
    
    async def event_generator():
        # Start run with official event class
        yield encoder.encode(
            RunStartedEvent(
                type=EventType.RUN_STARTED,
                thread_id=input_data.thread_id,
                run_id=input_data.run_id
            )
        )
        
        try:
            # Stream agent events
            async for event in chat_agent.run(state):
                yield encoder.encode(event)
            
            # Finish run with official event class
            yield encoder.encode(
                RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id
                )
            )
        except Exception as e:
            # Error with official event class
            yield encoder.encode(
                RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id,
                    message=str(e)
                )
            )
    
    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type()
    )
```

### Chat Agent
```python
from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    BaseEvent
)

class ChatAgent(BaseAgent):
    async def run(self, state: AgentState) -> AsyncGenerator[BaseEvent, None]:
        message_id = str(uuid.uuid4())
        
        # Start message
        yield TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant"
        )
        
        # Stream content chunks
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta=chunk.content
                )
        
        # End message
        yield TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
```

## Benefits of Official SDK

### 1. Type Safety
All events are Pydantic models with proper validation:
- Field name validation (camelCase)
- Type checking
- Required vs optional fields
- Custom validators

### 2. Correct Field Names
The SDK ensures proper camelCase naming:
- ✅ `thread_id` → serializes to `threadId`
- ✅ `run_id` → serializes to `runId`
- ✅ `message_id` → serializes to `messageId`

### 3. Documentation
Events are self-documenting with docstrings and type hints.

### 4. Protocol Compliance
Guaranteed compatibility with AG-UI frontend clients.

### 5. Future-Proof
Automatic updates when new event types are added to the protocol.

## Testing

### Manual Test
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}' \
  --no-buffer
```

### Expected Output
```
data: {"type":"RUN_STARTED","threadId":"...","runId":"..."}

data: {"type":"TEXT_MESSAGE_START","messageId":"...","role":"assistant"}

data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"...","delta":"Hello"}

data: {"type":"TEXT_MESSAGE_CONTENT","messageId":"...","delta":" there"}

data: {"type":"TEXT_MESSAGE_END","messageId":"..."}

data: {"type":"RUN_FINISHED","threadId":"...","runId":"..."}
```

Note the proper camelCase field names: `threadId`, `runId`, `messageId`

## File Structure

```
backend/
  protocols/
    event_types.py     # Re-exports EventType from ag_ui.core
    event_encoder.py   # Re-exports EventEncoder from ag_ui.encoder
  agents/
    chat_agent.py      # Uses official event classes
  api/
    routes.py          # Uses official event classes
```

## Migration Notes

### Before (Custom Implementation)
```python
# Custom EventType enum
class EventType(str, Enum):
    RUN_STARTED = "RUN_STARTED"
    ...

# Custom encoder
class EventEncoder:
    def encode(self, event: Dict[str, Any]) -> str:
        return f"data: {json.dumps(event)}\n\n"

# Manual dict creation
yield {"type": "TEXT_MESSAGE_START", "messageId": message_id, ...}
```

### After (Official SDK)
```python
# Import from official SDK
from ag_ui.core import EventType, TextMessageStartEvent
from ag_ui.encoder import EventEncoder

# Type-safe event creation
yield TextMessageStartEvent(
    type=EventType.TEXT_MESSAGE_START,
    message_id=message_id,  # Python snake_case
    role="assistant"
)
# Automatically serializes to: {"type":"TEXT_MESSAGE_START","messageId":"...","role":"assistant"}
```

## Best Practices

1. **Always use official event classes** instead of dicts
2. **Import types from ag_ui.core** for consistency
3. **Use Python snake_case** for field names (SDK handles conversion)
4. **Type hint with BaseEvent** for async generators
5. **Let Pydantic handle validation** - don't manually validate
6. **Use EventEncoder.encode()** for all events

## Documentation References

- Official AG-UI Docs: https://docs.ag-ui.com
- Python SDK: https://docs.ag-ui.com/sdk/python
- Event Types: https://docs.ag-ui.com/sdk/python/core/events
- EventEncoder: https://docs.ag-ui.com/sdk/python/encoder

## Verification Checklist

✅ Installed `ag-ui-protocol` package  
✅ Imported EventType from `ag_ui.core`  
✅ Imported EventEncoder from `ag_ui.encoder`  
✅ Using official event classes (RunStartedEvent, TextMessageContentEvent, etc.)  
✅ Proper field naming (snake_case in Python, camelCase in JSON)  
✅ Type hints with BaseEvent  
✅ SSE streaming working  
✅ Events conform to AG-UI protocol  
✅ Tested with curl - confirmed proper JSON serialization  

## Conclusion

The backend now fully implements the AG-UI protocol using the official Python SDK. All communication with the frontend follows the standardized AG-UI specification, ensuring seamless integration and type safety throughout the application.
