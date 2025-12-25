# Partial Content Editing Implementation Plan

## Overview
Enable users to select a portion of content in Canvas mode and ask the agent to edit only that specific section. The agent should return the edited portion, and the frontend needs to stream and apply the changes to the correct region within the overall content in the canvas.

## Key Capabilities
1. **Text Selection**: User can select any portion of text/code in canvas artifact
2. **Contextual Editing**: Agent receives selected text + surrounding context for editing
3. **Partial Streaming**: Agent streams only the edited portion, not the entire artifact
4. **Smart Merging**: Frontend intelligently replaces the selected region with streamed content
5. **Version Tracking**: Each partial edit creates a new version in artifact history

## Architecture Flow

```
User selects text in Canvas
    ↓
Frontend captures selection (start, end, text)
    ↓
User sends edit request with selectedText context
    ↓
Backend receives: {messages, artifact, selectedText, artifactAction: "partial_update"}
    ↓
Agent generates edited portion with context awareness
    ↓
Backend streams: PARTIAL_EDIT_START → PARTIAL_EDIT_CHUNK → PARTIAL_EDIT_END
    ↓
Frontend merges streamed content into artifact at correct position
    ↓
Canvas updates with new version
```

---

## 1. Backend Implementation (LangGraph + AG-UI)

### 1.1 State Schema Updates
**File**: `backend/graphs/canvas_graph.py`

**Current State**: `SelectedText` TypedDict already exists with `start`, `end`, `text` fields.

**Enhancement**: Add partial edit tracking in `CanvasGraphState`:

```python
class CanvasGraphState(TypedDict):
    """Extended state for canvas feature"""
    messages: List[Dict[str, str]]
    thread_id: str
    run_id: str
    artifact: Optional[ArtifactV3]
    selectedText: Optional[SelectedText]
    artifactAction: Optional[str]  # "create", "update", "rewrite", "partial_update"
    partialEdit: Optional['PartialEdit']  # NEW: tracks partial edit result

class PartialEdit(TypedDict):
    """Result of partial content editing"""
    originalStart: int
    originalEnd: int
    newContent: str
    contentType: Literal["code", "text"]
```

**Implementation Steps**:
1. Add `PartialEdit` TypedDict to track edit boundaries and new content
2. Update `artifactAction` to include `"partial_update"` option
3. Add `partialEdit` field to `CanvasGraphState`

---

### 1.2 Intent Detection Enhancement
**File**: `backend/graphs/canvas_graph.py` → `detect_intent_node()`

**Current Behavior**: Detects "create", "update", "rewrite" based on keywords

**Enhancement**: Detect partial editing when `selectedText` is present

```python
def detect_intent_node(state: CanvasGraphState) -> CanvasGraphState:
    """Classify if message requires artifact manipulation"""
    
    if not state["messages"]:
        return state
    
    last_message = state["messages"][-1]["content"].lower()
    artifact = state.get("artifact")
    selected_text = state.get("selectedText")
    
    # NEW: Check for partial editing
    if artifact and selected_text:
        # User has selected text in existing artifact - this is partial editing
        state["artifactAction"] = "partial_update"
        logger.info(f"Detected partial_update: selection from {selected_text['start']} to {selected_text['end']}")
        return state
    
    # ... existing logic for create/update/rewrite
    
    return state
```

**Implementation Steps**:
1. Check for presence of both `artifact` and `selectedText`
2. Set `artifactAction = "partial_update"` when selection exists
3. Log selection boundaries for debugging

---

### 1.3 Canvas Agent - Partial Update Handler
**File**: `backend/agents/canvas_agent.py`

**Enhancement**: Add `_partial_update_artifact()` method to handle selected text editing

