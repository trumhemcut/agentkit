# Canvas Mode Integration - Knowledge Base

## Overview
This document captures the knowledge and patterns from implementing canvas mode integration into the main chat using a unified TEXT_MESSAGE protocol.

## Core Concept

### Artifacts as Messages
Instead of treating artifacts as separate entities, they are now **messages with special metadata**:
- Regular messages: `metadata.message_type = "text"`
- Artifact messages: `metadata.message_type = "artifact"`

This unifies the chat experience and maintains chronological message order.

## Architecture Pattern

### Agent Specialization

```
ChatAgent
├── Purpose: Text-only conversations
├── Protocol: TEXT_MESSAGE events
└── Metadata: message_type = "text"

CanvasAgent
├── Purpose: Text + artifact generation
├── Protocol: TEXT_MESSAGE events (unified)
├── Intelligent routing: text vs artifact
└── Metadata: 
    ├── text: message_type = "text"
    └── artifact: message_type = "artifact" + artifact_type, language, title
```

### Unified Endpoint Pattern

```
POST /chat/{agent_id}

Routing:
├── /chat/chat-agent → ChatAgent
└── /chat/canvas-agent → CanvasAgent
```

**Benefits:**
- Single endpoint pattern for all agents
- Clear agent selection via path parameter
- Extensible for future agents
- No complex routing logic needed

## Protocol Design

### Event Stream Structure

All messages use the same event types:
1. `text_message_start` - Begin message (with metadata)
2. `text_message_content` - Stream content chunks
3. `text_message_end` - Complete message

**Metadata distinguishes message types:**
```typescript
// Text message
metadata: { message_type: "text" }

// Artifact message
metadata: {
  message_type: "artifact",
  artifact_type: "code" | "text" | "document",
  language: "python",  // for code
  title: "Artifact Title"
}
```

### Why This Works

1. **Single Source of Truth**: Message list contains everything
2. **Chronological Order**: Natural conversation flow maintained
3. **Type Safety**: Metadata provides structured type information
4. **Streaming Consistency**: Same mechanism for all content
5. **Frontend Simplicity**: One message handler, metadata-based routing

## Implementation Patterns

### Agent Implementation Pattern

```python
class Agent(BaseAgent):
    async def run(self, state) -> AsyncGenerator[BaseEvent, None]:
        # 1. Determine response type
        should_create_artifact = self._analyze_intent(state)
        
        if should_create_artifact:
            # 2a. Emit artifact message
            yield TextMessageStartEvent(
                message_id=msg_id,
                metadata={
                    "message_type": "artifact",
                    "artifact_type": self._detect_type(),
                    "language": self._detect_language(),
                    "title": "Generating..."
                }
            )
        else:
            # 2b. Emit text message
            yield TextMessageStartEvent(
                message_id=msg_id,
                metadata={"message_type": "text"}
            )
        
        # 3. Stream content (same for both)
        async for chunk in self.llm.astream(messages):
            yield TextMessageContentEvent(
                message_id=msg_id,
                delta=chunk.content
            )
        
        # 4. Complete message (same for both)
        yield TextMessageEndEvent(message_id=msg_id)
```

### Frontend Integration Pattern

```typescript
// 1. Message detection
if (event.type === 'text_message_start') {
  const messageType = event.metadata?.message_type || 'text';
  
  if (messageType === 'artifact') {
    // Activate canvas mode
    setCanvasMode(true);
  }
  
  // Add message to history (unified list)
  addMessage({
    id: event.message_id,
    messageType: messageType,
    // ... artifact metadata if present
  });
}

// 2. Content streaming (unified)
if (event.type === 'text_message_content') {
  updateMessageContent(event.message_id, event.delta);
}

// 3. Completion (unified)
if (event.type === 'text_message_end') {
  markMessageComplete(event.message_id);
}
```

## Key Learnings

### 1. Protocol Unification Benefits
- **Reduced Complexity**: One event type system instead of multiple
- **Better Maintainability**: Single code path for all messages
- **Improved Testing**: One protocol to test thoroughly
- **Frontend Simplicity**: Simpler event handling logic

### 2. Metadata-Driven Design
- **Flexible**: Easy to add new message types
- **Type-Safe**: Structured metadata schema
- **Discoverable**: Metadata makes capabilities clear
- **Extensible**: New fields can be added without breaking changes

### 3. Agent Specialization
- **ChatAgent**: Simple, focused on text
- **CanvasAgent**: Complex, handles both text and artifacts
- **Separation of Concerns**: Each agent has clear responsibility
- **Easy Testing**: Test each agent independently

### 4. Backward Compatibility
- **Gradual Migration**: Old endpoints still work
- **Deprecation Path**: Clear warnings and timeline
- **Risk Mitigation**: No sudden breaking changes
- **User Experience**: Seamless transition

## Common Patterns

### Pattern 1: Intelligent Agent Routing

```python
# Let the agent decide based on user intent
if "create" in user_message or "generate" in user_message:
    # Create artifact
    action = "create"
else:
    # Respond with text
    action = "text"
```

