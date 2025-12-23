# Backend Integration Guide

## Overview

This document describes the API contract between the frontend and backend, including expected endpoints, data formats, and AG-UI event protocol.

## Required Backend Endpoints

### 1. Send Chat Message

**Endpoint**: `POST /api/chat/message`

**Purpose**: Send user message to agent for processing

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "message": "User's message text",
  "threadId": "thread-123"
}
```

**Response** (Success):
```json
{
  "success": true,
  "messageId": "msg-456"
}
```

**Response** (Error):
```json
{
  "success": false,
  "messageId": "",
  "error": "Error description"
}
```

**Status Codes**:
- `200 OK`: Message received successfully
- `400 Bad Request`: Invalid request data
- `500 Internal Server Error`: Server error

---

### 2. AG-UI Event Stream

**Endpoint**: `GET /api/agent/stream`

**Purpose**: SSE endpoint for streaming agent responses using AG-UI protocol

**Query Parameters**:
- `threadId` (required): Thread ID for the conversation

**Response Type**: `text/event-stream`

**Response Format**:
```
event: message
data: {"type":"RUN_STARTED","data":{"runId":"run-123"},"timestamp":1234567890}

event: message
data: {"type":"TEXT_MESSAGE_CHUNK","data":{"content":"Hello"},"timestamp":1234567891}

event: message
data: {"type":"RUN_FINISHED","data":{},"timestamp":1234567892}
```

**Connection**:
- Keep-alive connection
- Client automatically reconnects on disconnect
- Server should implement heartbeat (optional)

---

### 3. Get Agent Status (Optional)

**Endpoint**: `GET /api/agent/{agentId}/status`

**Purpose**: Get current status of an agent

**Path Parameters**:
- `agentId`: Agent identifier

**Response**:
```json
{
  "agentId": "agent-1",
  "status": "active",
  "lastUpdate": 1234567890
}
```

**Status Values**:
- `active`: Agent is running
- `idle`: Agent is idle
- `error`: Agent encountered an error

---

## AG-UI Protocol

### Event Structure

All AG-UI events follow this structure:

```typescript
interface AGUIEvent {
  type: AGUIEventType;
  data: any;
  timestamp: number;
  agentName?: string;
  threadId?: string;
}
```

### Event Types

#### 1. RUN_STARTED

Emitted when agent begins processing a request.

```json
{
  "type": "RUN_STARTED",
  "data": {
    "runId": "run-123",
    "agentName": "Agent Name"
  },
  "timestamp": 1234567890
}
```

#### 2. TEXT_MESSAGE_CHUNK

Emitted for each chunk of streaming text response.

```json
{
  "type": "TEXT_MESSAGE_CHUNK",
  "data": {
    "content": "Text chunk",
    "isComplete": false
  },
  "timestamp": 1234567891,
  "agentName": "Agent Name"
}
```

**Guidelines**:
- Send small chunks (e.g., word-by-word or sentence-by-sentence)
- Set `isComplete: true` on the final chunk (optional)
- Include `agentName` for multi-agent scenarios

#### 3. RUN_FINISHED

Emitted when agent completes processing successfully.

```json
{
  "type": "RUN_FINISHED",
  "data": {
    "runId": "run-123",
    "message": "Completed successfully"
  },
  "timestamp": 1234567892
}
```

#### 4. THINKING

Emitted when agent is processing/thinking (optional).

```json
{
  "type": "THINKING",
  "data": {
    "message": "Analyzing your request..."
  },
  "timestamp": 1234567893
}
```

#### 5. EXECUTING

Emitted when agent is executing a tool/action (optional).

```json
{
  "type": "EXECUTING",
  "data": {
    "action": "search",
    "tool": "web_search"
  },
  "timestamp": 1234567894
}
```

#### 6. ERROR

Emitted when an error occurs.

```json
{
  "type": "ERROR",
  "data": {
    "message": "Error description",
    "code": "ERROR_CODE"
  },
  "timestamp": 1234567895
}
```

---

## Implementation Guidelines

### Backend (Python/FastAPI Example)

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json
import asyncio

app = FastAPI()

@app.post("/api/chat/message")
async def send_message(request: Request):
    data = await request.json()
    message = data.get("message")
    thread_id = data.get("threadId")
    
    # Process message (trigger agent)
    # ...
    
    return {
        "success": True,
        "messageId": f"msg-{timestamp}"
    }

@app.get("/api/agent/stream")
async def agent_stream(thread_id: str):
    async def event_generator():
        # Send RUN_STARTED
        yield f"event: message\n"
        yield f"data: {json.dumps({
            'type': 'RUN_STARTED',
            'data': {'runId': 'run-123'},
            'timestamp': time.time() * 1000
        })}\n\n"
        
        # Stream response chunks
        for chunk in response_chunks:
            yield f"event: message\n"
            yield f"data: {json.dumps({
                'type': 'TEXT_MESSAGE_CHUNK',
                'data': {'content': chunk},
                'timestamp': time.time() * 1000
            })}\n\n"
            await asyncio.sleep(0.1)  # Small delay
        
        # Send RUN_FINISHED
        yield f"event: message\n"
        yield f"data: {json.dumps({
            'type': 'RUN_FINISHED',
            'data': {},
            'timestamp': time.time() * 1000
        })}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
```

