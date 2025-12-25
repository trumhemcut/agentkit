# Implementation Plan: Partial Content Editing in Canvas Mode

## Overview
Enable users to select a portion of content in Canvas mode and request the agent to make edits. The agent will stream only the modified section, and the frontend will intelligently merge the updated portion into the complete content in the canvas.

## Key Features
1. **Text Selection**: User selects a specific range of text in the artifact
2. **Partial Edit Request**: Agent receives context of selection + user's modification request
3. **Targeted Response**: Agent generates only the modified section (not entire content)
4. **Smart Merging**: Frontend streams and replaces only the selected region while preserving the rest

---

## Architecture

### State Flow
```
User selects text → Frontend captures selection coordinates → 
User sends edit request → Backend receives selection context → 
Agent generates partial update → Frontend merges partial update into full content
```

### Data Models

**Extended SelectedText (Backend)**
```python
class SelectedText(TypedDict):
    start: int          # Character position start
    end: int            # Character position end  
    text: str           # The actual selected text
    lineStart: int      # Line number start (optional, for code)
    lineEnd: int        # Line number end (optional, for code)
```

**Partial Edit Response (AG-UI Protocol)**
```typescript
{
  type: "artifact_partial_update",
  data: {
    selection: {
      start: number,
      end: number
    },
    updatedContent: string,  // Only the modified portion
    strategy: "replace" | "insert" | "append"
  }
}
```

---

## Backend Implementation

### 1. Update State Schema (`backend/graphs/canvas_graph.py`)

**Task:** Enhance `SelectedText` to include line numbers for code artifacts

```python
class SelectedText(TypedDict):
    """User selected text in artifact - supports both character and line-based selection"""
    start: int                      # Character position start (0-indexed)
    end: int                        # Character position end (0-indexed)
    text: str                       # The actual selected text content
    lineStart: Optional[int]        # Line number start (1-indexed) for code
    lineEnd: Optional[int]          # Line number end (1-indexed) for code
```

**Why:** Line numbers are crucial for code artifacts to provide precise context to the LLM.

---

### 2. Create Partial Update Intent Detection (`backend/graphs/canvas_graph.py`)

**Task:** Add detection logic for partial edit intent in `detect_intent_node`

```python
def detect_intent_node(state: CanvasGraphState) -> CanvasGraphState:
    """Classify if message requires artifact manipulation"""
    
    # Check if there's a text selection
    selected_text = state.get("selectedText")
    
    if selected_text and state.get("artifact"):
        # User has selected text AND there's an existing artifact
        # Default to "partial_update" action
        state["artifactAction"] = "partial_update"
        return state
    
    # ... existing logic for create/update/rewrite ...
```

**Why:** Need to distinguish partial edits from full artifact updates.

---

### 3. Implement Partial Update System Prompt (`backend/agents/canvas_agent.py`)

**Task:** Create specialized prompt for partial content editing

```python
def _build_partial_update_prompt(self, state: CanvasGraphState) -> str:
    """Build context-aware prompt for partial content updates"""
    
    artifact = state["artifact"]
    selected_text = state["selectedText"]
    current_content = artifact["contents"][artifact["currentIndex"] - 1]
    
    # Get surrounding context (lines/characters before and after)
    full_content = (current_content.get("code") or 
                    current_content.get("fullMarkdown") or "")
    
    selection_start = selected_text["start"]
    selection_end = selected_text["end"]
    
    # Extract context window (e.g., 200 chars before/after)
    context_window = 200
    context_before = full_content[max(0, selection_start - context_window):selection_start]
    context_after = full_content[selection_end:min(len(full_content), selection_end + context_window)]
    
    prompt = f"""You are editing a specific section of content in a canvas artifact.

**Task:** Modify ONLY the selected portion based on the user's request.

**Artifact Type:** {current_content["type"]}
**Language:** {current_content.get("language", "text")}

**Context Before Selection:**
```
{context_before}
```

**SELECTED TEXT (to be modified):**
```
{selected_text["text"]}
```

**Context After Selection:**
```
{context_after}
```

**User Request:** {state["messages"][-1]["content"]}

**Instructions:**
1. Return ONLY the modified version of the selected text
2. Maintain the same indentation and formatting style
3. Do NOT include surrounding context
4. Do NOT regenerate the entire content
5. Focus solely on the user's requested change

**Output Format:**
- For code: Return only the modified code block
- For text: Return only the modified paragraph/section
"""
    
    return prompt
```

