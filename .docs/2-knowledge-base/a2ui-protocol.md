# A2UI Protocol Documentation

## Overview

**A2UI (Agent-to-UI)** is an open protocol that enables AI agents to generate dynamic, interactive UI components as JSON that render natively in the frontend. This protocol complements the existing AG-UI protocol in AgentKit.

### Protocol Comparison

| Feature | AG-UI | A2UI |
|---------|-------|------|
| **Purpose** | Real-time event streaming | Declarative UI generation |
| **Message Types** | Text messages, status updates, agent thinking | UI components, data models, rendering signals |
| **Use Cases** | Chat messages, streaming responses | Forms, checkboxes, buttons, interactive UIs |
| **Format** | Event-based (SSE) | Component-based (JSON) |

## Architecture

### Data Flow

```
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│  LangGraph  │  A2UI     │   FastAPI   │   SSE     │   React     │
│   Agent     │  JSON ──> │   Backend   │  Stream─> │  Frontend   │
└─────────────┘           └─────────────┘           └─────────────┘
     │                           │                         │
     ├─ Generate UI JSON         ├─ Validate & Stream      ├─ Parse A2UI
     ├─ Component Tree           ├─ Mix with AG-UI         ├─ Buffer Components
     └─ Data Model               └─ Event Encoding         └─ Render Native UI
```

### Component Model

A2UI uses an **adjacency list model** for components:

- Each component has a unique `id` within a surface
- Components are defined by a `component` dictionary with type as key
- The root component is specified in `beginRendering` message

Example:
```json
{
  "id": "checkbox-1",
  "component": {
    "Checkbox": {
      "label": {"literalString": "I agree"},
      "value": {"path": "/form/agreed"}
    }
  }
}
```

## Core Message Types

### 1. surfaceUpdate

Defines or updates UI components in a surface. A surface is a collection of components that can be rendered independently.

**Schema:**
```json
{
  "type": "surfaceUpdate",
  "surfaceId": "surface-abc123",
  "components": [
    {
      "id": "component-id",
      "component": {
        "ComponentType": {
          // component properties
        }
      }
    }
  ]
}
```

**Example:**
```json
{
  "type": "surfaceUpdate",
  "surfaceId": "surface-12ab",
  "components": [
    {
      "id": "terms-checkbox",
      "component": {
        "Checkbox": {
          "label": {"literalString": "I agree to terms"},
          "value": {"path": "/form/agreedToTerms"}
        }
      }
    }
  ]
}
```

### 2. dataModelUpdate

Updates the data model that backs UI components. Uses JSON Pointer paths to specify update locations.

**Schema:**
```json
{
  "type": "dataModelUpdate",
  "surfaceId": "surface-abc123",
  "path": "/optional/path",
  "contents": [
    {
      "key": "fieldName",
      "valueString": "string value",     // optional
      "valueNumber": 42,                 // optional
      "valueBoolean": true,              // optional
      "valueMap": {"nested": "object"}   // optional
    }
  ]
}
```

**Examples:**

Update root data model:
```json
{
  "type": "dataModelUpdate",
  "surfaceId": "surface-12ab",
  "path": "/",
  "contents": [
    {"key": "userName", "valueString": "Alice"},
    {"key": "age", "valueNumber": 30}
  ]
}
```

Update nested path:
```json
{
  "type": "dataModelUpdate",
  "surfaceId": "surface-12ab",
  "path": "/form/settings",
  "contents": [
    {"key": "theme", "valueString": "dark"},
    {"key": "notifications", "valueBoolean": true}
  ]
}
```

### 3. beginRendering

Signals the frontend to start rendering from a specified root component.

**Schema:**
```json
{
  "type": "beginRendering",
  "surfaceId": "surface-abc123",
  "rootComponentId": "root-component-id"
}
```

**Example:**
```json
{
  "type": "beginRendering",
  "surfaceId": "surface-12ab",
  "rootComponentId": "main-form"
}
```

**Important:** This message should be sent **after** `surfaceUpdate` and `dataModelUpdate` to prevent partial rendering.

### 4. deleteSurface

Removes a UI surface and all its components.

**Schema:**
```json
{
  "type": "deleteSurface",
  "surfaceId": "surface-abc123"
}
```

## Backend Implementation

### File Structure

