# Implementation Plan: Canvas Mode for Main Chat

## Overview
Integrate canvas mode into the main chat page (`app/page.tsx`) to support artifact rendering alongside chat messages. This unifies the chat experience by allowing agents to dynamically generate artifacts (code, documents) within a single thread, with the frontend adapting its layout based on agent responses.

## Requirements Summary
- Enable canvas mode in main chat when artifacts are generated
- Dynamic layout: Chat container (1/3 width) + Artifact panel (2/3 width) when canvas active
- Sidebar collapses when canvas mode is active
- Single unified chat thread (no separate canvas/chat threads)
- Agent decides whether to return artifacts (backend-driven)
- Real-time artifact streaming with custom events

## Architecture Changes

### State Management
- Unified thread model: Remove distinction between chat and canvas threads
- Canvas mode activation: Triggered by artifact events from backend
- Layout state: Track sidebar collapse and panel width distribution

### Event Stream Protocol
Single unified message stream with metadata distinguishing types:

**All Messages** (text and artifacts):
- `TEXT_MESSAGE_START` (with `metadata.message_type` to identify artifacts)
- `TEXT_MESSAGE_CONTENT` 
- `TEXT_MESSAGE_END`

**Key Difference:**
- Regular text message: `metadata.message_type = "text"` (or omitted)
- Artifact message: `metadata.message_type = "artifact"` + artifact metadata
  - Canvas mode activates when artifact message detected
  - Artifact appears in message list at correct chronological position

---

## Implementation Tasks

### 1. Backend Tasks (LangGraph + AG-UI)
> **Delegate to Backend Agent** - See [backend.agent.md](../../../.github/agents/backend.agent.md)

#### 1.1 Agent State Schema Updates
- [ ] Update message model to support artifact type messages
- [ ] Extend existing message schema to include artifact fields:
  ```python
  class Message:
      role: str  # "user", "assistant", "system"
      content: str
      message_type: str  # "text", "artifact"
      
      # Artifact-specific fields (only when message_type="artifact")
      artifact_type: Optional[str]  # "code", "text", "document"
      language: Optional[str]  # for code artifacts
      title: Optional[str]
      streaming: bool = False
  ```
- [ ] Messages with `message_type="artifact"` will trigger canvas mode
- [ ] Maintain chronological order: artifacts appear in message list at correct position

#### 1.2 Message Event Emission (Artifacts as Messages)
- [ ] Emit standard message events with artifact metadata
- [ ] Use `TEXT_MESSAGE_START` with artifact indicator:
  ```python
  {
    "type": "text_message_start",
    "message_id": "...",
    "metadata": {
      "message_type": "artifact",
      "artifact_type": "code",
      "language": "python",
      "title": "Generated Script"
    }
  }
  ```
- [ ] Stream content with `TEXT_MESSAGE_CONTENT`:
  ```python
  {
    "type": "text_message_content",
    "message_id": "...",
    "content": "chunk..."
  }
  ```
- [ ] Complete with `TEXT_MESSAGE_END`:
  ```python
  {
    "type": "text_message_end",
    "message_id": "..."
  }
  ```
- [ ] Frontend detects artifact via `metadata.message_type="artifact"` in START event
- [ ] This maintains chronological order in message stream

#### 1.3 Agent Logic Updates
- [ ] Keep `ChatAgent` for text-only conversations (simple use case)
- [ ] Keep `CanvasAgent` for artifact-capable conversations (complex use case)
- [ ] Both agents emit messages with `message_type` metadata field
- [ ] `ChatAgent`: Always emits `message_type: "text"`
- [ ] `CanvasAgent`: Intelligently decides between `message_type: "text"` or `"artifact"` based on context
- [ ] Agent determines `message_type`, `artifact_type`, `language`, `title` in metadata
- [ ] All agents use TEXT_MESSAGE_START/CONTENT/END (unified protocol)
- [ ] Test with `qwen:7b` model (default Ollama provider)

#### 1.4 API Endpoint Updates
- [ ] **Single unified endpoint**: `/chat/{agent_id}` handles all agents
- [ ] **Remove** `/canvas/{agent_id}` endpoint (no longer needed)
- [ ] Endpoint routes to appropriate agent based on `agent_id`:
  - `/chat/chat-agent` → `ChatAgent` (text only)
  - `/chat/canvas-agent` → `CanvasAgent` (text + artifacts)
