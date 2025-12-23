# Canvas Feature - Backend Implementation

## Overview
The Canvas feature enables a split-view interface for generating and editing artifacts (code/text) with real-time streaming updates through AG-UI protocol.

## Architecture

### Core Components

#### 1. State Management (`graphs/canvas_graph.py`)
- **CanvasGraphState**: Extended state with artifact, selection, and action tracking
- **ArtifactV3**: Versioned artifact structure supporting code and text types
- **Intent Detection**: Automatically routes between artifact manipulation and chat

#### 2. Canvas Agent (`agents/canvas_agent.py`)
- **Streaming Mode**: `run()` - Streams AG-UI events for real-time updates
- **Sync Mode**: `process_sync()` - Returns state for LangGraph workflow
- **Actions**:
  - `create`: Generate new artifacts from scratch
  - `update`: Modify existing artifacts incrementally  
  - `rewrite`: Complete artifact regeneration

#### 3. Canvas Tools (`tools/canvas_tools.py`)
- **ExtractCodeTool**: Extract code from artifacts
- **UpdateCodeBlockTool**: Update specific line ranges
- **ConvertArtifactTypeTool**: Convert between code/text formats
- **AnalyzeArtifactTool**: Get artifact metrics and insights

#### 4. API Routes (`api/routes.py`)
- **POST /canvas/stream**: Main canvas endpoint with SSE streaming
- **POST /canvas/artifacts/{id}**: Manual artifact updates (placeholder)
- **GET /canvas/artifacts/{id}/versions**: Version history (placeholder)

#### 5. Data Models (`api/models.py`)
- **CanvasMessageRequest**: Request with messages, artifact, and action
- **ArtifactV3/ArtifactContentCode/ArtifactContentText**: Artifact structures
- **SelectedText**: Text selection context

#### 6. Event Types (`protocols/event_types.py`)
- **CanvasEventType**: Custom canvas events for AG-UI
  - `artifact_created`
  - `artifact_updated`
  - `artifact_streaming`
  - `artifact_streaming_start`
  - `thinking`

## Request Flow

```
1. Client → POST /canvas/stream with CanvasMessageRequest
2. Detect intent (artifact action vs chat)
3. Route to CanvasAgent or ChatAgent
4. Stream AG-UI events:
   - RUN_STARTED
   - thinking
   - artifact_streaming_start
   - artifact_streaming (chunks)
   - artifact_created/artifact_updated
   - RUN_FINISHED
5. Client receives artifact in final event
```

## AG-UI Event Stream Example

```json
{
  "type": "run_started",
  "thread_id": "uuid",
  "run_id": "uuid"
}

{
  "type": "thinking",
  "data": {
    "message": "Processing create request..."
  }
}

{
  "type": "artifact_streaming_start",
  "data": {
    "artifactType": "code"
  }
}

{
  "type": "artifact_streaming",
  "data": {
    "contentDelta": "def hello():\n",
    "artifactIndex": 1
  }
}

{
  "type": "artifact_created",
  "data": {
    "artifact": {
      "currentIndex": 1,
      "contents": [{
        "index": 1,
        "type": "code",
        "title": "Hello Function",
        "code": "def hello():\n    print('Hello')",
        "language": "python"
      }]
    }
  }
}

{
  "type": "run_finished",
  "thread_id": "uuid",
  "run_id": "uuid"
}
```

## Artifact Structure

### Code Artifact
```python
{
  "index": 1,
  "type": "code",
  "title": "Example Function",
  "code": "def example():\n    return True",
  "language": "python"
}
```

### Text Artifact
```python
{
  "index": 1,
  "type": "text",
  "title": "Document Title",
  "fullMarkdown": "# Heading\n\nContent here..."
}
```

## LLM Integration

### System Prompts

**Code Creation:**
- Generates production-quality code
- Includes error handling and comments
- Follows language best practices