**Why:** The LLM needs clear context boundaries to avoid hallucinating or regenerating entire content.

---

### 4. Implement Partial Update Streaming (`backend/agents/canvas_agent.py`)

**Task:** Add streaming logic for partial updates with custom AG-UI events

```python
async def _stream_partial_update(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
    """Stream partial content update for selected region"""
    
    # Build specialized prompt
    system_prompt = self._build_partial_update_prompt(state)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["messages"][-1]["content"]}
    ]
    
    # Emit start event
    yield CustomEvent(
        event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_START,
        data={
            "selection": {
                "start": state["selectedText"]["start"],
                "end": state["selectedText"]["end"]
            },
            "strategy": "replace"
        }
    )
    
    # Stream the partial update
    updated_content = ""
    async for chunk in self.llm.astream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            updated_content += chunk.content
            
            # Stream chunks to frontend
            yield CustomEvent(
                event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_CHUNK,
                data={
                    "chunk": chunk.content,
                    "selection": {
                        "start": state["selectedText"]["start"],
                        "end": state["selectedText"]["end"]
                    }
                }
            )
    
    # Emit completion event with full updated section
    yield CustomEvent(
        event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_COMPLETE,
        data={
            "selection": {
                "start": state["selectedText"]["start"],
                "end": state["selectedText"]["end"]
            },
            "updatedContent": updated_content,
            "strategy": "replace"
        }
    )
```

**Why:** Frontend needs to know exact selection boundaries and the replacement strategy.

---

### 5. Integrate Partial Update into Main Agent Run (`backend/agents/canvas_agent.py`)

**Task:** Add routing for partial update action

```python
async def run(self, state: CanvasGraphState) -> AsyncGenerator[BaseEvent, None]:
    """Stream events for artifact operations"""
    
    action = state.get("artifactAction", None)
    
    # ... existing RUN_STARTED event ...
    
    if action == "partial_update":
        # Handle partial content editing
        async for event in self._stream_partial_update(state):
            yield event
    elif action == "create":
        # ... existing create logic ...
    elif action in ["update", "rewrite"]:
        # ... existing update/rewrite logic ...
    else:
        # ... chat-only logic ...
    
    # ... existing RUN_FINISHED event ...
```

---

### 6. Update Custom Event Types (`backend/protocols/event_types.py`)

**Task:** Add new event types for partial updates

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
    
    # New: Partial update events
    ARTIFACT_PARTIAL_UPDATE_START = "artifact_partial_update_start"
    ARTIFACT_PARTIAL_UPDATE_CHUNK = "artifact_partial_update_chunk"
    ARTIFACT_PARTIAL_UPDATE_COMPLETE = "artifact_partial_update_complete"
```

---

### 7. Update API Models (`backend/api/models.py`)

**Task:** Ensure `CanvasMessageRequest` properly handles enhanced `selectedText`

```python
class SelectedText(BaseModel):
    """User-selected text in artifact"""
    start: int = Field(..., description="Character position start (0-indexed)")
    end: int = Field(..., description="Character position end (0-indexed)")
    text: str = Field(..., description="Selected text content")
    lineStart: Optional[int] = Field(None, description="Line number start (1-indexed) for code")
    lineEnd: Optional[int] = Field(None, description="Line number end (1-indexed) for code")
```

---

## AG-UI Protocol

### Event Flow Specification

**1. User Sends Request with Selection**
```json
{
  "message": "Make this function async",
  "artifact": { /* current artifact */ },
  "selectedText": {
    "start": 245,
    "end": 389,
    "text": "def process_data(data):\n    return transform(data)",
    "lineStart": 12,
    "lineEnd": 13
  },
  "thread_id": "thread_123"
}
```

**2. Backend Emits Partial Update Start**
```json
{
  "type": "custom_event",
  "event_type": "artifact_partial_update_start",
  "data": {
    "selection": { "start": 245, "end": 389 },
    "strategy": "replace"
  }
}
```

**3. Backend Streams Partial Update Chunks**
```json
{
  "type": "custom_event",
  "event_type": "artifact_partial_update_chunk",
  "data": {
    "chunk": "async def ",
    "selection": { "start": 245, "end": 389 }
  }
}
```

**4. Backend Emits Completion**
```json
{
  "type": "custom_event",
  "event_type": "artifact_partial_update_complete",
  "data": {
    "selection": { "start": 245, "end": 389 },
    "updatedContent": "async def process_data(data):\n    return await transform(data)",
    "strategy": "replace"
  }
}
```

---

## Frontend Implementation

### 1. Update Types (`frontend/types/canvas.ts`)

**Task:** Add types for partial updates

```typescript
export interface SelectedText {
  start: number          // Character position start (0-indexed)
  end: number           // Character position end (0-indexed)
  text: string          // Selected text content
  lineStart?: number    // Line number start (1-indexed) for code
  lineEnd?: number      // Line number end (1-indexed) for code
}

