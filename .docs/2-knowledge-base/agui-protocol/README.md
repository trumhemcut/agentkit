# AG-UI Protocol Documentation

**Last Updated**: December 23, 2025

## Overview

AG-UI (Agent UI) is a protocol for real-time communication between AI agents and frontend applications. It uses Server-Sent Events (SSE) to stream agent execution events from the backend to the frontend, enabling real-time UI updates as agents think, execute actions, and generate responses.

## Protocol Architecture

```
┌─────────────┐                    ┌─────────────┐
│   Backend   │    SSE Stream      │  Frontend   │
│  (FastAPI)  │ ─────────────────> │   (React)   │
│             │   JSON Events      │             │
└─────────────┘                    └─────────────┘
     │                                     │
     ├─ LangGraph Agents                  ├─ AG-UI Client
     ├─ AG-UI Event Emitter               ├─ Event Handlers
     └─ SSE Encoder                       └─ UI Components
```

## Key Concepts

### Server-Sent Events (SSE)
- **Unidirectional**: Server → Client streaming only
- **HTTP-based**: Uses standard HTTP/1.1 with `text/event-stream` content type
- **Real-time**: Events are pushed as they occur
- **Simple**: JSON events prefixed with `data:`

### Event-Driven Architecture
- Agents emit events at key execution points
- Frontend subscribes to event types
- UI updates reactively based on event stream
- Type-safe event handling on both ends

## Documentation Structure

### [Protocol Specification](protocol-spec.md)
Complete reference for all AG-UI event types:
- Event formats and structures
- Event lifecycle and sequences
- Required and optional fields
- Usage patterns

### [Official SDK](official-sdk.md)
Backend implementation using the official Python SDK:
- Installation and setup
- Event types and models
- Event encoder usage
- Code examples

### [Frontend Integration](frontend-integration.md)
Frontend SSE integration patterns:
- AG-UI client implementation
- Event processing
- React hooks integration
- Error handling and reconnection

## Quick Start

### Backend (Python)

```python
from ag_ui.core import (
    EventType,
    RunStartedEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    RunFinishedEvent
)
from ag_ui.encoder import EventEncoder

# Create encoder
encoder = EventEncoder(accept="text/event-stream")

# Emit events
yield encoder.encode(RunStartedEvent(
    type=EventType.RUN_STARTED,
    thread_id=thread_id,
    run_id=run_id
))

yield encoder.encode(TextMessageStartEvent(
    type=EventType.TEXT_MESSAGE_START,
    message_id=message_id,
    role="assistant"
))

yield encoder.encode(TextMessageContentEvent(
    type=EventType.TEXT_MESSAGE_CONTENT,
    message_id=message_id,
    delta="Hello, "
))

yield encoder.encode(TextMessageContentEvent(
    type=EventType.TEXT_MESSAGE_CONTENT,
    message_id=message_id,
    delta="world!"
))

yield encoder.encode(TextMessageEndEvent(
    type=EventType.TEXT_MESSAGE_END,
    message_id=message_id
))

yield encoder.encode(RunFinishedEvent(
    type=EventType.RUN_FINISHED,
    thread_id=thread_id,
    run_id=run_id
))
```

### Frontend (TypeScript)

```typescript
// Send message and process event stream
await sendChatMessage(
  messages,
  threadId,
  runId,
  (event) => {
    // Process event through AG-UI client
    aguiClient.processEvent(event);
  }
);

// Register event handlers
const unsubscribe = aguiClient.on('TEXT_MESSAGE_CONTENT', (event) => {
  console.log('Received chunk:', event.delta);
});

// Clean up
unsubscribe();
```

## Event Flow Example

Typical conversation flow:

```
1. RUN_STARTED          → Agent run begins
2. TEXT_MESSAGE_START   → New assistant message
3. TEXT_MESSAGE_CONTENT → "Hello"
4. TEXT_MESSAGE_CONTENT → ", "
5. TEXT_MESSAGE_CONTENT → "world!"
6. TEXT_MESSAGE_END     → Message complete
7. RUN_FINISHED         → Agent run complete
```

## Benefits

### For Backend Developers
- **Standardized**: Use official SDK with type-safe events
- **Flexible**: Easy to add custom event types
- **Observable**: Clear visibility into agent execution
- **Testable**: Events can be captured and validated

### For Frontend Developers
- **Real-time**: UI updates as events arrive
- **Type-safe**: TypeScript interfaces for all events
- **Reactive**: Event-driven state updates
- **Composable**: Easy to build complex UIs from simple events

## Integration Points

### Backend Components
- [BaseAgent](../backend/agents/base-agent.md) - Agent base class with AG-UI integration
- [ChatAgent](../backend/agents/chat-agent.md) - Chat agent implementation
- [API Routes](../backend/api/routes.md) - FastAPI SSE endpoints

### Frontend Components
- [useAGUI Hook](../frontend/hooks/useAGUI.md) - React hook for AG-UI integration
- [AG-UI Client](../frontend/services/overview.md) - Client-side event processor
- [ChatContainer](../frontend/components/overview.md) - Chat UI with event handling

## Best Practices

### Backend
1. **Always emit RUN_STARTED first** - Signals beginning of agent execution
2. **Emit RUN_FINISHED or RUN_ERROR last** - Signals completion
3. **Use message IDs consistently** - Link related message events
4. **Handle errors gracefully** - Emit RUN_ERROR with descriptive messages
5. **Keep events small** - Stream content in reasonable chunks

### Frontend
1. **Handle all event types** - Gracefully handle unknown events
2. **Clean up subscriptions** - Unsubscribe when components unmount
3. **Show loading states** - Use RUN_STARTED to show progress
4. **Display errors clearly** - Handle RUN_ERROR events appropriately
5. **Buffer content** - Accumulate TEXT_MESSAGE_CONTENT chunks efficiently

## Troubleshooting

### Common Issues

**Events not received on frontend**
- Check SSE endpoint returns `Content-Type: text/event-stream`
- Verify events are properly formatted with `data:` prefix
- Ensure proper CORS configuration for SSE

**Duplicate events**
- Check event handlers aren't registered multiple times
- Verify cleanup of event subscriptions

**Message chunks out of order**
- Use message IDs to group related events
- Buffer chunks until TEXT_MESSAGE_END received

## Related Documentation

- [Backend Architecture](../architecture/backend-architecture.md)
- [Frontend Architecture](../architecture/frontend-architecture.md)
- [System Overview](../architecture/overview.md)

---

*For detailed event specifications, see [Protocol Specification](protocol-spec.md)*