```python
class CanvasAgent(BaseAgent):
    
    async def run(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """Stream events for artifact creation/modification"""
        
        action = state.get("artifactAction", None)
        
        # ... existing code ...
        
        # NEW: Handle partial update
        if action == "partial_update":
            async for event in self._partial_update_artifact(state):
                yield event
        # ... rest of actions ...
    
    async def _partial_update_artifact(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
        """
        Edit only the selected portion of artifact content.
        Streams the edited portion for frontend to merge.
        """
        messages = state["messages"]
        artifact = state["artifact"]
        selected_text = state["selectedText"]
        
        if not artifact or not selected_text:
            logger.error("partial_update called without artifact or selectedText")
            return
        
        current_content = artifact["contents"][artifact["currentIndex"]]
        content_type = current_content["type"]
        
        # Get full content for context
        full_content = current_content.get("code") if content_type == "code" else current_content.get("fullMarkdown")
        
        # Extract surrounding context (e.g., 200 chars before and after)
        start_pos = max(0, selected_text["start"] - 200)
        end_pos = min(len(full_content), selected_text["end"] + 200)
        context_before = full_content[start_pos:selected_text["start"]]
        context_after = full_content[selected_text["end"]:end_pos]
        
        # Build prompt with context
        edit_prompt = self._build_partial_edit_prompt(
            selected_text=selected_text["text"],
            context_before=context_before,
            context_after=context_after,
            user_request=messages[-1]["content"],
            content_type=content_type
        )
        
        # Emit PARTIAL_EDIT_START custom event
        yield CustomEvent(
            type=EventType.CUSTOM,
            custom_type="partial_edit_start",
            data={
                "originalStart": selected_text["start"],
                "originalEnd": selected_text["end"],
                "contentType": content_type
            }
        )
        
        # Stream edited content from LLM
        edited_content = ""
        async for chunk in self.llm.astream([{"role": "user", "content": edit_prompt}]):
            content = chunk.content
            if content:
                edited_content += content
                # Emit PARTIAL_EDIT_CHUNK
                yield CustomEvent(
                    type=EventType.CUSTOM,
                    custom_type="partial_edit_chunk",
                    data={"delta": content}
                )
        
        # Emit PARTIAL_EDIT_END with full edited content
        yield CustomEvent(
            type=EventType.CUSTOM,
            custom_type="partial_edit_end",
            data={
                "editedContent": edited_content,
                "originalStart": selected_text["start"],
                "originalEnd": selected_text["end"]
            }
        )
        
        # Store partial edit result in state for finalization
        state["partialEdit"] = {
            "originalStart": selected_text["start"],
            "originalEnd": selected_text["end"],
            "newContent": edited_content,
            "contentType": content_type
        }
    
    def _build_partial_edit_prompt(
        self, 
        selected_text: str, 
        context_before: str, 
        context_after: str,
        user_request: str,
        content_type: str
    ) -> str:
        """Build LLM prompt for partial editing with context"""
        
        prompt = f"""You are editing a portion of a {content_type} artifact.

**Context Before:**
```
{context_before}
```

**Selected Text to Edit:**
```
{selected_text}
```

**Context After:**
```
{context_after}
```

**User's Edit Request:**
{user_request}

**Instructions:**
- Only output the edited version of the selected text
- Maintain consistency with surrounding context
- Preserve formatting style (indentation, syntax)
- Do NOT include the context before/after, only the edited portion
- Do NOT add explanations, just the edited content

**Edited Content:**
"""
        return prompt
```

**Implementation Steps**:
1. Add `partial_update` case to `run()` method's action routing
2. Implement `_partial_update_artifact()` to:
   - Extract selected text and surrounding context
   - Build prompt with context awareness
   - Stream edited content chunk by chunk
   - Emit custom events: `partial_edit_start`, `partial_edit_chunk`, `partial_edit_end`
3. Implement `_build_partial_edit_prompt()` to construct context-aware prompt
4. Store `partialEdit` result in state for graph finalization

---

### 1.4 Graph Finalization Node
**File**: `backend/graphs/canvas_graph.py` → `update_artifact_node()`

**Enhancement**: Apply partial edit to create new artifact version