export interface PartialUpdateEvent {
  selection: {
    start: number
    end: number
  }
  updatedContent?: string   // Only present in COMPLETE event
  chunk?: string            // Only present in CHUNK event
  strategy: 'replace' | 'insert' | 'append'
}
```

---

### 2. Enhance Canvas Context (`frontend/contexts/CanvasContext.tsx`)

**Task:** Add state management for partial updates and text selection

```typescript
interface CanvasContextType {
  // ... existing fields ...
  selectedText: SelectedText | null
  setSelectedText: (selection: SelectedText | null) => void
  isPartialUpdating: boolean
  partialUpdateBuffer: string
}

export function CanvasProvider({ children }: { children: React.ReactNode }) {
  const [selectedText, setSelectedText] = useState<SelectedText | null>(null)
  const [isPartialUpdating, setIsPartialUpdating] = useState(false)
  const [partialUpdateBuffer, setPartialUpdateBuffer] = useState("")
  
  // ... existing state ...
  
  return (
    <CanvasContext.Provider value={{
      // ... existing values ...
      selectedText,
      setSelectedText,
      isPartialUpdating,
      partialUpdateBuffer
    }}>
      {children}
    </CanvasContext.Provider>
  )
}
```

---

### 3. Implement Text Selection Handler (`frontend/components/Canvas/CodeRenderer.tsx`)

**Task:** Capture user text selection in CodeMirror

```typescript
import { EditorView } from "@codemirror/view"
import { EditorSelection } from "@codemirror/state"