### Pattern 2: Artifact Type Detection

```python
def _detect_artifact_type(self, message: str) -> str:
    code_keywords = ["code", "function", "script", "program"]
    if any(kw in message.lower() for kw in code_keywords):
        return "code"
    return "text"
```

### Pattern 3: Language Detection

```python
def _detect_language(self, message: str, code: str) -> str:
    # Check explicit mentions
    if "python" in message.lower():
        return "python"
    
    # Analyze code syntax
    if "def " in code or "import " in code:
        return "python"
    elif "function" in code or "const" in code:
        return "javascript"
    
    return "python"  # default
```

### Pattern 4: Unified Content Streaming

```python
# Same streaming logic for text and artifacts
async for chunk in self.llm.astream(messages):
    if chunk.content:
        yield TextMessageContentEvent(
            message_id=message_id,
            delta=chunk.content
        )
```

## Best Practices

### 1. Metadata Usage
- ✅ Use metadata for message type identification
- ✅ Include all relevant artifact information in START event
- ✅ Keep metadata structure consistent across agents
- ❌ Don't put streaming content in metadata

### 2. Event Emission
- ✅ Always emit START → CONTENT (streaming) → END sequence
- ✅ Use same event types for all message types
- ✅ Include message_id in all related events
- ❌ Don't skip END event even on errors

### 3. Agent Implementation
- ✅ Let agent decide message type based on intent
- ✅ Support both text and artifact responses when appropriate
- ✅ Use consistent metadata structure
- ❌ Don't hardcode message types without analysis

### 4. Error Handling
- ✅ Emit RUN_ERROR events on failures
- ✅ Include descriptive error messages
- ✅ Log errors for debugging
- ❌ Don't leave streams hanging without END event

## Testing Strategies

### Unit Tests
```python
# Test agent emits correct events
async def test_agent_events():
    agent = CanvasAgent()
    events = [e async for e in agent.run(state)]
    
    # Verify event sequence
    assert events[0].type == EventType.TEXT_MESSAGE_START
    assert events[-1].type == EventType.TEXT_MESSAGE_END
    
    # Verify metadata
    start_event = events[0]
    assert start_event.metadata["message_type"] in ["text", "artifact"]
```

### Integration Tests
```python
# Test endpoint with actual requests
def test_endpoint():
    response = requests.post(
        f"{BASE_URL}/api/chat/canvas-agent",
        json={"messages": [{"role": "user", "content": "Create code"}]},
        stream=True
    )
    
    # Parse SSE events
    events = parse_sse_stream(response)
    
    # Verify artifact message
    start = next(e for e in events if e["type"] == "text_message_start")
    assert start["metadata"]["message_type"] == "artifact"
```

### Manual Testing
```bash
# Test with curl
curl -X POST http://localhost:8000/api/chat/canvas-agent \
  -H "Accept: text/event-stream" \
  -d '{"messages":[{"role":"user","content":"Create a Python function"}]}'
```

## Troubleshooting Guide

### Issue: Canvas mode not activating

**Symptoms:**
- Artifact content appears as text
- Canvas panel doesn't show

**Solutions:**
1. Check TEXT_MESSAGE_START metadata contains `message_type: "artifact"`
2. Verify frontend detects metadata correctly
3. Check console for parsing errors

### Issue: Content not streaming

**Symptoms:**
- No content appears during generation
- Only shows after completion

**Solutions:**
1. Verify TEXT_MESSAGE_CONTENT events are emitted
2. Check SSE connection is maintained
3. Ensure frontend updates on CONTENT events

### Issue: Wrong agent behavior

**Symptoms:**
- ChatAgent creating artifacts
- CanvasAgent only doing text

**Solutions:**
1. Verify correct agent_id in request
2. Check agent routing in endpoint
3. Review intent detection logic

## Future Enhancements

### 1. Enhanced Artifact Types
- Images, diagrams, charts
- Interactive components
- Data tables, CSV
- 3D models

### 2. Artifact Operations
- Version history
- Editing capabilities
- Artifact forking
- Collaborative editing

### 3. Agent Capabilities
- Multi-agent collaboration
- Agent composition
- Dynamic tool usage
- Context sharing

### 4. Protocol Extensions
- Partial updates (diffs)
- Binary content support
- Structured data artifacts
- Real-time collaboration events

## References

- [Implementation Plan](../../.docs/1-implementation-plans/canvas-mode-for-main-chat.md)
- [Changelog](../CANVAS_INTEGRATION_CHANGELOG.md)
- [Quick Reference](../CANVAS_INTEGRATION_QUICKREF.md)
- [Backend Patterns](../../.github/agents/backend.agent.md)

## Version History

- **v1.0** (2025-12-24): Initial implementation
  - Unified TEXT_MESSAGE protocol
  - Agent specialization (ChatAgent, CanvasAgent)
  - Single endpoint pattern (/chat/{agent_id})
  - Metadata-driven artifact detection
  - Backward compatibility support

---

**Last Updated:** December 24, 2025
**Maintained By:** Backend Agent