```python
def update_artifact_node(state: CanvasGraphState) -> CanvasGraphState:
    """Finalize artifact updates, including partial edits"""
    
    partial_edit = state.get("partialEdit")
    
    if partial_edit:
        # Apply partial edit to create new version
        artifact = state["artifact"]
        current_content = artifact["contents"][artifact["currentIndex"]]
        content_type = current_content["type"]
        
        # Get full content
        if content_type == "code":
            full_content = current_content["code"]
        else:
            full_content = current_content["fullMarkdown"]
        
        # Replace selected region with new content
        new_full_content = (
            full_content[:partial_edit["originalStart"]] +
            partial_edit["newContent"] +
            full_content[partial_edit["originalEnd"]:]
        )
        
        # Create new version
        new_index = len(artifact["contents"])
        if content_type == "code":
            new_version = {
                "index": new_index,
                "type": "code",
                "title": current_content["title"],
                "code": new_full_content,
                "language": current_content["language"]
            }
        else:
            new_version = {
                "index": new_index,
                "type": "text",
                "title": current_content["title"],
                "fullMarkdown": new_full_content
            }
        
        artifact["contents"].append(new_version)
        artifact["currentIndex"] = new_index
        
        logger.info(f"Created new artifact version {new_index} from partial edit")
        
        # Clear partial edit from state
        state["partialEdit"] = None
    
    return state
```

**Implementation Steps**:
1. Check for `partialEdit` in state
2. Extract full content from current artifact version
3. Splice new content: `before + edited + after`
4. Create new artifact version with spliced content
5. Update `artifact.currentIndex` to new version
6. Clear `partialEdit` from state

---

### 1.5 Custom Event Types
**File**: `backend/protocols/event_types.py`

**Enhancement**: Add partial editing event types

```python
class CanvasEventType:
    """Canvas-specific event type constants"""
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_STREAMING = "artifact_streaming"
    ARTIFACT_STREAMING_START = "artifact_streaming_start"
    ARTIFACT_VERSION_CHANGED = "artifact_version_changed"
    SELECTION_CONTEXT = "selection_context"
    THINKING = "thinking"
    
    # NEW: Partial editing events
    PARTIAL_EDIT_START = "partial_edit_start"
    PARTIAL_EDIT_CHUNK = "partial_edit_chunk"
    PARTIAL_EDIT_END = "partial_edit_end"
```

**Implementation Steps**:
1. Add three new event type constants for partial editing lifecycle
2. Document event payload schemas in comments

---

### 1.6 API Route Updates
**File**: `backend/api/models.py`

**Current State**: `CanvasChatRequest` already has `selectedText` field

**Verification**: Ensure `selectedText` is properly passed from API to graph state

```python
class CanvasChatRequest(BaseModel):
    thread_id: str
    message: str
    artifact: Optional[ArtifactV3Schema] = None
    selectedText: Optional[SelectedText] = None  # Already exists ✓
    model: Optional[str] = None
    agent: Optional[str] = "canvas"
```

**No changes needed** - the API already supports receiving `selectedText`.

---

## 2. Frontend Implementation (AG-UI + React)

### 2.1 Text Selection Tracking
**File**: `frontend/components/Canvas/TextRenderer.tsx` and `CodeRenderer.tsx`

**Enhancement**: Capture user text selection and expose via callback

#### TextRenderer.tsx

```typescript
interface TextRendererProps {
  markdown: string
  isStreaming: boolean
  onUpdate: (newMarkdown: string) => void
  onTextSelect?: (selection: SelectedText) => void  // NEW
}

export function TextRenderer({ 
  markdown, 
  isStreaming, 
  onUpdate,
  onTextSelect 
}: TextRendererProps) {
  const contentRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection()
      if (!selection || selection.isCollapsed) return
      
      const selectedText = selection.toString()
      if (!selectedText.trim()) return
      
      // Calculate position in markdown string
      const range = selection.getRangeAt(0)
      const container = contentRef.current
      if (!container) return
      
      // Get text before selection to calculate start position
      const preRange = document.createRange()
      preRange.setStart(container, 0)
      preRange.setEnd(range.startContainer, range.startOffset)
      const textBefore = preRange.toString()
      
      const start = textBefore.length
      const end = start + selectedText.length
      
      onTextSelect?.({
        start,
        end,
        text: selectedText
      })
    }
    
    document.addEventListener('mouseup', handleSelection)
    return () => document.removeEventListener('mouseup', handleSelection)
  }, [markdown, onTextSelect])
  
  // ... rest of component
}
```

#### CodeRenderer.tsx

