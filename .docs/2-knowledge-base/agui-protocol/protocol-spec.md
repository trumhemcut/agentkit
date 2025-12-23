# AG-UI Protocol Implementation Guide

**Date**: December 23, 2025

## Overview

AG-UI is a protocol for real-time agent-frontend communication using Server-Sent Events (SSE). It provides a standardized way for AI agents to stream events to frontend applications.

## Protocol Basics

### Transport
- **Method**: Server-Sent Events (SSE)
- **Content-Type**: `text/event-stream`
- **Format**: JSON events prefixed with `data:`

### Event Structure

All events follow this format:
```
data: {"type": "EVENT_TYPE", ...additional fields}\n\n
```

## Event Types

### 1. RUN_STARTED
Emitted when an agent run begins.

```json
{
  "type": "RUN_STARTED",
  "threadId": "uuid",
  "runId": "uuid"
}
```

**Usage**: First event in every agent execution stream.

### 2. RUN_FINISHED
Emitted when an agent run completes successfully.

```json
{
  "type": "RUN_FINISHED",
  "threadId": "uuid",
  "runId": "uuid"
}
```

**Usage**: Last event in successful agent execution stream.

### 3. RUN_ERROR
Emitted when an error occurs during agent execution.

```json
{
  "type": "RUN_ERROR",
  "threadId": "uuid",
  "runId": "uuid",
  "error": "Error message"
}
```

**Usage**: Replaces RUN_FINISHED when execution fails.

### 4. TEXT_MESSAGE_START
Emitted when agent starts generating a text message.

```json
{
  "type": "TEXT_MESSAGE_START",
  "messageId": "uuid",
  "role": "assistant"
}
```

**Usage**: Marks the beginning of a new message in the conversation.

### 5. TEXT_MESSAGE_CONTENT
Emitted for each content chunk during streaming.

```json
{
  "type": "TEXT_MESSAGE_CONTENT",
  "messageId": "uuid",
  "delta": "content chunk"
}
```

**Usage**: Can be emitted multiple times per message for streaming responses.

### 6. TEXT_MESSAGE_END
Emitted when message generation completes.

```json
{
  "type": "TEXT_MESSAGE_END",
  "messageId": "uuid"
}
```

**Usage**: Marks the end of a message.

## Event Flow Example

### Simple Chat Flow

```
1. RUN_STARTED (threadId: "abc", runId: "123")
2. TEXT_MESSAGE_START (messageId: "msg-1", role: "assistant")
3. TEXT_MESSAGE_CONTENT (messageId: "msg-1", delta: "Hello")
4. TEXT_MESSAGE_CONTENT (messageId: "msg-1", delta: " there")
5. TEXT_MESSAGE_CONTENT (messageId: "msg-1", delta: "!")
6. TEXT_MESSAGE_END (messageId: "msg-1")
7. RUN_FINISHED (threadId: "abc", runId: "123")
```

### Error Flow

```
1. RUN_STARTED (threadId: "abc", runId: "123")
2. RUN_ERROR (threadId: "abc", runId: "123", error: "LLM timeout")
```

## Implementation

### Backend (Python)

#### Event Encoder

```python
class EventEncoder:
    def encode(self, event: Dict[str, Any]) -> str:
        """Encode event as SSE format"""
        event_data = json.dumps(event)
        return f"data: {event_data}\n\n"
    
    def get_content_type(self) -> str:
        return "text/event-stream"
```

#### FastAPI Streaming Response

```python
@router.post("/chat")
async def chat_endpoint(input_data: RunAgentInput, request: Request):
    encoder = EventEncoder()
    
    async def event_generator():
        # Start run
        yield encoder.encode({
            "type": EventType.RUN_STARTED,
            "threadId": input_data.thread_id,
            "runId": input_data.run_id
        })
        
        try:
            # Stream agent events
            async for event in agent.run(state):
                yield encoder.encode(event)
            
            # Finish run
            yield encoder.encode({
                "type": EventType.RUN_FINISHED,
                "threadId": input_data.thread_id,
                "runId": input_data.run_id
            })
        except Exception as e:
            # Error handling
            yield encoder.encode({
                "type": EventType.RUN_ERROR,
                "threadId": input_data.thread_id,
                "runId": input_data.run_id,
                "error": str(e)
            })
    
    return StreamingResponse(
        event_generator(),
        media_type=encoder.get_content_type()
    )
```

#### Agent Implementation