- [ ] All agents emit TEXT_MESSAGE_START/CONTENT/END with metadata
- [ ] Ensure SSE streaming includes metadata field for message type identification
- [ ] Update response models in `api/models.py` if needed
- [ ] Simplify routing logic - agent_id is the only variable

---

### 2. Protocol Definition (AG-UI)
> **Communication contract between backend and frontend**

#### 2.1 Event Format Specifications

**Message Events (Unified for Text and Artifacts):**

All messages use the same event types: `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END`

**Artifact Message Start:**
```typescript
{
  type: 'text_message_start',
  message_id: string,
  metadata: {
    message_type: 'artifact',  // Key field to trigger canvas mode
    artifact_type: 'code' | 'text' | 'document',
    language?: string,
    title: string
  }
}
```

**Content Streaming (Same for Both):**
```typescript
{
  type: 'text_message_content',
  message_id: string,
  content: string  // Chunk of content
}
```

**Message End (Same for Both):**
```typescript
{
  type: 'text_message_end',
  message_id: string
}
```

**Regular Text Message Start (for comparison):**
```typescript
{
  type: 'text_message_start',
  message_id: string,
  metadata: {
    message_type: 'text'  // Regular message, no canvas activation
  }
}
```

#### 2.2 State Synchronization
- Canvas mode activation: Triggered when `TEXT_MESSAGE_START` has `metadata.message_type="artifact"`
- Canvas mode deactivation: Manual user action or end of session
- Layout state: Maintained in frontend context
- Message ordering: Artifacts appear in message list at correct chronological position

---

### 3. Frontend Tasks (NextJS + AG-UI)
> **Delegate to Frontend Agent** - See [frontend.agent.md](../../../.github/agents/frontend.agent.md)

#### 3.1 State Management Refactoring

**Unified Message Model:**
- [ ] Remove `useChatThreads` hook distinction between thread types
- [ ] Remove separate canvas page `/app/canvas/page.tsx` (no longer needed)
- [ ] Update `services/storage.ts` to use single thread model with unified messages
- [ ] Migrate existing canvas threads to unified thread format
- [ ] Frontend always uses `/chat/{agent_id}` endpoint
- [ ] Agent selection determines behavior (ChatAgent vs CanvasAgent)

**Add Canvas Mode State:**
- [ ] Create `useCanvasMode` hook:
  ```typescript
  interface CanvasMode {
    isActive: boolean,
    currentArtifactMessage: Message | null,  // The message that is an artifact
    activateCanvas: (message: Message) => void,
    deactivateCanvas: () => void
  }
  ```
- [ ] Integrate with existing `useMessages` hook
- [ ] Artifacts are just messages with `messageType: 'artifact'`
- [ ] No separate artifacts array - everything in messages list

#### 3.2 Layout Component Updates

**Update `app/page.tsx`:**
- [ ] Add conditional layout based on canvas mode state
- [ ] Implement dynamic width distribution:
  - Canvas inactive: Full-width chat container
  - Canvas active: Chat (33%) + Artifact Panel (67%)
- [ ] Collapse sidebar when canvas mode is active
- [ ] Smooth transitions between layouts (CSS animations)

**Layout Structure:**
```tsx
<Layout>
  <Sidebar collapsed={canvasMode.isActive} />
  <div className={canvasMode.isActive ? "grid grid-cols-3" : "flex-1"}>
    <div className={canvasMode.isActive ? "col-span-1" : "w-full"}>
      <ChatContainer messages={messages} />
    </div>
    {canvasMode.isActive && canvasMode.currentArtifactMessage && (
      <div className="col-span-2">
        <ArtifactPanel message={canvasMode.currentArtifactMessage} />
      </div>
    )}
  </div>
</Layout>
```

Note: `messages` array contains ALL messages (text + artifacts) in chronological order

#### 3.3 Event Handler Implementation

**Update `useAGUI` or `useMessages` hook:**
- [ ] Handle `TEXT_MESSAGE_START` with artifact detection:
  ```typescript
  case 'text_message_start':
    const isArtifact = event.metadata?.message_type === 'artifact';
    
    if (isArtifact) {
      // Activate canvas mode
      activateCanvas();
      
      // Add artifact message to message list
      addMessage({
        id: event.message_id,
        role: 'assistant',
        content: '',
        messageType: 'artifact',
        artifactType: event.metadata.artifact_type,
        language: event.metadata.language,
        title: event.metadata.title,
        streaming: true
      });
    } else {
      // Regular message
      addMessage({
        id: event.message_id,
        role: 'assistant',
        content: '',
        messageType: 'text',
        streaming: true
      });
    }
    break;
  ```