```typescript
interface CodeRendererProps {
  code: string
  language: string
  isStreaming: boolean
  onUpdate: (newCode: string) => void
  onTextSelect?: (selection: SelectedText) => void  // NEW
}

export function CodeRenderer({ 
  code, 
  language, 
  isStreaming, 
  onUpdate,
  onTextSelect 
}: CodeRendererProps) {
  const editorRef = useRef<any>(null)
  
  useEffect(() => {
    if (!editorRef.current) return
    
    const editor = editorRef.current
    
    // Listen for Monaco editor selection changes
    const disposable = editor.onDidChangeCursorSelection((e: any) => {
      const selection = e.selection
      if (selection.isEmpty()) return
      
      const model = editor.getModel()
      if (!model) return
      
      const start = model.getOffsetAt(selection.getStartPosition())
      const end = model.getOffsetAt(selection.getEndPosition())
      const selectedText = model.getValueInRange(selection)
      
      onTextSelect?.({
        start,
        end,
        text: selectedText
      })
    })
    
    return () => disposable.dispose()
  }, [onTextSelect])
  
  // ... rest of component
}
```

**Implementation Steps**:
1. Add `onTextSelect` callback prop to both renderers
2. In `TextRenderer`: Listen to `mouseup` events, calculate selection position in markdown string
3. In `CodeRenderer`: Use Monaco editor's `onDidChangeCursorSelection` event
4. Call `onTextSelect` with `{start, end, text}` when selection changes
5. Handle edge cases: empty selections, collapsed ranges

---

### 2.2 Selection State Management
**File**: `frontend/hooks/useCanvasChat.ts`

**Enhancement**: Track selected text and include in API requests

```typescript
export function useCanvasChat(threadId: string) {
  const [selectedText, setSelectedText] = useState<SelectedText | null>(null)
  
  // ... existing state ...
  
  const handleTextSelect = useCallback((selection: SelectedText) => {
    console.log('Text selected:', selection)
    setSelectedText(selection)
  }, [])
  
  const handleSendMessage = async (content: string) => {
    // ... existing code ...
    
    // Include selectedText in request if present
    const requestPayload = {
      thread_id: threadId,
      message: content,
      artifact: artifact || undefined,
      selectedText: selectedText || undefined,  // NEW
      model: currentModel || undefined,
      agent: "canvas"
    }
    
    // Clear selection after sending
    setSelectedText(null)
    
    // ... rest of send logic ...
  }
  
  return {
    // ... existing returns ...
    selectedText,
    handleTextSelect,
    // ... rest of returns ...
  }
}
```

**Implementation Steps**:
1. Add `selectedText` state to track current selection
2. Add `handleTextSelect` callback to update selection state
3. Include `selectedText` in API request payload
4. Clear selection after message is sent
5. Expose `handleTextSelect` for components to call

---

### 2.3 Partial Edit Event Handling
**File**: `frontend/hooks/useCanvasChat.ts` → AG-UI event handling

**Enhancement**: Handle partial editing events and merge content

```typescript
export function useCanvasChat(threadId: string) {
  const [partialEditBuffer, setPartialEditBuffer] = useState<string>("")
  const [partialEditBounds, setPartialEditBounds] = useState<{start: number, end: number} | null>(null)
  
  // ... existing state ...
  
  const handleAGUIEvent = useCallback((event: AGUIEvent) => {
    console.log('AGUI Event:', event)
    
    switch (event.type) {
      // ... existing cases ...
      
      case 'custom':
        const customEvent = event as CustomAGUIEvent
        
        switch (customEvent.custom_type) {
          case 'partial_edit_start':
            // Initialize partial edit streaming
            setPartialEditBuffer("")
            setPartialEditBounds({
              start: customEvent.data.originalStart,
              end: customEvent.data.originalEnd
            })
            setIsStreaming(true)
            console.log('Partial edit started:', customEvent.data)
            break
          
          case 'partial_edit_chunk':
            // Accumulate streamed content
            setPartialEditBuffer(prev => prev + customEvent.data.delta)
            
            // Real-time preview: merge buffer into artifact at correct position
            if (partialEditBounds && artifact) {
              const currentContent = artifact.contents[artifact.currentIndex]
              const fullContent = currentContent.type === 'code' 
                ? currentContent.code 
                : currentContent.fullMarkdown
              
              const previewContent = 
                fullContent.slice(0, partialEditBounds.start) +
                partialEditBuffer + customEvent.data.delta +
                fullContent.slice(partialEditBounds.end)
              
              // Update streaming preview
              setStreamingContent(previewContent)
            }
            break
          
          case 'partial_edit_end':
            // Finalize partial edit
            if (artifact && partialEditBounds) {
              const currentContent = artifact.contents[artifact.currentIndex]
              const fullContent = currentContent.type === 'code' 
                ? currentContent.code 
                : currentContent.fullMarkdown
              
              // Create new version with edited content
              const editedFullContent = 
                fullContent.slice(0, partialEditBounds.start) +
                customEvent.data.editedContent +
                fullContent.slice(partialEditBounds.end)
              
              const newVersion = {
                index: artifact.contents.length,
                type: currentContent.type,
                title: currentContent.title,
                ...(currentContent.type === 'code' 
                  ? { code: editedFullContent, language: currentContent.language }
                  : { fullMarkdown: editedFullContent }
                )
              }
              
              setArtifact({
                currentIndex: newVersion.index,
                contents: [...artifact.contents, newVersion]
              })
            }
            
            // Clear partial edit state
            setPartialEditBuffer("")
            setPartialEditBounds(null)
            setIsStreaming(false)
            setStreamingContent("")
            console.log('Partial edit completed')
            break
          
          // ... existing custom event cases ...
        }
        break
      
      // ... rest of cases ...
    }
  }, [artifact, partialEditBounds, partialEditBuffer])
  
  // ... rest of hook ...
}
```