```
backend/
├── protocols/
│   ├── a2ui_types.py      # Pydantic models for A2UI messages
│   └── a2ui_encoder.py    # SSE/JSONL encoder
├── agents/
│   └── a2ui_agent.py      # Agent that generates A2UI components
└── api/
    └── routes.py          # API endpoint: /a2ui/stream
```

### Usage Example

```python
from agents.a2ui_agent import A2UIAgent
from protocols.a2ui_types import SurfaceUpdate, create_checkbox_component

# Create agent
agent = A2UIAgent()

# Prepare state
state = {
    "messages": [{"role": "user", "content": "Show me a checkbox"}],
    "thread_id": "thread-123",
    "run_id": "run-456"
}

# Stream A2UI events
async for event in agent.run(state):
    # Event is SSE-formatted string
    print(event)
    # Output: data: {"type":"surfaceUpdate",...}\n\n
```

### Creating Custom Components

```python
from protocols.a2ui_types import (
    Component,
    SurfaceUpdate,
    DataModelUpdate,
    BeginRendering,
    create_checkbox_component
)

# Create checkbox
checkbox = create_checkbox_component(
    component_id="my-checkbox",
    label_text="Accept terms",
    value_path="/form/accepted"
)

# Create surface with component
surface_update = SurfaceUpdate(
    surface_id="my-surface",
    components=[checkbox]
)

# Initialize data
data_update = DataModelUpdate(
    surface_id="my-surface",
    path="/form",
    contents=[
        DataContent(key="accepted", value_boolean=False)
    ]
)

# Begin rendering
begin_render = BeginRendering(
    surface_id="my-surface",
    root_component_id="my-checkbox"
)
```

## Component Types

### Checkbox

Interactive checkbox with label and boolean state.

**Structure:**
```json
{
  "id": "checkbox-id",
  "component": {
    "Checkbox": {
      "label": {
        "literalString": "Label text"  // or "path": "/data/path"
      },
      "value": {
        "path": "/data/model/path"
      }
    }
  }
}
```

**Helper:**
```python
from protocols.a2ui_types import create_checkbox_component

checkbox = create_checkbox_component(
    component_id="cb-1",
    label_text="I agree",
    value_path="/form/agreed"
)
```

### Text

Static or dynamic text component.

**Structure:**
```json
{
  "id": "text-id",
  "component": {
    "Text": {
      "content": {
        "literalString": "Text content"  // or "path": "/data/path"
      }
    }
  }
}
```

**Helper:**
```python
from protocols.a2ui_types import create_text_component

text = create_text_component(
    component_id="text-1",
    content="Hello world"
)
```

### Button

Interactive button with action trigger.

**Structure:**
```json
{
  "id": "button-id",
  "component": {
    "Button": {
      "label": {"literalString": "Click me"},
      "onPress": {"action": "action_name"}
    }
  }
}
```

**Helper:**
```python
from protocols.a2ui_types import create_button_component

button = create_button_component(
    component_id="btn-1",
    label_text="Submit",
    action_name="form_submit"
)
```

## Streaming Pattern

A2UI messages are streamed alongside AG-UI events in a unified SSE stream:

```
data: {"type":"surfaceUpdate","surfaceId":"s1",...}       ← A2UI
data: {"type":"dataModelUpdate","surfaceId":"s1",...}     ← A2UI
data: {"type":"beginRendering","surfaceId":"s1",...}      ← A2UI
data: {"type":"TEXT_MESSAGE_START",...}                    ← AG-UI
data: {"type":"TEXT_MESSAGE_CONTENT","delta":"Hello"}      ← AG-UI
data: {"type":"TEXT_MESSAGE_END",...}                      ← AG-UI
```

### Message Ordering

**Critical ordering rules:**

1. **surfaceUpdate** before **dataModelUpdate**
   - Define components before initializing their data

2. **dataModelUpdate** before **beginRendering**
   - Ensure data is ready before rendering

3. **beginRendering** signals "ready to render"
   - Frontend should buffer previous messages until this signal

## API Endpoint

### GET /a2ui/stream

Test endpoint for A2UI agent.

**Parameters:**
- `message` (string, optional): User message (default: "Show me a checkbox")
- `thread_id` (string, optional): Thread ID for conversation context

**Response:**
- `Content-Type`: `text/event-stream`
- Stream of A2UI and AG-UI messages in SSE format

