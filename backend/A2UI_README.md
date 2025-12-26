# A2UI Protocol Backend Implementation

> ✅ **Status**: Complete and Tested (December 27, 2025)

This directory contains the backend implementation of the **A2UI (Agent-to-UI) protocol** for AgentKit, enabling AI agents to generate dynamic, interactive UI components.

## Quick Start

### 1. Start the Backend Server

```bash
cd backend
python main.py
```

### 2. Test the A2UI Endpoint

```bash
# Basic test - creates a checkbox UI
curl -N http://localhost:8000/a2ui/stream

# Custom message
curl -N http://localhost:8000/a2ui/stream?message=Create+a+terms+agreement

# With thread ID
curl -N http://localhost:8000/a2ui/stream?thread_id=my-thread-123
```

### 3. Run Tests

```bash
cd backend

# All A2UI tests
python -m pytest tests/test_a2ui_*.py -v

# Protocol tests only
python -m pytest tests/test_a2ui_protocol.py -v

# Agent tests only
python -m pytest tests/test_a2ui_agent.py -v
```

## What's Implemented

### Core Components

1. **Protocol Types** (`protocols/a2ui_types.py`)
   - Pydantic models for A2UI messages
   - Helper functions for common components
   
2. **Message Encoder** (`protocols/a2ui_encoder.py`)
   - SSE and JSONL format encoding
   - Message type detection

3. **A2UI Agent** (`agents/a2ui_agent.py`)
   - Generates interactive UI components
   - Mixes A2UI with AG-UI events
   
4. **API Endpoint** (`api/routes.py`)
   - `GET /a2ui/stream` for testing

5. **Tests** (`tests/test_a2ui_*.py`)
   - 34 tests, 100% passing ✅

## Architecture

```
A2UI Messages Flow:

Agent → surfaceUpdate → dataModelUpdate → beginRendering → AG-UI Text
         (components)    (initial data)     (render signal)   (context)
```

### Example Event Stream

```
data: {"type":"surfaceUpdate","surfaceId":"surface-abc",...}
data: {"type":"dataModelUpdate","surfaceId":"surface-abc",...}
data: {"type":"beginRendering","surfaceId":"surface-abc",...}
data: {"type":"TEXT_MESSAGE_CONTENT","delta":"Check the box above"}
```

## Message Types

| Type | Purpose | Example Use |
|------|---------|-------------|
| `surfaceUpdate` | Define UI components | Create checkbox, button, form |
| `dataModelUpdate` | Update component state | Set initial values, update data |
| `beginRendering` | Signal ready to render | Tell frontend which component is root |
| `deleteSurface` | Remove UI surface | Clean up when done |

## Usage Example

### Python Code

```python
from agents.a2ui_agent import A2UIAgent

# Create agent
agent = A2UIAgent()

# Prepare state
state = {
    "messages": [{"role": "user", "content": "Show checkbox"}],
    "thread_id": "thread-123",
    "run_id": "run-456"
}

# Stream events
async for event in agent.run(state):
    print(event)
```

### Creating Custom Components

```python
from protocols.a2ui_types import (
    create_checkbox_component,
    create_text_component,
    SurfaceUpdate,
    DataModelUpdate,
    BeginRendering
)

# Create components
checkbox = create_checkbox_component(
    component_id="my-checkbox",
    label_text="I agree",
    value_path="/form/agreed"
)

text = create_text_component(
    component_id="my-text",
    content="Please accept the terms"
)

# Create surface
surface_update = SurfaceUpdate(
    surface_id="my-surface",
    components=[text, checkbox]
)
```

## Component Catalog

### Currently Implemented

- ✅ **Checkbox**: Interactive checkbox with label
- ✅ **Text**: Static or dynamic text
- ✅ **Button**: Button with action trigger

### Coming Soon

- ⏳ Input fields (text, number, email)
- ⏳ Dropdown/Select
- ⏳ Card layouts
- ⏳ Tables and lists
- ⏳ Forms with validation

## API Reference

### GET /a2ui/stream

Test endpoint for A2UI agent.

**Query Parameters**:
- `message` (string, optional): User message. Default: "Show me a checkbox"
- `thread_id` (string, optional): Thread ID for conversation context

**Response**:
- Content-Type: `text/event-stream`
- Stream of A2UI and AG-UI events

**Example**:
```bash
curl -N "http://localhost:8000/a2ui/stream?message=Show+me+a+checkbox"
```

## Testing

### Run All Tests

```bash
pytest tests/test_a2ui_*.py -v
```

**Expected Output**:
```
34 passed, 5 warnings ✅
```

### Test Coverage

- **Protocol Tests**: 22 tests covering message types, encoding, helpers
- **Agent Tests**: 12 tests covering agent logic, event generation, error handling

## Documentation

📚 **Full Documentation**: `.docs/2-knowledge-base/a2ui-protocol.md`

This includes:
- Complete protocol specification
- Backend implementation guide
- Component catalog reference
- Streaming patterns and best practices
- Troubleshooting guide

## Next Steps

1. **Frontend Integration** (Phase 2):
   - Create A2UI store in frontend
   - Build component renderers
   - Implement data binding

2. **Extended Components** (Phase 3):
   - Add more component types
   - Support complex layouts
   - Implement form validation

3. **LLM-Driven Generation** (Phase 4):
   - Use structured output from LLMs
   - Dynamic UI based on queries
   - Template system

## Files Structure

```
backend/
├── protocols/
│   ├── a2ui_types.py          # Pydantic models (268 lines)
│   └── a2ui_encoder.py        # SSE/JSONL encoder (147 lines)
├── agents/
│   └── a2ui_agent.py          # A2UI agent (243 lines)
├── api/
│   └── routes.py              # API endpoint (+87 lines)
└── tests/
    ├── test_a2ui_protocol.py  # Protocol tests (330 lines)
    └── test_a2ui_agent.py     # Agent tests (337 lines)
```

## References

- [A2UI Specification](https://a2ui.org/specification/v0.8-a2ui/)
- [A2UI GitHub Repository](https://github.com/google/a2ui)
- [Implementation Plan](../.docs/1-implementation-plans/017-support-a2ui-protocol-plan.md)
- [Backend Agent Guide](../.github/agents/backend.agent.md)

## Support

For questions or issues:
- Check the [knowledge base](../.docs/2-knowledge-base/a2ui-protocol.md)
- Review [implementation summary](../.docs/2-knowledge-base/a2ui-implementation-summary.md)
- See test examples in `tests/test_a2ui_*.py`

---

**Implementation Status**: ✅ Complete  
**Test Status**: ✅ 34/34 passing  
**Documentation**: ✅ Complete  
**Ready for**: Frontend integration (Phase 2)