export function CodeRenderer({ code, language, isStreaming, onUpdate, onSelectionChange }: CodeRendererProps) {
  // ... existing code ...
  
  const handleSelectionChange = (view: EditorView) => {
    const selection = view.state.selection.main
    
    if (selection.from !== selection.to) {
      // User has selected text
      const selectedText = view.state.doc.sliceString(selection.from, selection.to)
      
      // Calculate line numbers
      const fromLine = view.state.doc.lineAt(selection.from).number
      const toLine = view.state.doc.lineAt(selection.to).number
      
      onSelectionChange({
        start: selection.from,
        end: selection.to,
        text: selectedText,
        lineStart: fromLine,
        lineEnd: toLine
      })
    } else {
      // Clear selection
      onSelectionChange(null)
    }
  }
  
  return (
    <CodeMirror
      value={localCode}
      extensions={[
        ...extensions,
        EditorView.updateListener.of((update) => {
          if (update.selectionSet) {
            handleSelectionChange(update.view)
          }
        })
      ]}
      onChange={handleChange}
      editable={!isStreaming}
    />
  )
}
```

**Task:** Similar implementation for `TextRenderer.tsx` (for markdown content)

```typescript
export function TextRenderer({ content, isStreaming, onUpdate, onSelectionChange }: TextRendererProps) {
  const handleMouseUp = () => {
    const selection = window.getSelection()
    
    if (selection && selection.toString().length > 0) {
      const range = selection.getRangeAt(0)
      
      // Get character positions relative to the content
      const preSelectionRange = range.cloneRange()
      preSelectionRange.selectNodeContents(contentRef.current!)
      preSelectionRange.setEnd(range.startContainer, range.startOffset)
      const start = preSelectionRange.toString().length
      
      onSelectionChange({
        start,
        end: start + selection.toString().length,
        text: selection.toString()
      })
    } else {
      onSelectionChange(null)
    }
  }
  
  return (
    <div 
      ref={contentRef}
      onMouseUp={handleMouseUp}
      className="prose"
    >
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  )
}
```

---

### 4. Update AGUI Hook (`frontend/hooks/useCanvasChat.ts`)

**Task:** Handle partial update events from backend

```typescript
export function useCanvasChat(threadId: string) {
  const { selectedText, setIsPartialUpdating, setPartialUpdateBuffer } = useCanvas()
  
  // ... existing code ...
  
  useEffect(() => {
    if (!sseConnection) return
    
    const handlePartialUpdateStart = (event: CustomEvent) => {
      setIsPartialUpdating(true)
      setPartialUpdateBuffer("")
    }
    
    const handlePartialUpdateChunk = (event: CustomEvent) => {
      const { chunk } = event.data as PartialUpdateEvent
      setPartialUpdateBuffer(prev => prev + chunk)
    }
    
    const handlePartialUpdateComplete = (event: CustomEvent) => {
      const { selection, updatedContent, strategy } = event.data as PartialUpdateEvent
      
      // Merge the updated content into the artifact
      mergePartialUpdate(selection, updatedContent, strategy)
      
      setIsPartialUpdating(false)
      setPartialUpdateBuffer("")
    }
    
    sseConnection.addEventListener('artifact_partial_update_start', handlePartialUpdateStart)
    sseConnection.addEventListener('artifact_partial_update_chunk', handlePartialUpdateChunk)
    sseConnection.addEventListener('artifact_partial_update_complete', handlePartialUpdateComplete)
    
    return () => {
      sseConnection.removeEventListener('artifact_partial_update_start', handlePartialUpdateStart)
      sseConnection.removeEventListener('artifact_partial_update_chunk', handlePartialUpdateChunk)
      sseConnection.removeEventListener('artifact_partial_update_complete', handlePartialUpdateComplete)
    }
  }, [sseConnection])
  
  // ... rest of hook ...
}
```

---

### 5. Implement Partial Update Merging Logic (`frontend/hooks/useCanvasChat.ts`)

**Task:** Smart merging of partial updates into full content

```typescript
function mergePartialUpdate(
  selection: { start: number; end: number },
  updatedContent: string,
  strategy: 'replace' | 'insert' | 'append'
) {
  setArtifact(prevArtifact => {
    if (!prevArtifact) return null
    
    const currentContent = prevArtifact.contents[prevArtifact.currentIndex - 1]
    const fullContent = currentContent.type === "code" 
      ? currentContent.code 
      : currentContent.fullMarkdown
    
    let newContent: string
    
    switch (strategy) {
      case 'replace':
        // Replace selected region with updated content
        newContent = 
          fullContent.slice(0, selection.start) +
          updatedContent +
          fullContent.slice(selection.end)
        break
      
      case 'insert':
        // Insert at cursor position (preserve selection)
        newContent = 
          fullContent.slice(0, selection.start) +
          updatedContent +
          fullContent.slice(selection.start)
        break
      
      case 'append':
        // Append after selection
        newContent = 
          fullContent.slice(0, selection.end) +
          updatedContent +
          fullContent.slice(selection.end)
        break
      
      default:
        newContent = fullContent
    }
    
    // Create new version of artifact with updated content
    const updatedArtifactContent = currentContent.type === "code"
      ? { ...currentContent, code: newContent }
      : { ...currentContent, fullMarkdown: newContent }
    
    return {
      ...prevArtifact,
      currentIndex: prevArtifact.currentIndex + 1,
      contents: [...prevArtifact.contents, updatedArtifactContent]
    }
  })
}
```

**Why:** Preserves artifact versioning while only updating the modified section.

---

### 6. Enhance Chat Input (`frontend/components/ChatInput.tsx`)

**Task:** Display selected text context when sending message

```typescript
export function ChatInput({ onSend, disabled, selectedText }: ChatInputProps) {
  const [message, setMessage] = useState("")
  
  const handleSend = () => {
    if (!message.trim()) return
    
    onSend({
      message: message.trim(),
      selectedText: selectedText || undefined
    })
    
    setMessage("")
  }
  
  return (
    <div className="space-y-2">
      {selectedText && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-blue-700">Selected:</span>
            <span className="text-gray-500">
              {selectedText.lineStart && selectedText.lineEnd
                ? `Lines ${selectedText.lineStart}-${selectedText.lineEnd}`
                : `${selectedText.start}-${selectedText.end}`}
            </span>
          </div>
          <pre className="text-xs text-gray-700 overflow-x-auto">
            {selectedText.text.slice(0, 100)}
            {selectedText.text.length > 100 && "..."}
          </pre>
        </div>
      )}
      
      <div className="flex gap-2">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={
            selectedText 
              ? "Ask to modify the selected text..." 
              : "Type your message..."
          }
          disabled={disabled}
        />
        <Button onClick={handleSend} disabled={disabled || !message.trim()}>
          Send
        </Button>
      </div>
    </div>
  )
}
```

---

### 7. Visual Feedback for Streaming Updates (`frontend/components/Canvas/CodeRenderer.tsx`)

**Task:** Highlight the region being updated during streaming

```typescript
import { Decoration, DecorationSet } from "@codemirror/view"
import { StateField, StateEffect } from "@codemirror/state"