**Implementation Steps**:
1. Add state for partial edit streaming: `partialEditBuffer`, `partialEditBounds`
2. Handle `partial_edit_start`: Initialize buffer and store edit boundaries
3. Handle `partial_edit_chunk`: 
   - Accumulate content in buffer
   - Generate real-time preview by splicing buffer into full content
   - Update `streamingContent` for live preview
4. Handle `partial_edit_end`:
   - Create new artifact version with final edited content
   - Splice: `before + editedContent + after`
   - Add new version to artifact history
   - Clear partial edit state
5. Add proper TypeScript types for custom events

---

### 2.4 Component Integration
**File**: `frontend/components/Canvas/CanvasChatContainer.tsx`

**Enhancement**: Wire up text selection callbacks

```typescript
export function CanvasChatContainer() {
  const { threadId } = useCanvasMode()
  const {
    artifact,
    messages,
    isStreaming,
    streamingContent,
    handleSendMessage,
    handleArtifactUpdate,
    handleVersionChange,
    handleTextSelect,  // NEW
    selectedText       // NEW
  } = useCanvasChat(threadId)
  
  return (
    <div className="flex h-screen">
      {/* Chat Panel */}
      <div className="w-1/2 border-r">
        <ChatHistory messages={messages} />
        <ChatInput 
          onSend={handleSendMessage}
          disabled={isStreaming}
          placeholder={selectedText 
            ? `Editing selected text (${selectedText.text.slice(0, 30)}...)`
            : "Message canvas agent..."
          }
        />
      </div>
      
      {/* Artifact Panel */}
      <div className="w-1/2">
        <ArtifactRenderer
          artifact={artifact}
          isStreaming={isStreaming}
          streamingContent={streamingContent}
          onArtifactUpdate={handleArtifactUpdate}
          onVersionChange={handleVersionChange}
          onTextSelect={handleTextSelect}  // NEW
        />
      </div>
    </div>
  )
}
```

**File**: `frontend/components/Canvas/ArtifactRenderer.tsx`

```typescript
interface ArtifactRendererProps {
  artifact: ArtifactV3 | null
  isStreaming: boolean
  streamingContent?: string
  onArtifactUpdate: (content: string, index: number) => void
  onVersionChange: (index: number) => void
  onTextSelect?: (selection: SelectedText) => void  // NEW
}

export function ArtifactRenderer({ 
  artifact, 
  isStreaming, 
  streamingContent,
  onArtifactUpdate,
  onVersionChange,
  onTextSelect  // NEW
}: ArtifactRendererProps) {
  // ... existing code ...
  
  return (
    <div className="flex flex-col h-full bg-white">
      <ArtifactHeader ... />
      
      <div className="flex-1 min-h-0 overflow-auto">
        {displayContent.type === "code" ? (
          <CodeRenderer
            code={displayContent.code}
            language={displayContent.language}
            isStreaming={isStreaming}
            onUpdate={(newCode) => onArtifactUpdate(newCode, artifact.currentIndex)}
            onTextSelect={onTextSelect}  // NEW
          />
        ) : (
          <TextRenderer
            markdown={displayContent.fullMarkdown}
            isStreaming={isStreaming}
            onUpdate={(newMarkdown) => onArtifactUpdate(newMarkdown, artifact.currentIndex)}
            onTextSelect={onTextSelect}  // NEW
          />
        )}
      </div>
    </div>
  )
}
```

