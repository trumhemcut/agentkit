# Partial Content Editing Feature

## Overview

The Partial Content Editing feature allows users to select specific portions of canvas artifacts and request targeted modifications. The agent generates only the modified section, and the system intelligently merges it back into the full content.

## Backend Implementation

### 1. Enhanced State Models

**SelectedText** (`graphs/canvas_graph.py`)
```python
class SelectedText(TypedDict):
    """User selected text in artifact - supports both character and line-based selection"""
    start: int                      # Character position start (0-indexed)
    end: int                        # Character position end (0-indexed)
    text: str                       # The actual selected text content
    lineStart: Optional[int]        # Line number start (1-indexed) for code
    lineEnd: Optional[int]          # Line number end (1-indexed) for code
```

**Updated CanvasGraphState**
- Added `"partial_update"` as a valid `artifactAction` value

### 2. Intent Detection

The `detect_intent_node` function now prioritizes text selection:

```python
def detect_intent_node(state: CanvasGraphState) -> CanvasGraphState:
    # Check if there's a text selection - this takes priority
    selected_text = state.get("selectedText")
    artifact = state.get("artifact")
    
    if selected_text and artifact:
        # User has selected text AND there's an existing artifact
        # Trigger partial_update action
        state["artifactAction"] = "partial_update"
        return state
    
    # ... existing logic for create/update/rewrite ...
```

### 3. AG-UI Protocol Events

**New Event Types** (`protocols/event_types.py`)

```python
class CanvasEventType:
    # Partial update events
    ARTIFACT_PARTIAL_UPDATE_START = "artifact_partial_update_start"
    ARTIFACT_PARTIAL_UPDATE_CHUNK = "artifact_partial_update_chunk"
    ARTIFACT_PARTIAL_UPDATE_COMPLETE = "artifact_partial_update_complete"
```

**Event Data Structure**

```python
# START Event
{
    "event_type": "artifact_partial_update_start",
    "data": {
        "selection": {"start": 100, "end": 200},
        "strategy": "replace"
    }
}

# CHUNK Event
{
    "event_type": "artifact_partial_update_chunk",
    "data": {
        "chunk": "async def ",
        "selection": {"start": 100, "end": 200}
    }
}

# COMPLETE Event
{
    "event_type": "artifact_partial_update_complete",
    "data": {
        "selection": {"start": 100, "end": 200},
        "updatedContent": "async def process_data(data):\n    return await transform(data)",
        "strategy": "replace"
    }
}
```

### 4. CanvasAgent Implementation

#### Context-Aware Prompt Building

The `_build_partial_update_prompt` method creates specialized prompts:

```python
def _build_partial_update_prompt(self, state: CanvasGraphState) -> str:
    """Build context-aware prompt for partial content updates"""
    
    # Extract context window (200 chars before/after selection)
    context_before = full_content[max(0, start - 200):start]
    context_after = full_content[end:min(len(full_content), end + 200)]
    
    # Build prompt with:
    # 1. Context before selection
    # 2. Selected text to modify
    # 3. Context after selection
    # 4. User's modification request
    # 5. Critical instructions to return ONLY the modified portion
```

**Key Prompt Instructions:**
- Return ONLY the modified version of selected text
- Maintain indentation and formatting style
- Do NOT include surrounding context
- Do NOT regenerate entire content
- Focus solely on requested change

#### Streaming Partial Updates

The `_stream_partial_update` method handles streaming:

```python
async def _stream_partial_update(self, state: CanvasGraphState):
    # 1. Build context-aware prompt
    system_prompt = self._build_partial_update_prompt(state)
    
    # 2. Emit START event with selection boundaries
    yield CustomEvent(
        event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_START,
        data={"selection": {...}, "strategy": "replace"}
    )
    
    # 3. Stream LLM response as CHUNK events
    async for chunk in self.llm.astream(messages):
        yield CustomEvent(
            event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_CHUNK,
            data={"chunk": chunk.content, "selection": {...}}
        )
    
    # 4. Emit COMPLETE event with full updated content
    yield CustomEvent(
        event_type=CanvasEventType.ARTIFACT_PARTIAL_UPDATE_COMPLETE,
        data={"selection": {...}, "updatedContent": updated_content}
    )
    
    # 5. Merge into artifact state
    self._merge_partial_update(state, updated_content)
```

#### Content Merging

The `_merge_partial_update` method handles intelligent merging:

```python
def _merge_partial_update(self, state: CanvasGraphState, updated_content: str):
    # 1. Get current artifact content
    full_content = current_content.get("code") or current_content.get("fullMarkdown")
    
    # 2. Replace selected region with updated content
    new_content = (
        full_content[:selection_start] +
        updated_content +
        full_content[selection_end:]
    )
    
    # 3. Create new artifact version (preserves history)
    new_index = len(artifact["contents"]) + 1
    
    # 4. Update state with new version
    state["artifact"] = updated_artifact
```

### 5. Routing in Main Agent

The `run` method now routes partial updates:

```python
async def run(self, state: CanvasGraphState):
    action = state.get("artifactAction")
    
    if action == "partial_update":
        async for event in self._stream_partial_update(state):
            yield event
    elif action == "create":
        # ... existing logic
    # ... other actions
```

## Request/Response Flow

### 1. Frontend Sends Request

```json
POST /canvas/stream

{
  "message": "make this function async",
  "artifact": {
    "currentIndex": 1,
    "contents": [{
      "index": 1,
      "type": "code",
      "code": "def process_data(data):\n    return transform(data)",
      "language": "python",
      "title": "Data Processor"
    }]
  },
  "selectedText": {
    "start": 0,
    "end": 23,
    "text": "def process_data(data):",
    "lineStart": 1,
    "lineEnd": 1
  },
  "thread_id": "thread_123"
}
```

### 2. Backend Detects Intent

- `detect_intent_node` sees `selectedText` + `artifact`
- Sets `artifactAction = "partial_update"`

### 3. Backend Streams Events

```
→ artifact_partial_update_start
→ artifact_partial_update_chunk ("async ")
→ artifact_partial_update_chunk ("def ")
→ artifact_partial_update_chunk ("process")
→ ...
→ artifact_partial_update_complete (full updated content)
```

### 4. Backend Merges Content

- Replaces characters 0-23 with new content
- Preserves rest of artifact
- Creates version 2 of artifact

### 5. Frontend Receives and Displays

- Receives streaming chunks
- Updates only the selected region
- Shows full merged content

## Key Features

### ✅ Context-Aware Prompting
- Includes 200 characters before/after selection
- Prevents LLM from hallucinating surrounding code
- Maintains proper indentation context

### ✅ Precise Selection Boundaries
- Character-based positioning (0-indexed)
- Line number support for code artifacts
- Exact replacement without drift

### ✅ Versioning Preserved
- Each partial update creates new artifact version
- Full history maintained
- Can undo/redo changes

### ✅ Streaming Support
- Real-time updates via AG-UI events
- Low latency feedback
- Chunked response delivery

### ✅ Multi-Format Support
- Works with code artifacts
- Works with text/markdown artifacts
- Language-agnostic

## Testing

Comprehensive test suite in `tests/test_partial_content_editing.py`:

- ✅ Intent detection with selection
- ✅ Intent detection without selection
- ✅ Prompt building with context windows
- ✅ Streaming event sequence
- ✅ Content merging (replace strategy)
- ✅ Artifact versioning preservation
- ✅ Metadata preservation (title, language)
- ✅ Edge cases (empty selection, invalid bounds)

Run tests:
```bash
cd backend
python tests/test_partial_content_editing.py
```

## Example Use Cases

### 1. Make Function Async

**Original:**
```python
def fetch_data(url):
    return requests.get(url)
```

**Selection:** `def fetch_data(url):`

**Request:** "make this async"

**Result:**
```python
async def fetch_data(url):
    return requests.get(url)
```

### 2. Refactor Loop

**Original:**
```python
total = 0
for num in numbers:
    total += num
return total
```

**Selection:** `for num in numbers:\n    total += num`

**Request:** "use list comprehension"

**Result:**
```python
total = 0
total = sum(numbers)
return total
```

### 3. Update Documentation

**Original:**
```markdown
## Overview

This is a brief description.
```

**Selection:** `This is a brief description.`

**Request:** "make it more detailed"

**Result:**
```markdown
## Overview

This comprehensive guide provides detailed information about...
```

## Implementation Status

✅ **Backend Complete**
- State models updated
- Intent detection implemented
- Event types defined
- Prompt building implemented
- Streaming logic implemented
- Content merging implemented
- Tests passing

⏳ **Frontend Pending**
- Text selection capture
- Event handlers
- Merging logic
- Visual feedback

## References

- Implementation Plan: `.docs/1-implementation-plans/009-partial-content-editing.md`
- Canvas Agent: `backend/agents/canvas_agent.py`
- State Models: `backend/graphs/canvas_graph.py`
- Event Types: `backend/protocols/event_types.py`
- API Models: `backend/api/models.py`
- Tests: `backend/tests/test_partial_content_editing.py`