**Code Updates:**
- Maintains code structure
- Makes targeted changes
- Preserves code quality

**Text Creation:**
- Uses proper markdown formatting
- Organizes with headings/sections
- Concise and clear

## Intent Detection

The system automatically classifies user messages:

**Create Keywords**: create, write, generate, make, build
**Update Keywords**: update, modify, change, edit, fix  
**Rewrite Keywords**: rewrite, refactor, redo, restart

**Logic:**
- No artifact + create keywords → create
- Artifact exists + rewrite keywords → rewrite
- Artifact exists + update keywords → update
- Artifact exists + other → update (default)
- No artifact + no keywords → chat only

## Language Detection

Supports automatic detection of:
- Python, JavaScript, TypeScript
- Java, C, C++, Go
- Rust, Ruby, PHP

**Detection Strategy:**
1. Check user message for language mentions
2. Analyze code syntax patterns
3. Default to Python if uncertain

## Version Management

Each artifact modification creates a new version:
- `currentIndex`: Points to active version
- `contents[]`: Array of all versions
- Frontend can navigate version history

## Future Enhancements

### Persistence Layer
- Store artifacts in database
- Implement version history retrieval
- Enable artifact sharing/export

### Advanced Features
- Multi-artifact workflows
- Real-time collaborative editing
- Artifact templates
- Code execution in sandbox
- Visual diff between versions

### Tool Integration
- Static analysis tools
- Code formatting
- Linting and validation
- Test generation

## Testing

### Unit Tests
```python
# Test artifact creation
async def test_create_code_artifact():
    agent = CanvasAgent()
    state = {
        "messages": [{"role": "user", "content": "Write a hello function"}],
        "thread_id": "test",
        "run_id": "test"
    }
    result = await agent._create_artifact_sync(state)
    assert result["artifact"]["currentIndex"] == 1
    assert result["artifact"]["contents"][0]["type"] == "code"
```

### Integration Tests
```python
# Test canvas endpoint
async def test_canvas_stream():
    response = await client.post(
        "/canvas/stream",
        json={
            "messages": [{"role": "user", "content": "Create a function"}]
        }
    )
    assert response.status_code == 200
```

## Usage Example

```python
import requests

response = requests.post(
    "http://localhost:8000/canvas/stream",
    json={
        "messages": [
            {"role": "user", "content": "Write a Python function to calculate factorial"}
        ]
    },
    headers={"Accept": "text/event-stream"},
    stream=True
)

for line in response.iter_lines():
    if line:
        event = json.loads(line.decode('utf-8'))
        print(event["type"], event.get("data"))
```

## Configuration

No additional configuration needed. Uses existing:
- `OLLAMA_BASE_URL`: LLM provider endpoint
- `OLLAMA_MODEL`: Model for generation (default: qwen:4b)

## Dependencies

All dependencies already included in requirements.txt:
- FastAPI, LangGraph, LangChain-Ollama
- ag-ui-protocol for event streaming
- Pydantic for data validation

## Error Handling

The canvas endpoint handles errors gracefully:
- Invalid artifact structure → Returns validation error
- LLM timeout → Returns RUN_ERROR event
- Network issues → Client receives error event stream

## Performance Considerations

- Streaming reduces perceived latency
- Artifact content streamed in chunks
- State kept minimal (only current artifact)
- Future: Implement artifact caching

## Security Notes

- Validate all input artifacts
- Sanitize code before execution (future feature)
- Rate limit artifact generation requests
- Implement artifact size limits

## Monitoring

Track these metrics:
- Artifact creation rate
- Average artifact size
- Version count per artifact
- Error rates by artifact type
- LLM response times

## Contributing

When extending canvas features:
1. Add new artifact types in `canvas_graph.py`
2. Extend `CanvasAgent` with new actions
3. Create new tools in `tools/canvas_tools.py`
4. Add custom events to `CanvasEventType`
5. Update this documentation