```python
class ChatAgent(BaseAgent):
    async def run(self, state: AgentState) -> AsyncGenerator[Dict[str, Any], None]:
        message_id = str(uuid.uuid4())
        
        # Start message
        yield {
            "type": EventType.TEXT_MESSAGE_START,
            "messageId": message_id,
            "role": "assistant"
        }
        
        # Stream content
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield {
                    "type": EventType.TEXT_MESSAGE_CONTENT,
                    "messageId": message_id,
                    "delta": chunk.content
                }
        
        # End message
        yield {
            "type": EventType.TEXT_MESSAGE_END,
            "messageId": message_id
        }
```

### Frontend (TypeScript)

#### Event Consumer (Simplified)

```typescript
async function consumeAgentStream(threadId: string, messages: Message[]) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify({ threadId, messages })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6));
        handleEvent(event);
      }
    }
  }
}

function handleEvent(event: any) {
  switch (event.type) {
    case 'RUN_STARTED':
      console.log('Run started:', event.runId);
      break;
    case 'TEXT_MESSAGE_START':
      createMessage(event.messageId);
      break;
    case 'TEXT_MESSAGE_CONTENT':
      appendToMessage(event.messageId, event.delta);
      break;
    case 'TEXT_MESSAGE_END':
      finalizeMessage(event.messageId);
      break;
    case 'RUN_FINISHED':
      console.log('Run finished:', event.runId);
      break;
    case 'RUN_ERROR':
      console.error('Run error:', event.error);
      break;
  }
}
```

## Best Practices

### Backend

1. **Always wrap in RUN_STARTED/RUN_FINISHED**
   - Every stream should start with RUN_STARTED
   - Always end with either RUN_FINISHED or RUN_ERROR

2. **Use consistent IDs**
   - Generate UUIDs for thread_id, run_id, message_id
   - Keep IDs consistent across related events

3. **Handle errors gracefully**
   - Catch exceptions and emit RUN_ERROR
   - Include helpful error messages

4. **Stream incrementally**
   - Emit TEXT_MESSAGE_CONTENT as soon as chunks are available
   - Don't buffer large responses

5. **Type safety**
   - Use enums for event types
   - Validate event structure with Pydantic

### Frontend

1. **Handle partial events**
   - SSE can split events across chunks
   - Buffer incomplete events

2. **Track message state**
   - Use messageId to accumulate content chunks
   - Track active messages

3. **Error handling**
   - Handle network errors
   - Handle RUN_ERROR events
   - Show user-friendly messages

4. **Connection management**
   - Implement reconnection logic
   - Handle connection timeouts

## Testing

### Manual Testing with curl

```bash
# Test streaming
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}' \
  --no-buffer
```

### Expected Output

```
data: {"type": "RUN_STARTED", "threadId": "...", "runId": "..."}

data: {"type": "TEXT_MESSAGE_START", "messageId": "...", "role": "assistant"}

data: {"type": "TEXT_MESSAGE_CONTENT", "messageId": "...", "delta": "Hello"}

data: {"type": "TEXT_MESSAGE_CONTENT", "messageId": "...", "delta": " there"}

data: {"type": "TEXT_MESSAGE_END", "messageId": "..."}

data: {"type": "RUN_FINISHED", "threadId": "...", "runId": "..."}
```

## Common Pitfalls

1. **Not setting Content-Type**
   - Must be `text/event-stream`

2. **Forgetting newlines**
   - SSE format requires `\n\n` after each event

3. **Buffering responses**
   - Disable buffering in proxies/web servers
   - Use `--no-buffer` with curl

4. **Not handling disconnections**
   - Clients may disconnect
   - Implement graceful cleanup

5. **Inconsistent event order**
   - Always emit TEXT_MESSAGE_START before TEXT_MESSAGE_CONTENT
   - Always emit TEXT_MESSAGE_END after all content

## Advanced Features (Future)

### Tool Execution Events

```json
{
  "type": "TOOL_EXECUTION_START",
  "toolName": "search",
  "toolArgs": {...}
}

{
  "type": "TOOL_EXECUTION_END",
  "toolName": "search",
  "result": {...}
}
```

### Multi-Agent Events

```json
{
  "type": "AGENT_HANDOFF",
  "fromAgent": "planner",
  "toAgent": "executor"
}
```

### Status Updates

```json
{
  "type": "STATUS_UPDATE",
  "status": "thinking",
  "message": "Analyzing your request..."
}
```

## References

- [AG-UI Protocol Specification](https://github.com/ag-ui-protocol/ag-ui)
- [Server-Sent Events Spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [FastAPI Streaming Response](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