**Implementation Steps**:
1. Pass `handleTextSelect` from `useCanvasChat` → `CanvasChatContainer` → `ArtifactRenderer` → renderers
2. Update `ChatInput` placeholder to show selected text preview
3. Add visual indicator when text is selected (optional: highlight selected region)

---

### 2.5 TypeScript Types
**File**: `frontend/types/canvas.ts`

**Enhancement**: Add partial edit types

```typescript
export interface SelectedText {
  start: number
  end: number
  text: string
}

export interface PartialEditStartEvent {
  originalStart: number
  originalEnd: number
  contentType: "code" | "text"
}

export interface PartialEditChunkEvent {
  delta: string
}

export interface PartialEditEndEvent {
  editedContent: string
  originalStart: number
  originalEnd: number
}
```

**File**: `frontend/types/agui.ts`

```typescript
export interface CustomAGUIEvent extends AGUIEvent {
  type: 'custom'
  custom_type: string
  data: any
}

// Add discriminated union for custom events
export type CanvasCustomEvent =
  | { custom_type: 'partial_edit_start'; data: PartialEditStartEvent }
  | { custom_type: 'partial_edit_chunk'; data: PartialEditChunkEvent }
  | { custom_type: 'partial_edit_end'; data: PartialEditEndEvent }
  | { custom_type: 'artifact_streaming_start'; data: any }
  // ... other custom events
```

**Implementation Steps**:
1. Add `SelectedText` interface (may already exist)
2. Add interfaces for partial edit event payloads
3. Create discriminated union for type-safe custom event handling

---

## 3. Testing Plan

### 3.1 Backend Tests
**New File**: `backend/tests/test_partial_editing.py`

```python
import pytest
import json
from api.routes import app
from fastapi.testclient import TestClient

client = TestClient(app)

@pytest.mark.asyncio
async def test_partial_edit_with_selection():
    """Test partial editing when selectedText is provided"""
    
    # Initial artifact
    artifact = {
        "currentIndex": 0,
        "contents": [{
            "index": 0,
            "type": "text",
            "title": "Test Document",
            "fullMarkdown": "This is the first paragraph.\n\nThis is the second paragraph.\n\nThis is the third paragraph."
        }]
    }
    
    # Select second paragraph
    selected_text = {
        "start": 29,
        "end": 56,
        "text": "This is the second paragraph."
    }
    
    request_data = {
        "thread_id": "test-thread-1",
        "message": "Make it more formal",
        "artifact": artifact,
        "selectedText": selected_text,
        "agent": "canvas"
    }
    
    events = []
    response = client.post("/canvas/chat", json=request_data, stream=True)
    
    for line in response.iter_lines():
        if line.startswith(b"data: "):
            event_data = json.loads(line[6:])
            events.append(event_data)
    
    # Verify partial edit events
    partial_start = next((e for e in events if e.get("custom_type") == "partial_edit_start"), None)
    assert partial_start is not None
    assert partial_start["data"]["originalStart"] == 29
    assert partial_start["data"]["originalEnd"] == 56
    
    partial_chunks = [e for e in events if e.get("custom_type") == "partial_edit_chunk"]
    assert len(partial_chunks) > 0
    
    partial_end = next((e for e in events if e.get("custom_type") == "partial_edit_end"), None)
    assert partial_end is not None
    assert "editedContent" in partial_end["data"]
    
    print("✓ Partial editing test passed")

@pytest.mark.asyncio
async def test_partial_edit_code_selection():
    """Test partial editing with code artifact"""
    
    artifact = {
        "currentIndex": 0,
        "contents": [{
            "index": 0,
            "type": "code",
            "title": "example.py",
            "code": "def hello():\n    print('Hello')\n\ndef goodbye():\n    print('Goodbye')",
            "language": "python"
        }]
    }
    
    # Select hello function
    selected_text = {
        "start": 0,
        "end": 31,
        "text": "def hello():\n    print('Hello')"
    }
    
    request_data = {
        "thread_id": "test-thread-2",
        "message": "Add docstring",
        "artifact": artifact,
        "selectedText": selected_text,
        "agent": "canvas"
    }
    
    response = client.post("/canvas/chat", json=request_data, stream=True)
    
    # Verify code partial edit works
    # ... similar assertions ...
    
    print("✓ Code partial editing test passed")
```