- [ ] Handle `TEXT_MESSAGE_CONTENT` same way for both artifact and text messages
- [ ] All messages in single chronological list
- [ ] Canvas displays the last artifact message in the list

**Streaming Handler Logic:**
```typescript
const handleMessageContent = (event: TextMessageContentEvent) => {
  setMessages(prev => 
    prev.map(msg => 
      msg.id === event.message_id
        ? { ...msg, content: msg.content + event.content }
        : msg
    )
  );
};
```

#### 3.4 Component Updates

**Reuse Existing Canvas Components:**
- [ ] Use `CanvasLayout` component as artifact panel container
- [ ] Use `ArtifactRenderer` for displaying artifacts
- [ ] Use `CodeRenderer` for code artifacts
- [ ] Use `TextRenderer` for text/document artifacts
- [ ] Ensure components support real-time content updates

**Update `ChatContainer`:**
- [ ] Add responsive width adjustments
- [ ] Maintain scroll behavior in narrow mode
- [ ] Update message bubble styling for narrow layout

**Create `ArtifactPanel` Component:**
- [ ] Accepts a `Message` prop (where `message.messageType === 'artifact'`)
- [ ] Wrapper around existing `ArtifactRenderer`
- [ ] Add header with artifact title and type indicator
- [ ] Add loading state during streaming
- [ ] Add error boundaries for render failures
- [ ] Render based on `message.content`, `message.artifactType`, `message.language`

#### 3.5 TypeScript Type Updates

**Update Message Types:**
```typescript
// types/chat.ts
export type MessageType = 'text' | 'artifact';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  messageType: MessageType;
  
  // Artifact-specific fields (only when messageType === 'artifact')
  artifactType?: 'code' | 'text' | 'document';
  language?: string;  // for code artifacts
  title?: string;
  
  streaming?: boolean;
  createdAt: Date;
  updatedAt?: Date;
}

// Helper type guard
export function isArtifactMessage(message: Message): boolean {
  return message.messageType === 'artifact';
}
```

**Update AGUI Event Types:**
```typescript
// types/agui.ts
export interface TextMessageStartEvent {
  type: 'text_message_start';
  message_id: string;
  metadata?: {
    message_type?: 'text' | 'artifact';
    artifact_type?: 'code' | 'text' | 'document';
    language?: string;
    title?: string;
  };
}

export interface TextMessageContentEvent {
  type: 'text_message_content';
  message_id: string;
  content: string;
}

export interface TextMessageEndEvent {
  type: 'text_message_end';
  message_id: string;
}
```

#### 3.6 Storage Updates
- [ ] Update `services/storage.ts` to store all messages in single list
- [ ] Save canvas mode state in thread metadata
- [ ] Simplified thread structure:
  ```typescript
  interface StoredThread {
    id: string;
    messages: Message[];  // Contains both text and artifact messages
    canvasModeActive: boolean;
    // ... other fields
  }
  ```
- [ ] Artifacts are identified by `message.messageType === 'artifact'`
- [ ] No separate artifacts array needed

---

## Integration & Testing

### Integration Points
1. **Backend → Frontend**: SSE stream with unified message events (metadata distinguishes artifacts)
2. **State Synchronization**: Canvas mode activation when artifact message detected
3. **Message Ordering**: Artifacts appear in message list at correct chronological position
4. **Component Communication**: Both chat container and artifact panel read from same message list

### Testing Checklist

#### Backend Testing
- [ ] Test `/chat/chat-agent` endpoint - verify text-only messages
- [ ] Test `/chat/canvas-agent` endpoint - verify text + artifact messages
- [ ] Verify streaming chunks use standard TEXT_MESSAGE_CONTENT events for both agents
- [ ] Test parallel regular text and artifact messages in same session (CanvasAgent)
- [ ] Validate event format matches protocol spec for both agents
- [ ] Ensure artifacts maintain chronological order in message stream
- [ ] Verify `/canvas` endpoint is removed/deprecated
- [ ] Verify `CanvasAgent` no longer emits custom artifact events

#### Frontend Testing
- [ ] Test layout transitions (chat-only → canvas mode)
- [ ] Verify sidebar collapse behavior
- [ ] Test real-time artifact streaming display
- [ ] Verify message history maintains chronological order (artifacts inline)
- [ ] Test artifact persistence in storage as messages
- [ ] Test responsive behavior (mobile, tablet, desktop)
- [ ] Verify chat container shows all messages including artifacts
- [ ] Test canvas panel displays selected artifact message

