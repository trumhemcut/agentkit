# Canvas Feature - Quick Start Guide

## Backend Setup Complete ✓

The Canvas feature has been successfully implemented in the backend with the following components:

### Files Created/Modified

1. **`backend/graphs/canvas_graph.py`** ✓
   - Canvas state definitions (CanvasGraphState, ArtifactV3, etc.)
   - Intent detection and routing logic
   - LangGraph workflow for canvas operations

2. **`backend/agents/canvas_agent.py`** ✓
   - Canvas agent with artifact generation capabilities
   - Streaming mode for real-time updates
   - Support for create/update/rewrite operations
   - Smart language and artifact type detection

3. **`backend/tools/canvas_tools.py`** ✓
   - ExtractCodeTool - Extract code from artifacts
   - UpdateCodeBlockTool - Update specific code sections
   - ConvertArtifactTypeTool - Convert between code/text
   - AnalyzeArtifactTool - Get artifact insights

4. **`backend/api/routes.py`** ✓
   - POST /canvas/stream - Main streaming endpoint
   - Placeholder endpoints for artifact persistence

5. **`backend/api/models.py`** ✓
   - CanvasMessageRequest - Request model
   - ArtifactV3 and related models

6. **`backend/protocols/event_types.py`** ✓
   - CanvasEventType - Custom event constants

7. **`backend/tests/test_canvas.py`** ✓
   - Comprehensive test suite (all tests passing)

## Testing the Canvas Feature

### 1. Start the Backend Server

```bash
cd /home/phihuynh/projects/agenkit
source .venv/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test with cURL

**Create a Code Artifact:**
```bash
curl -N -X POST http://localhost:8000/canvas/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a Python function to calculate factorial"}
    ]
  }'
```

**Update Existing Artifact:**
```bash
curl -N -X POST http://localhost:8000/canvas/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a factorial function"},
      {"role": "assistant", "content": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)"},
      {"role": "user", "content": "Add error handling for negative numbers"}
    ],
    "artifact": {
      "currentIndex": 1,
      "contents": [{
        "index": 1,
        "type": "code",
        "title": "Factorial Function",
        "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
        "language": "python"
      }]
    }
  }'
```

### 3. Run Unit Tests

```bash
cd /home/phihuynh/projects/agenkit
source .venv/bin/activate
cd backend
python tests/test_canvas.py
```

## Expected Event Stream

When you make a canvas request, you'll receive events like:

```json
{"type": "run_started", "thread_id": "...", "run_id": "..."}
{"type": "thinking", "data": {"message": "Processing create request..."}}
{"type": "artifact_streaming_start", "data": {"artifactType": "code"}}
{"type": "artifact_streaming", "data": {"contentDelta": "def ", "artifactIndex": 1}}
{"type": "artifact_streaming", "data": {"contentDelta": "factorial(n):\n", "artifactIndex": 1}}
...
{"type": "artifact_created", "data": {"artifact": {...}}}
{"type": "run_finished", "thread_id": "...", "run_id": "..."}
```

## API Endpoint Details

### POST /canvas/stream

**Request Body:**
```typescript
{
  thread_id?: string,
  run_id?: string,
  messages: Array<{role: string, content: string}>,
  artifact?: ArtifactV3,  // For updates
  selectedText?: {start: number, end: number, text: string},
  action?: "create" | "update" | "rewrite" | "chat"
}
```

**Response:** Server-Sent Events (SSE) stream

**Events:**
- `run_started` - Execution started
- `thinking` - Agent is processing
- `artifact_streaming_start` - Starting to generate artifact
- `artifact_streaming` - Streaming artifact content chunks
- `artifact_created` - New artifact created
- `artifact_updated` - Artifact updated
- `run_finished` - Execution completed
- `run_error` - Error occurred

## Features Implemented

### ✓ Core Functionality
- [x] Artifact creation (code and text)
- [x] Artifact updates with versioning
- [x] Real-time streaming with AG-UI
- [x] Intent detection (create/update/rewrite/chat)
- [x] Multiple programming languages support
- [x] Smart title extraction
- [x] Canvas tools for artifact manipulation

### ✓ Testing
- [x] Unit tests for all components
- [x] Integration tests for canvas workflow
- [x] All tests passing

### ✓ Documentation
- [x] Comprehensive README
- [x] Quick start guide
- [x] API documentation
- [x] Code comments

## Next Steps (Frontend Integration)

To complete the canvas feature, implement the frontend components as outlined in the implementation plan:

1. **Canvas Layout** - Split-view interface
2. **Artifact Renderer** - Display code/text artifacts
3. **Code Renderer** - Syntax highlighting with CodeMirror
4. **Text Renderer** - Rich markdown editor with BlockNote
5. **AG-UI Integration** - Event stream handling
6. **State Management** - Canvas context and hooks

See `.docs/1-implementation-plans/canvas-feature.md` for detailed frontend specifications.

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│          Frontend (NextJS)              │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ Chat Panel   │  │ Artifact Panel  │ │
│  │              │  │                 │ │
│  │  Messages    │  │  Code/Text      │ │
│  │  Input       │  │  Renderer       │ │
│  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────┘
            │ SSE Stream (AG-UI)
            ▼
┌─────────────────────────────────────────┐
│      Backend (FastAPI + LangGraph)      │
│  ┌─────────────────────────────────┐   │
│  │  POST /canvas/stream            │   │
│  └─────────────────────────────────┘   │
│             │                            │
│             ▼                            │
│  ┌─────────────────────────────────┐   │
│  │  Intent Detection Node          │   │
│  └─────────────────────────────────┘   │
│         │              │                 │
│   artifact_action    chat_only          │
│         │              │                 │
│         ▼              ▼                 │
│  ┌──────────┐   ┌──────────┐           │
│  │ Canvas   │   │  Chat    │           │
│  │ Agent    │   │  Agent   │           │
│  └──────────┘   └──────────┘           │
│         │                                │
│         ▼                                │
│  ┌─────────────────────────────────┐   │
│  │  Artifact (versioned)           │   │
│  │  - Code or Text                 │   │
│  │  - Version history              │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Configuration

The canvas feature uses your existing configuration:

```python
# config.py
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen:4b"
```

Make sure Ollama is running:
```bash
ollama serve
ollama pull qwen:4b
```

## Troubleshooting

### Issue: Module not found
**Solution:** Activate virtual environment
```bash
source /home/phihuynh/projects/agenkit/.venv/bin/activate
```

### Issue: Ollama connection error
**Solution:** Start Ollama service
```bash
ollama serve
```

### Issue: No streaming response
**Solution:** Ensure Accept header is set
```bash
-H "Accept: text/event-stream"
```

## Performance Notes

- Artifact streaming reduces latency
- Each version creates new entry (memory consideration)
- LLM calls are async and non-blocking
- Future: Add caching for large artifacts

## Security Considerations

- Input validation on all artifact operations
- Future: Add rate limiting
- Future: Implement artifact size limits
- Future: Sandbox code execution

## Support

For issues or questions:
1. Check test output: `python tests/test_canvas.py`
2. Review logs in terminal
3. See `CANVAS_README.md` for detailed docs
4. Check `.docs/1-implementation-plans/canvas-feature.md`

---

**Status:** ✅ Backend Implementation Complete
**Next:** Frontend Integration (see implementation plan)