const partialUpdateEffect = StateEffect.define<{start: number, end: number}>()

const partialUpdateField = StateField.define<DecorationSet>({
  create() { return Decoration.none },
  update(decorations, tr) {
    decorations = decorations.map(tr.changes)
    
    for (let effect of tr.effects) {
      if (effect.is(partialUpdateEffect)) {
        const deco = Decoration.mark({
          class: "partial-update-highlight"
        }).range(effect.value.start, effect.value.end)
        
        decorations = Decoration.set([deco])
      }
    }
    
    return decorations
  },
  provide: f => EditorView.decorations.from(f)
})

// In CodeRenderer component:
export function CodeRenderer({ 
  code, 
  isPartialUpdating, 
  updateSelection 
}: CodeRendererProps) {
  
  const extensions = [
    ...getLanguageExtension(language),
    partialUpdateField
  ]
  
  useEffect(() => {
    if (isPartialUpdating && updateSelection && editorViewRef.current) {
      // Highlight the region being updated
      editorViewRef.current.dispatch({
        effects: partialUpdateEffect.of({
          start: updateSelection.start,
          end: updateSelection.end
        })
      })
    }
  }, [isPartialUpdating, updateSelection])
  
  // ... rest of component ...
}
```

**CSS for highlighting:**
```css
/* globals.css */
.partial-update-highlight {
  background-color: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.4);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
```

---

## Testing Strategy

### Backend Tests (`backend/tests/test_partial_content_editing.py`)

**1. Test Intent Detection**
```python
def test_partial_update_intent_detection():
    """Test that selection + message triggers partial_update action"""
    state = {
        "messages": [{"role": "user", "content": "make this async"}],
        "artifact": {...},  # existing artifact
        "selectedText": {"start": 100, "end": 200, "text": "def foo():"}
    }
    
    result = detect_intent_node(state)
    assert result["artifactAction"] == "partial_update"
```

**2. Test Prompt Building**
```python
def test_partial_update_prompt_context():
    """Ensure prompt includes proper context window"""
    agent = CanvasAgent()
    state = {...}  # with selection
    
    prompt = agent._build_partial_update_prompt(state)
    
    assert "Context Before Selection" in prompt
    assert "SELECTED TEXT" in prompt
    assert "Context After Selection" in prompt
```

**3. Test Streaming Events**
```python
async def test_partial_update_streaming():
    """Verify correct event sequence for partial updates"""
    agent = CanvasAgent()
    state = {...}  # with selection
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    assert events[0].event_type == CanvasEventType.ARTIFACT_PARTIAL_UPDATE_START
    assert any(e.event_type == CanvasEventType.ARTIFACT_PARTIAL_UPDATE_CHUNK for e in events)
    assert events[-1].event_type == CanvasEventType.ARTIFACT_PARTIAL_UPDATE_COMPLETE
```

---

### Frontend Tests

**1. Test Selection Capture**
```typescript
// Test that CodeMirror properly captures selection
it('captures text selection with line numbers', () => {
  const onSelectionChange = jest.fn()
  render(<CodeRenderer 
    code="line1\nline2\nline3" 
    onSelectionChange={onSelectionChange}
  />)
  
  // Simulate selection...
  expect(onSelectionChange).toHaveBeenCalledWith({
    start: 6,
    end: 17,
    text: "line2\nline3",
    lineStart: 2,
    lineEnd: 3
  })
})
```

**2. Test Partial Update Merging**
```typescript
// Test that partial updates correctly merge into content
it('merges partial update into artifact content', () => {
  const originalContent = "hello world\nfoo bar"
  const selection = { start: 12, end: 19 }  // "foo bar"
  const updatedContent = "baz qux"
  
  const result = mergePartialUpdate(selection, updatedContent, 'replace')
  
  expect(result).toBe("hello world\nbaz qux")
})
```

---

## User Experience Flow

### Example Scenario: Edit a Function

**Step 1:** User opens Canvas with a Python script
```python
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
```

**Step 2:** User selects the loop portion:
```python
    for num in numbers:
        total += num