#### End-to-End Testing
- [ ] Create test scenario: User asks agent to generate code
- [ ] Verify agent decision to return artifact message
- [ ] Confirm canvas mode activates automatically when artifact message appears
- [ ] Validate streaming updates in artifact panel
- [ ] Test multiple artifacts in same chat session (chronological order maintained)
- [ ] Test conversation flow: text → artifact → text → artifact
- [ ] Verify artifacts appear inline in message history
- [ ] Test switching between threads with/without artifacts

---

## Migration Plan

### Phase 1: Backend Foundation
1. Implement artifact message schema (message with artifact metadata)
2. Add message event emission with artifact indicator in metadata
3. Update `CanvasAgent` to emit standard TEXT_MESSAGE events (remove custom events)
4. Keep `ChatAgent` text-only, `CanvasAgent` supports text + artifacts
5. Consolidate to single `/chat/{agent_id}` endpoint
6. Remove `/canvas` endpoint and routing
7. Test with unified endpoint pattern

### Phase 2: Protocol & Types
1. Define TypeScript message types with artifact variant
2. Update AGUI event type definitions
3. Document protocol in codebase

### Phase 3: Frontend Core
1. Update message model to support artifact type
2. Implement canvas mode state management
3. Add artifact message detection in event handlers
4. Update storage layer (unified message list)

### Phase 4: UI Implementation
1. Update main chat page layout (remove separate canvas page)
2. Integrate artifact panel components into main chat (accept Message prop)
3. Add sidebar collapse behavior
4. Implement CSS transitions
5. Ensure message history shows all messages in order
6. Update agent selection to use single `/chat/{agent_id}` endpoint

### Phase 5: Testing & Refinement
1. Backend unit tests
2. Frontend component tests
3. E2E integration testing (verify chronological order)
4. Performance optimization
5. User experience refinement

---

## Dependencies

### External Dependencies
- No new dependencies required (reuse existing AG-UI, LangGraph, Shadcn UI)

### Internal Dependencies
- Backend artifact message logic must be complete before frontend integration
- Protocol definition must be finalized before parallel implementation
- Existing canvas components (`ArtifactRenderer`, `CodeRenderer`) ready for reuse in main chat
- Agent routing logic in `/chat/{agent_id}` endpoint
- Migration plan for existing `/canvas` endpoint users
- Update frontend to remove canvas page and routing

---

## Success Criteria

- ✅ Single message list contains both text and artifact messages in chronological order
- ✅ Artifacts are messages with `messageType: 'artifact'`
- ✅ Canvas mode activates automatically when agent generates artifact message
- ✅ Layout transitions smoothly between chat-only and canvas modes
- ✅ Real-time artifact streaming displays chunk-by-chunk
- ✅ Sidebar collapses when canvas mode is active
- ✅ Artifacts persist as messages in chat history
- ✅ No breaking changes to existing chat functionality
- ✅ Backend agent decides artifact generation (not frontend)
- ✅ Message ordering maintained: text, artifact, text, artifact flow works correctly

---

## Notes

### Design Considerations
- **Agent-Driven**: Backend determines when to create artifact messages based on user intent
- **Unified Experience**: No mental model split between "chat" and "canvas" modes
- **Progressive Enhancement**: Chat works normally until artifact messages appear
- **Reusable Components**: Leverage existing canvas components in main chat
- **Chronological Integrity**: Artifacts are messages, maintaining natural conversation flow
- **Single Source of Truth**: One message list contains everything in order
- **Unified Protocol**: Both `ChatAgent` and `CanvasAgent` use same event protocol
- **Single Endpoint Pattern**: `/chat/{agent_id}` routes to appropriate agent
- **Agent Specialization**: ChatAgent (simple), CanvasAgent (complex) - separation of concerns

### Future Enhancements
- Multiple artifacts visible simultaneously (tabs/accordion)
- Artifact editing capabilities
- Artifact export functionality
- Artifact version history

---

## References
- Requirement: `/.docs/0-requirements/007-canvasmode-for-mainchat.md`
- Backend Patterns: `/.github/agents/backend.agent.md`
- Frontend Patterns: `/.github/agents/frontend.agent.md`
- Existing Canvas Implementation: `/app/canvas/page.tsx`
- AG-UI Protocol: `/backend/protocols/event_types.py`