---

## CORS Configuration

Enable CORS for frontend to access backend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Testing

### Test with curl

#### Send Message:
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","threadId":"test-123"}'
```

#### Test SSE Stream:
```bash
curl -N http://localhost:8000/api/agent/stream?threadId=test-123
```

### Test with Postman

1. Create POST request to `/api/chat/message`
2. Set body to raw JSON
3. For SSE, use GET request and observe streamed events

---

## Environment Configuration

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend

Configure CORS to allow frontend origin:
```python
ALLOWED_ORIGINS=["http://localhost:3000"]
```

---

## Error Handling

### Frontend Responsibilities

1. **Connection Errors**: Display user-friendly message
2. **Timeout**: Implement timeout for long-running requests
3. **Retry Logic**: Retry failed API calls
4. **Graceful Degradation**: Handle missing features

### Backend Responsibilities

1. **Validation**: Validate all inputs
2. **Error Messages**: Provide clear error messages
3. **Status Codes**: Use appropriate HTTP status codes
4. **Rate Limiting**: Implement rate limiting for API calls
5. **Authentication**: (Future) Implement authentication/authorization

---

## Performance Considerations

### Streaming Best Practices

1. **Chunk Size**: Send reasonably-sized chunks (not too small)
2. **Buffering**: Avoid buffering on server or proxy
3. **Heartbeat**: Send periodic heartbeat to keep connection alive
4. **Timeout**: Implement timeout for inactive connections
5. **Compression**: Consider gzip compression for large responses

### API Optimization

1. **Caching**: Cache agent status responses
2. **Connection Pooling**: Reuse database connections
3. **Async Processing**: Use async for non-blocking operations
4. **Load Balancing**: Distribute load across multiple backend instances

---

## Security Considerations

1. **Authentication**: Implement JWT or session-based auth
2. **Authorization**: Validate user access to threads
3. **Input Validation**: Sanitize all user inputs
4. **Rate Limiting**: Prevent abuse
5. **HTTPS**: Use HTTPS in production
6. **CORS**: Restrict CORS to known origins

---

## Future Enhancements

1. **Authentication**: User authentication and authorization
2. **Multi-tenancy**: Support multiple users/workspaces
3. **File Uploads**: Support file attachments
4. **Voice Input**: Voice-to-text integration
5. **Real-time Collaboration**: Multi-user chat support
6. **Agent Selection**: Allow users to select specific agents
7. **Feedback Loop**: User feedback on agent responses