```

**Step 3:** User types: "make this use list comprehension"

**Step 4:** Backend generates ONLY the modified section:
```python
    total = sum(numbers)
```

**Step 5:** Frontend merges the update, result:
```python
def calculate_sum(numbers):
    total = 0
    total = sum(numbers)
    return total
```

**Note:** LLM might need refinement to remove redundant lines. Consider adding post-processing.

---

## Dependencies

### Backend
- **No new dependencies required**
- Uses existing: LangGraph, ag-ui, ollama

### Frontend
- **CodeMirror 6**: Already installed (`@uiw/react-codemirror`)
- **Selection API**: Native browser API for text selection
- **No new dependencies required**

---

## Edge Cases & Considerations

### 1. Multi-line Selection in Code
- **Issue:** Selection might span incomplete syntax blocks
- **Solution:** LLM prompt instructs to maintain context and indentation

### 2. Overlapping Updates
- **Issue:** User sends another edit while one is streaming
- **Solution:** Disable input during `isPartialUpdating` state

### 3. Selection Drift
- **Issue:** Character positions change if content is edited
- **Solution:** Always capture selection immediately before sending request

### 4. Empty Selection
- **Issue:** User sends message without selecting text
- **Solution:** Fall back to full artifact update behavior

### 5. LLM Generates Too Much Content
- **Issue:** LLM might ignore instruction and regenerate everything
- **Solution:** 
  - Stronger system prompt with examples
  - Post-processing to extract only the relevant portion
  - Validate output length against selection length

---

## Success Criteria

✅ **Backend:**
- [ ] `selectedText` with line numbers properly captured
- [ ] Intent detection correctly identifies `partial_update` action
- [ ] System prompt includes proper context window
- [ ] Partial update streaming emits correct AG-UI events
- [ ] Only modified section is generated by LLM

✅ **Frontend:**
- [ ] CodeMirror captures text selection with positions
- [ ] Selected text displayed in chat input area
- [ ] Partial update events properly received
- [ ] Merging logic correctly replaces selected region
- [ ] Visual feedback (highlighting) during streaming
- [ ] Artifact versioning preserved

✅ **Integration:**
- [ ] End-to-end flow: select → edit → stream → merge
- [ ] Works for both code and markdown artifacts
- [ ] Performance: No lag during streaming merge
- [ ] Error handling: Graceful fallback on failure

---

## Implementation Order

### Phase 1: Backend Foundation (Day 1-2)
1. Update `SelectedText` model with line numbers
2. Add `partial_update` intent detection
3. Implement `_build_partial_update_prompt` method
4. Add new AG-UI event types

### Phase 2: Backend Streaming (Day 2-3)
1. Implement `_stream_partial_update` method
2. Integrate into main `CanvasAgent.run` router
3. Write backend tests

### Phase 3: Frontend Selection (Day 3-4)
1. Update TypeScript types
2. Implement selection capture in `CodeRenderer`
3. Implement selection capture in `TextRenderer`
4. Update `ChatInput` to display selection context

### Phase 4: Frontend Merging (Day 4-5)
1. Enhance `CanvasContext` with partial update state
2. Implement AG-UI event handlers in `useCanvasChat`
3. Implement `mergePartialUpdate` logic
4. Add visual feedback (highlighting)

### Phase 5: Testing & Refinement (Day 5-6)
1. Write frontend tests
2. End-to-end manual testing
3. Fix edge cases
4. Performance optimization
5. Update knowledge base documentation

---

## Knowledge Base Updates

After implementation, update:
- `/.docs/2-knowledge-base/canvas-implementation-summary.md` - Add partial editing section
- `/.docs/2-knowledge-base/agui-protocol/protocol-spec.md` - Document new event types
- `/.docs/2-knowledge-base/frontend/canvas-components.md` - Document selection handling
- `/.docs/2-knowledge-base/backend/canvas-agent.md` - Document partial update logic

---

## References

- [Backend Agent Guide](../../.github/agents/backend.agent.md) - LangGraph patterns
- [Frontend Agent Guide](../../.github/agents/frontend.agent.md) - AG-UI integration
- [Canvas Implementation Summary](../.docs/2-knowledge-base/canvas-implementation-summary.md) - Current state
- [LangGraph Docs](/langchain-ai/langgraph) - State management patterns
- [AG-UI Protocol](/ag-ui-protocol/ag-ui) - Event-driven communication