**Example Request:**
```bash
curl -N http://localhost:8000/a2ui/stream?message=Create+a+checkbox
```

**Example Response:**
```
data: {"type":"surfaceUpdate","surfaceId":"surface-abc",...}

data: {"type":"dataModelUpdate","surfaceId":"surface-abc",...}

data: {"type":"beginRendering","surfaceId":"surface-abc",...}

data: {"type":"TEXT_MESSAGE_CONTENT","delta":"Check the box above"}
```

## Best Practices

### 1. Surface Management

- Use unique surface IDs (e.g., `f"surface-{uuid.uuid4().hex[:8]}"`)
- Clean up surfaces with `deleteSurface` when no longer needed
- Keep surfaces focused (one logical UI per surface)

### 2. Component IDs

- Use descriptive IDs (e.g., `"terms-checkbox"` not `"c1"`)
- Ensure uniqueness within a surface
- Use consistent naming conventions

### 3. Data Model Structure

- Use JSON Pointer paths for nested data (`"/form/settings/theme"`)
- Initialize all component values before `beginRendering`
- Keep data model flat when possible

### 4. Streaming Order

Always follow this order:
```python
# 1. Define components
yield encoder.encode(surface_update)

# 2. Initialize data
yield encoder.encode(data_update)

# 3. Signal ready
yield encoder.encode(begin_rendering)

# 4. Send context messages (AG-UI)
yield encoder.encode(text_message)
```

### 5. Mixing A2UI with AG-UI

- Use A2UI for structured UI components
- Use AG-UI for conversational messages
- Combine both for rich interactions

Example:
```python
# A2UI: Create form
yield a2ui_encoder.encode(surface_update)
yield a2ui_encoder.encode(data_update)
yield a2ui_encoder.encode(begin_rendering)

# AG-UI: Explain what to do
yield agui_encoder.encode(text_start)
yield agui_encoder.encode(text_content)
yield agui_encoder.encode(text_end)
```

## Testing

### Unit Tests

Run A2UI protocol tests:
```bash
cd backend
python -m pytest tests/test_a2ui_protocol.py -v
```

Run A2UI agent tests:
```bash
python -m pytest tests/test_a2ui_agent.py -v
```

### Manual Testing

Start the backend server:
```bash
cd backend
python main.py
```

Test the A2UI endpoint:
```bash
curl -N http://localhost:8000/a2ui/stream?message=Show+me+a+checkbox
```

## Future Enhancements

### Extended Component Catalog
- Input fields (text, number, email)
- Dropdown/Select components
- Card layouts
- Tables and lists
- Charts and visualizations

### LLM-Driven UI Generation
- Use structured output from LLMs (Gemini, GPT)
- Dynamic UI based on user queries
- UI templates for common patterns

### User Actions
- Client-to-server action messages
- Form submission handling
- Real-time validation

### Advanced Features
- Custom component catalogs
- Theming system
- Animations and transitions
- Accessibility enhancements

## References

- [A2UI Official Documentation](https://a2ui.org/)
- [A2UI Specification v0.8](https://a2ui.org/specification/v0.8-a2ui/)
- [A2UI GitHub Repository](https://github.com/google/a2ui)
- [AG-UI Protocol in AgentKit](./agui-protocol/README.md)

## Troubleshooting

### Components not rendering

**Problem:** Frontend doesn't display A2UI components

**Solutions:**
1. Check `beginRendering` message is sent after `surfaceUpdate`
2. Verify `rootComponentId` matches an actual component ID
3. Check browser console for parsing errors
4. Verify SSE stream format is correct

### Data binding not working

**Problem:** Component doesn't reflect data model changes

**Solutions:**
1. Verify JSON Pointer paths are correct (e.g., `/form/field` not `form/field`)
2. Check data model is initialized before `beginRendering`
3. Ensure field names match between component and data model

### Mixed event stream issues

**Problem:** A2UI and AG-UI events conflict

**Solutions:**
1. Use `is_a2ui_message()` to distinguish message types
2. Ensure both encoders use SSE format
3. Check `type` field is present and correct in all messages

## Support

For questions or issues:
- Check the implementation plan: `.docs/1-implementation-plans/017-support-a2ui-protocol-plan.md`
- Review backend agent patterns: `.github/agents/backend.agent.md`
- See existing tests for examples