**Implementation Steps**:
1. Create test cases for text and code partial editing
2. Verify `partial_edit_start/chunk/end` events are emitted
3. Test boundary calculations (start/end positions)
4. Test version creation with spliced content

---

### 3.2 Frontend Tests
**Validation Tasks**:

1. **Text Selection**:
   - Select text in markdown renderer → verify `onTextSelect` called with correct positions
   - Select code in Monaco editor → verify selection tracking
   - Test edge cases: multi-line selections, special characters

2. **Streaming Preview**:
   - During partial edit, verify real-time content merging
   - Verify cursor position doesn't jump during streaming
   - Test undo/redo after partial edit

3. **Version History**:
   - After partial edit, verify new version created
   - Verify navigation between versions works
   - Verify partial edit reflected in diff view

---

## 4. Integration Points

### Backend → Frontend
1. **Selection to Backend**: Frontend sends `selectedText` in API request
2. **Partial Edit Events**: Backend streams `partial_edit_start/chunk/end` custom events
3. **Version Update**: Backend creates new artifact version with spliced content

### Frontend Rendering
1. **Real-time Preview**: During streaming, frontend shows live content merging
2. **Version Creation**: After `partial_edit_end`, frontend adds new version to artifact
3. **Selection Clearing**: After edit completes, clear selection state

---

## 5. Implementation Order

### Phase 1: Backend Foundation
1. ✅ Add `PartialEdit` TypedDict to state schema
2. ✅ Update `detect_intent_node` to detect `partial_update` action
3. ✅ Implement `_partial_update_artifact()` in `CanvasAgent`
4. ✅ Implement `_build_partial_edit_prompt()` for context-aware editing
5. ✅ Add partial edit event types to `event_types.py`
6. ✅ Update `update_artifact_node` to finalize partial edits

### Phase 2: Frontend Selection
1. ✅ Add text selection tracking to `TextRenderer`
2. ✅ Add selection tracking to `CodeRenderer` (Monaco)
3. ✅ Update `useCanvasChat` to manage selection state
4. ✅ Wire selection callbacks through component hierarchy

### Phase 3: Frontend Streaming
1. ✅ Add partial edit event handling in `useCanvasChat`
2. ✅ Implement real-time preview during streaming
3. ✅ Implement version creation on `partial_edit_end`
4. ✅ Add TypeScript types for partial edit events

### Phase 4: Testing & Refinement
1. ✅ Write backend test for partial editing flow
2. ✅ Manual testing: select text → edit → verify result
3. ✅ Test edge cases: boundary positions, multi-line, special chars
4. ✅ Performance testing: large documents, rapid edits

---

## 6. Success Criteria

✅ **User can select text/code in canvas artifact**
✅ **Selection boundaries (start/end) calculated correctly**
✅ **Backend receives selection context and generates edited portion only**
✅ **Frontend streams partial edit in real-time at correct position**
✅ **New artifact version created with correctly spliced content**
✅ **Version history shows partial edit as distinct version**
✅ **Works for both text (markdown) and code artifacts**

---

## 7. Future Enhancements

- **Multi-region editing**: Select multiple non-contiguous regions
- **Diff visualization**: Show before/after comparison in UI
- **Undo/redo**: Fine-grained undo for partial edits
- **Collaborative editing**: Multiple users editing different regions
- **Smart context detection**: Auto-expand selection to include related code blocks

---

## References

- Existing canvas implementation: [canvas-feature.md](canvas-feature.md)
- Backend agent patterns: [.github/agents/backend.agent.md](../../.github/agents/backend.agent.md)
- Frontend patterns: [.github/agents/frontend.agent.md](../../.github/agents/frontend.agent.md)
- AG-UI protocol: `frontend/services/agui-client.ts`
- LangGraph state: `backend/graphs/canvas_graph.py`
