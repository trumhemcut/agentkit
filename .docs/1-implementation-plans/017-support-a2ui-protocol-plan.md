# Implementation Plan: Support A2UI Protocol

**Requirement**: [017-support-a2ui-protocol.md](../0-requirements/017-support-a2ui-protocol.md)  
**Created**: December 27, 2025  
**Status**: Planning

## Executive Summary

This plan outlines the integration of the **A2UI (Agent-to-UI) protocol** into AgentKit, enabling AI agents to generate dynamic, interactive UI components as JSON that render natively in the frontend. A2UI complements the existing **AG-UI protocol** by adding structured UI rendering capabilities.

**Key Differences**:
- **AG-UI**: Real-time event streaming (text messages, status updates)
- **A2UI**: Declarative UI component generation (checkboxes, forms, cards)

## Protocol Overview

### What is A2UI?

A2UI is an open protocol that allows AI agents to create rich, interactive UIs by sending declarative JSON messages. The protocol is:

- **LLM-Friendly**: Flat component structure with ID references, easy for LLMs to generate
- **Framework-Agnostic**: Abstract component tree that clients map to native widgets
- **Streaming**: Progressive rendering via JSONL/SSE for responsive UX
- **Secure**: JSON data (not executable code) ensures safety

### Core Message Types

1. **surfaceUpdate**: Define UI components (adjacency list model)
2. **dataModelUpdate**: Update application state/data
3. **beginRendering**: Signal client to start rendering from root component
4. **deleteSurface**: Remove a UI surface

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

---

## Implementation Plan

### Phase 1: Backend - A2UI Message Generation

**Owner**: Backend Agent (see [backend.agent.md](../../.github/agents/backend.agent.md))

#### 1.1 A2UI Message Models

**File**: `backend/protocols/a2ui_types.py`

Create Pydantic models for A2UI messages:

```python
from typing import Literal, Optional, Dict, Any, List
from pydantic import BaseModel, Field

# Component model
class Component(BaseModel):
    """Base component with ID and type"""
    id: str
    component: Dict[str, Any]  # e.g., {"Checkbox": {...}}

# Message types
class SurfaceUpdate(BaseModel):
    """Define or update UI components"""
    type: Literal["surfaceUpdate"] = "surfaceUpdate"
    surface_id: str = Field(alias="surfaceId")
    components: List[Component]

class DataModelUpdate(BaseModel):
    """Update data model for components"""
    type: Literal["dataModelUpdate"] = "dataModelUpdate"
    surface_id: str = Field(alias="surfaceId")
    path: Optional[str] = None
    contents: List[Dict[str, Any]]

class BeginRendering(BaseModel):
    """Signal client to start rendering"""
    type: Literal["beginRendering"] = "beginRendering"
    surface_id: str = Field(alias="surfaceId")
    root_component_id: str = Field(alias="rootComponentId")

class DeleteSurface(BaseModel):
    """Remove a UI surface"""
    type: Literal["deleteSurface"] = "deleteSurface"
    surface_id: str = Field(alias="surfaceId")

# Union type for all A2UI messages
A2UIMessage = SurfaceUpdate | DataModelUpdate | BeginRendering | DeleteSurface
```

**Dependencies**: None

#### 1.2 A2UI Encoder

**File**: `backend/protocols/a2ui_encoder.py`

Create encoder to convert A2UI messages to SSE/JSONL format:

```python
import json
from typing import Union
from .a2ui_types import A2UIMessage

class A2UIEncoder:
    """Encode A2UI messages for SSE streaming"""
    
    def encode(self, message: A2UIMessage) -> str:
        """
        Encode A2UI message to SSE format
        
        Returns:
            SSE-formatted string: "data: {json}\n\n"
        """
        json_str = message.model_dump_json(by_alias=True)
        return f"data: {json_str}\n\n"
    
    def encode_jsonl(self, message: A2UIMessage) -> str:
        """
        Encode A2UI message to JSONL format (single line JSON)
        
        Returns:
            JSONL string: "{json}\n"
        """
        json_str = message.model_dump_json(by_alias=True)
        return f"{json_str}\n"
```

**Dependencies**: a2ui_types.py

#### 1.3 A2UI Agent

**File**: `backend/agents/a2ui_agent.py`

Create specialized agent that generates A2UI UI components:

```python
from typing import AsyncGenerator
from .base_agent import BaseAgent, AgentState
from ..protocols.a2ui_types import (
    SurfaceUpdate, DataModelUpdate, BeginRendering, Component
)
from ..protocols.a2ui_encoder import A2UIEncoder
from ..protocols.event_types import EventType
from ag_ui.core import TextMessageContentEvent, RunFinishedEvent
from ag_ui.encoder import EventEncoder
import uuid

class A2UIAgent(BaseAgent):
    """Agent that generates A2UI components"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.a2ui_encoder = A2UIEncoder()
        self.agui_encoder = EventEncoder(accept="text/event-stream")
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Generate checkbox UI example"""
        
        thread_id = state["thread_id"]
        run_id = state["run_id"]
        surface_id = f"surface-{uuid.uuid4().hex[:8]}"
        
        # 1. Create surface with checkbox component
        checkbox_component = Component(
            id="terms-checkbox",
            component={
                "Checkbox": {
                    "label": {"literalString": "I agree to the terms"},
                    "value": {"path": "/form/agreedToTerms"}
                }
            }
        )
        
        surface_update = SurfaceUpdate(
            surface_id=surface_id,
            components=[checkbox_component]
        )
        
        yield self.a2ui_encoder.encode(surface_update)
        
        # 2. Initialize data model
        data_update = DataModelUpdate(
            surface_id=surface_id,
            path="/form",
            contents=[
                {"key": "agreedToTerms", "valueBoolean": False}
            ]
        )
        
        yield self.a2ui_encoder.encode(data_update)
        
        # 3. Begin rendering
        begin_render = BeginRendering(
            surface_id=surface_id,
            root_component_id="terms-checkbox"
        )
        
        yield self.a2ui_encoder.encode(begin_render)
        
        # 4. Send AG-UI text message for context
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        text_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta="Please confirm by checking the box above."
        )
        
        yield self.agui_encoder.encode(text_event)
        
        # 5. Finish run
        finish_event = RunFinishedEvent(
            type=EventType.RUN_FINISHED,
            thread_id=thread_id,
            run_id=run_id
        )
        
        yield self.agui_encoder.encode(finish_event)
```

**Key Features**:
- Generates simple checkbox UI as proof of concept
- Mixes A2UI messages with AG-UI events
- Uses adjacency list component model
- Streams progressively (surface → data → render → text)

**Dependencies**: a2ui_types.py, a2ui_encoder.py, base_agent.py

#### 1.4 Agent Registry Integration

**File**: `backend/agents/agent_registry.py`

Register the A2UI agent:

```python
from .a2ui_agent import A2UIAgent

# In get_agent() or registry initialization
AGENTS = {
    "chat": ChatAgent,
    "canvas": CanvasAgent,
    "a2ui-agent": A2UIAgent,  # Add new agent
}
```

**Dependencies**: a2ui_agent.py

#### 1.5 API Endpoint

**File**: `backend/api/routes.py`

Add endpoint to test A2UI agent:

```python
@router.get("/a2ui/stream")
async def stream_a2ui(
    message: str,
    thread_id: Optional[str] = None
):
    """Stream A2UI UI components via SSE"""
    
    thread_id = thread_id or str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    
    agent = get_agent("a2ui-agent", llm_provider)
    
    state = {
        "messages": [{"role": "user", "content": message}],
        "thread_id": thread_id,
        "run_id": run_id
    }
    
    async def event_stream():
        async for event in agent.run(state):
            yield event
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Dependencies**: agent_registry.py, a2ui_agent.py

---

### Phase 2: Protocol - A2UI Event Types

**Owner**: Protocol Designer (Implementation Planner + Backend Agent)

#### 2.1 A2UI Event Integration with AG-UI

The protocol must support **dual-streaming**:
- **AG-UI events**: Text messages, status updates, agent thinking
- **A2UI messages**: UI components, data model updates

**Event Format**:

```typescript
// AG-UI event (existing)
{
  "type": "TEXT_MESSAGE_CONTENT",
  "message_id": "msg-123",
  "delta": "Here's your UI:"
}

// A2UI message (new)
{
  "type": "surfaceUpdate",
  "surfaceId": "surface-abc",
  "components": [...]
}
```

**Stream Structure**:
```
data: {"type": "RUN_STARTED", ...}       ← AG-UI
data: {"type": "TEXT_MESSAGE_START", ...}  ← AG-UI
data: {"type": "surfaceUpdate", ...}       ← A2UI
data: {"type": "dataModelUpdate", ...}     ← A2UI
data: {"type": "beginRendering", ...}      ← A2UI
data: {"type": "TEXT_MESSAGE_END", ...}    ← AG-UI
data: {"type": "RUN_FINISHED", ...}        ← AG-UI
```

#### 2.2 A2UI Message Validation

**File**: `backend/protocols/a2ui_validator.py`

Create JSON schema validator (optional but recommended):

```python
import jsonschema
from typing import Dict, Any

A2UI_SCHEMA = {
    "oneOf": [
        {"$ref": "#/definitions/surfaceUpdate"},
        {"$ref": "#/definitions/dataModelUpdate"},
        {"$ref": "#/definitions/beginRendering"},
        {"$ref": "#/definitions/deleteSurface"}
    ],
    "definitions": {
        "surfaceUpdate": {
            "type": "object",
            "required": ["type", "surfaceId", "components"],
            "properties": {
                "type": {"const": "surfaceUpdate"},
                "surfaceId": {"type": "string"},
                "components": {"type": "array"}
            }
        },
        # ... other message types
    }
}

def validate_a2ui_message(message: Dict[str, Any]) -> bool:
    """Validate A2UI message against schema"""
    try:
        jsonschema.validate(instance=message, schema=A2UI_SCHEMA)
        return True
    except jsonschema.ValidationError:
        return False
```

---

### Phase 3: Frontend - A2UI Renderer

**Owner**: Frontend Agent (see [frontend.agent.md](../../.github/agents/frontend.agent.md))

#### 3.1 A2UI Message Types

**File**: `frontend/types/a2ui.ts`

Define TypeScript types for A2UI messages:

```typescript
// Component model
export interface A2UIComponent {
  id: string;
  component: Record<string, any>;
}

// Message types
export interface SurfaceUpdate {
  type: "surfaceUpdate";
  surfaceId: string;
  components: A2UIComponent[];
}

export interface DataModelUpdate {
  type: "dataModelUpdate";
  surfaceId: string;
  path?: string;
  contents: Array<{
    key: string;
    valueString?: string;
    valueNumber?: number;
    valueBoolean?: boolean;
    valueMap?: Record<string, any>;
  }>;
}

export interface BeginRendering {
  type: "beginRendering";
  surfaceId: string;
  rootComponentId: string;
}

export interface DeleteSurface {
  type: "deleteSurface";
  surfaceId: string;
}

export type A2UIMessage = 
  | SurfaceUpdate 
  | DataModelUpdate 
  | BeginRendering 
  | DeleteSurface;
```

**Dependencies**: None

#### 3.2 A2UI Surface Store

**File**: `frontend/stores/a2uiStore.ts`

Create Zustand store to manage A2UI surfaces and data models:

```typescript
import { create } from 'zustand';
import type { A2UIComponent, A2UIMessage } from '@/types/a2ui';

interface Surface {
  id: string;
  components: Map<string, A2UIComponent>; // Adjacency list
  dataModel: Record<string, any>;
  rootComponentId?: string;
  isRendering: boolean;
}

interface A2UIStore {
  surfaces: Map<string, Surface>;
  
  // Actions
  createOrUpdateSurface: (surfaceId: string, components: A2UIComponent[]) => void;
  updateDataModel: (surfaceId: string, path: string | undefined, contents: any[]) => void;
  beginRendering: (surfaceId: string, rootComponentId: string) => void;
  deleteSurface: (surfaceId: string) => void;
  getSurface: (surfaceId: string) => Surface | undefined;
}

export const useA2UIStore = create<A2UIStore>((set, get) => ({
  surfaces: new Map(),
  
  createOrUpdateSurface: (surfaceId, components) => {
    set((state) => {
      const surfaces = new Map(state.surfaces);
      const existing = surfaces.get(surfaceId) || {
        id: surfaceId,
        components: new Map(),
        dataModel: {},
        isRendering: false
      };
      
      // Add/update components in adjacency list
      components.forEach((comp) => {
        existing.components.set(comp.id, comp);
      });
      
      surfaces.set(surfaceId, existing);
      return { surfaces };
    });
  },
  
  updateDataModel: (surfaceId, path, contents) => {
    set((state) => {
      const surfaces = new Map(state.surfaces);
      const surface = surfaces.get(surfaceId);
      
      if (!surface) return state;
      
      // Update data model at path
      if (!path || path === '/') {
        // Replace entire model
        const newModel: Record<string, any> = {};
        contents.forEach(({ key, valueString, valueNumber, valueBoolean, valueMap }) => {
          newModel[key] = valueString ?? valueNumber ?? valueBoolean ?? valueMap;
        });
        surface.dataModel = newModel;
      } else {
        // Update at specific path (simplified JSON Pointer)
        const keys = path.split('/').filter(k => k);
        let current = surface.dataModel;
        
        // Navigate to parent
        for (let i = 0; i < keys.length - 1; i++) {
          if (!current[keys[i]]) current[keys[i]] = {};
          current = current[keys[i]];
        }
        
        // Set value
        const lastKey = keys[keys.length - 1];
        contents.forEach(({ key, valueString, valueNumber, valueBoolean, valueMap }) => {
          if (!current[lastKey]) current[lastKey] = {};
          current[lastKey][key] = valueString ?? valueNumber ?? valueBoolean ?? valueMap;
        });
      }
      
      surfaces.set(surfaceId, surface);
      return { surfaces };
    });
  },
  
  beginRendering: (surfaceId, rootComponentId) => {
    set((state) => {
      const surfaces = new Map(state.surfaces);
      const surface = surfaces.get(surfaceId);
      
      if (!surface) return state;
      
      surface.rootComponentId = rootComponentId;
      surface.isRendering = true;
      surfaces.set(surfaceId, surface);
      
      return { surfaces };
    });
  },
  
  deleteSurface: (surfaceId) => {
    set((state) => {
      const surfaces = new Map(state.surfaces);
      surfaces.delete(surfaceId);
      return { surfaces };
    });
  },
  
  getSurface: (surfaceId) => {
    return get().surfaces.get(surfaceId);
  }
}));
```

**Key Features**:
- Manages multiple surfaces (surfaces as separate UI contexts)
- Stores components in adjacency list (Map<id, component>)
- Handles data model updates via JSON Pointer paths
- Tracks rendering state

**Dependencies**: a2ui.ts types

#### 3.3 A2UI Event Handler

**File**: `frontend/hooks/useA2UIEvents.ts`

Hook to process A2UI messages from SSE stream:

```typescript
import { useEffect } from 'react';
import { useA2UIStore } from '@/stores/a2uiStore';
import type { A2UIMessage } from '@/types/a2ui';

export const useA2UIEvents = () => {
  const {
    createOrUpdateSurface,
    updateDataModel,
    beginRendering,
    deleteSurface
  } = useA2UIStore();
  
  const processA2UIMessage = (message: any) => {
    // Type guard to check if message is A2UI (not AG-UI)
    if (!message.type) return;
    
    const a2uiMessage = message as A2UIMessage;
    
    switch (a2uiMessage.type) {
      case 'surfaceUpdate':
        createOrUpdateSurface(
          a2uiMessage.surfaceId,
          a2uiMessage.components
        );
        break;
        
      case 'dataModelUpdate':
        updateDataModel(
          a2uiMessage.surfaceId,
          a2uiMessage.path,
          a2uiMessage.contents
        );
        break;
        
      case 'beginRendering':
        beginRendering(
          a2uiMessage.surfaceId,
          a2uiMessage.rootComponentId
        );
        break;
        
      case 'deleteSurface':
        deleteSurface(a2uiMessage.surfaceId);
        break;
    }
  };
  
  return { processA2UIMessage };
};
```

**Dependencies**: a2uiStore.ts, a2ui.ts

#### 3.4 A2UI Component Renderer

**File**: `frontend/components/A2UI/A2UIRenderer.tsx`

Component to render A2UI surfaces:

```typescript
import React from 'react';
import { useA2UIStore } from '@/stores/a2uiStore';
import { A2UICheckbox } from './components/A2UICheckbox';
import type { A2UIComponent } from '@/types/a2ui';

interface A2UIRendererProps {
  surfaceId: string;
}

export const A2UIRenderer: React.FC<A2UIRendererProps> = ({ surfaceId }) => {
  const surface = useA2UIStore((state) => state.getSurface(surfaceId));
  
  if (!surface || !surface.isRendering || !surface.rootComponentId) {
    return null;
  }
  
  // Recursively render component tree starting from root
  const renderComponent = (componentId: string): React.ReactNode => {
    const component = surface.components.get(componentId);
    if (!component) return null;
    
    // Get component type (first key in component object)
    const [componentType, props] = Object.entries(component.component)[0];
    
    // Map A2UI component types to React components
    switch (componentType) {
      case 'Checkbox':
        return (
          <A2UICheckbox
            key={component.id}
            id={component.id}
            props={props}
            dataModel={surface.dataModel}
            surfaceId={surfaceId}
          />
        );
        
      // Add more component types as needed
      case 'Row':
      case 'Column':
      case 'Card':
        // Implement container components with children
        return null;
        
      default:
        console.warn(`Unknown A2UI component type: ${componentType}`);
        return null;
    }
  };
  
  return (
    <div className="a2ui-surface" data-surface-id={surfaceId}>
      {renderComponent(surface.rootComponentId)}
    </div>
  );
};
```

**Dependencies**: a2uiStore.ts, A2UICheckbox component

#### 3.5 A2UI Checkbox Component

**File**: `frontend/components/A2UI/components/A2UICheckbox.tsx`

Implement checkbox component with data binding:

```typescript
import React from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useA2UIStore } from '@/stores/a2uiStore';

interface A2UICheckboxProps {
  id: string;
  props: {
    label?: { literalString?: string; path?: string };
    value?: { path?: string };
  };
  dataModel: Record<string, any>;
  surfaceId: string;
}

export const A2UICheckbox: React.FC<A2UICheckboxProps> = ({
  id,
  props,
  dataModel,
  surfaceId
}) => {
  const updateDataModel = useA2UIStore((state) => state.updateDataModel);
  
  // Resolve label (literal or from data model)
  const labelText = props.label?.literalString || 
    resolvePath(dataModel, props.label?.path) || 
    'Checkbox';
  
  // Resolve value from data model
  const checked = resolvePath(dataModel, props.value?.path) || false;
  
  // Handle checkbox change
  const handleChange = (newValue: boolean) => {
    if (props.value?.path) {
      // Extract key from path (e.g., "/form/agreedToTerms" → "agreedToTerms")
      const pathParts = props.value.path.split('/').filter(p => p);
      const key = pathParts[pathParts.length - 1];
      const parentPath = '/' + pathParts.slice(0, -1).join('/');
      
      // Update data model
      updateDataModel(surfaceId, parentPath, [
        { key, valueBoolean: newValue }
      ]);
      
      // TODO: Send userAction to backend
      // sendUserAction({ name: "checkbox_changed", context: { [key]: newValue } })
    }
  };
  
  return (
    <div className="flex items-center space-x-2">
      <Checkbox
        id={id}
        checked={checked}
        onCheckedChange={handleChange}
      />
      <Label htmlFor={id}>{labelText}</Label>
    </div>
  );
};

// Helper to resolve JSON Pointer paths
function resolvePath(obj: any, path?: string): any {
  if (!path) return undefined;
  
  const keys = path.split('/').filter(k => k);
  let current = obj;
  
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key];
    } else {
      return undefined;
    }
  }
  
  return current;
}
```

**Key Features**:
- Binds to data model via JSON Pointer paths
- Supports literal and dynamic labels
- Updates data model on user interaction
- Uses Shadcn UI checkbox component

**Dependencies**: Shadcn UI, a2uiStore.ts

#### 3.6 Integration with Chat UI

**File**: `frontend/components/MessageHistory.tsx` (modify)

Integrate A2UI renderer into message history:

```typescript
import { A2UIRenderer } from './A2UI/A2UIRenderer';
import { useA2UIEvents } from '@/hooks/useA2UIEvents';

export const MessageHistory: React.FC<MessageHistoryProps> = ({ messages }) => {
  const { processA2UIMessage } = useA2UIEvents();
  
  // In SSE event handler
  const handleSSEMessage = (event: MessageEvent) => {
    const data = JSON.parse(event.data);
    
    // Check if A2UI message
    if (isA2UIMessage(data)) {
      processA2UIMessage(data);
    } else {
      // Handle AG-UI events (existing logic)
      handleAGUIEvent(data);
    }
  };
  
  return (
    <div>
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      
      {/* Render all active A2UI surfaces */}
      {Array.from(useA2UIStore((s) => s.surfaces.keys())).map((surfaceId) => (
        <A2UIRenderer key={surfaceId} surfaceId={surfaceId} />
      ))}
    </div>
  );
};

function isA2UIMessage(data: any): boolean {
  return [
    'surfaceUpdate',
    'dataModelUpdate',
    'beginRendering',
    'deleteSurface'
  ].includes(data.type);
}
```

---

## Testing Strategy

### Backend Tests

**File**: `backend/tests/test_a2ui_agent.py`

```python
import pytest
from backend.agents.a2ui_agent import A2UIAgent
from backend.protocols.a2ui_types import SurfaceUpdate, DataModelUpdate

@pytest.mark.asyncio
async def test_a2ui_agent_generates_checkbox():
    """Test that A2UI agent generates checkbox component"""
    agent = A2UIAgent(mock_llm_provider)
    
    state = {
        "messages": [{"role": "user", "content": "Show me a checkbox"}],
        "thread_id": "test-thread",
        "run_id": "test-run"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Parse events to check for A2UI messages
    a2ui_events = [e for e in events if "surfaceUpdate" in e or "dataModelUpdate" in e]
    
    assert len(a2ui_events) > 0, "Should generate A2UI messages"
    assert "Checkbox" in str(a2ui_events), "Should contain Checkbox component"
```

### Frontend Tests

**File**: `frontend/tests/A2UIRenderer.test.tsx`

```typescript
import { render, screen } from '@testing-library/react';
import { A2UIRenderer } from '@/components/A2UI/A2UIRenderer';
import { useA2UIStore } from '@/stores/a2uiStore';

describe('A2UIRenderer', () => {
  it('renders checkbox from surface', () => {
    // Setup surface
    useA2UIStore.getState().createOrUpdateSurface('test-surface', [
      {
        id: 'checkbox-1',
        component: {
          Checkbox: {
            label: { literalString: 'Accept terms' },
            value: { path: '/accepted' }
          }
        }
      }
    ]);
    
    useA2UIStore.getState().updateDataModel('test-surface', '/', [
      { key: 'accepted', valueBoolean: false }
    ]);
    
    useA2UIStore.getState().beginRendering('test-surface', 'checkbox-1');
    
    // Render
    render(<A2UIRenderer surfaceId="test-surface" />);
    
    // Assert
    expect(screen.getByText('Accept terms')).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).not.toBeChecked();
  });
});
```

---

## Documentation Updates

### 1. Knowledge Base

**File**: `.docs/2-knowledge-base/a2ui-protocol/README.md`

Create comprehensive A2UI documentation covering:
- Protocol overview and comparison with AG-UI
- Message types and data flow
- Backend implementation patterns
- Frontend integration guide
- Component catalog reference

### 2. Backend Documentation

**File**: `.docs/2-knowledge-base/backend/agents/a2ui-agent.md`

Document A2UIAgent implementation:
- How to create A2UI messages
- Component model best practices
- LLM prompt engineering for UI generation
- Mixing A2UI with AG-UI events

### 3. Frontend Documentation

**File**: `.docs/2-knowledge-base/frontend/a2ui-components.md`

Document A2UI renderer and components:
- How to create custom A2UI components
- Data binding patterns
- Surface lifecycle management
- User interaction handling

---

## Rollout Plan

### Milestone 1: Proof of Concept (Week 1)
- ✅ Research A2UI protocol
- ✅ Create implementation plan
- Backend: Implement A2UI types and encoder
- Backend: Create simple A2UI agent with checkbox
- Frontend: Implement A2UI store and event handler

### Milestone 2: Basic Rendering (Week 2)
- Frontend: Build A2UI renderer and checkbox component
- Backend: Add API endpoint for A2UI agent
- Integration: Connect SSE stream with dual protocol handling
- Testing: Unit tests for backend and frontend

### Milestone 3: Extended Components (Week 3-4)
- Backend: Add more component types (Button, Card, Row, Column)
- Frontend: Implement additional A2UI component renderers
- Backend: Enhance agent to generate complex UIs
- Testing: E2E tests for full A2UI flow

### Milestone 4: LLM Integration (Week 5-6)
- Backend: Add LLM-powered UI generation (structured output)
- Backend: Create prompts for dynamic UI creation
- Frontend: Handle dynamic surface updates
- Documentation: Complete knowledge base updates

---

## Success Criteria

### Functional Requirements
- ✅ Agent can generate checkbox UI component
- ✅ Frontend renders checkbox from A2UI messages
- ✅ User interactions update data model
- ✅ A2UI messages coexist with AG-UI events
- ✅ Multiple surfaces can be managed simultaneously

### Non-Functional Requirements
- Performance: UI renders within 100ms of receiving `beginRendering`
- Type Safety: All A2UI messages are type-checked
- Extensibility: Easy to add new component types
- Documentation: Complete guide for developers

---

## Future Enhancements

1. **Extended Component Catalog**
   - Input, Button, Dropdown, Card, Table
   - Layout components (Row, Column, Stack)
   - Complex components (Form, Chart, Map)

2. **LLM-Driven UI Generation**
   - Structured output mode with Gemini/GPT
   - Dynamic UI based on user queries
   - UI templates for common patterns

3. **User Actions**
   - Client-to-server action messages
   - Event handling and callbacks
   - Form submission and validation

4. **Advanced Features**
   - Custom component catalogs
   - Theming and styling system
   - Animations and transitions
   - Accessibility enhancements

---

## References

- [A2UI Official Documentation](https://a2ui.org/)
- [A2UI Specification v0.8](https://a2ui.org/specification/v0.8-a2ui/)
- [A2UI GitHub Repository](https://github.com/google/a2ui)
- [CopilotKit A2UI Example](https://github.com/copilotkit/with-a2a-a2ui)
- [AG-UI Protocol Documentation](.docs/2-knowledge-base/agui-protocol/README.md)

---

## Notes for Implementation

### Backend Team
1. Follow existing LangGraph patterns in `chat_agent.py`
2. Use AG-UI encoder as reference for A2UI encoder
3. Keep A2UI logic separate from core agent logic
4. Test with Ollama first, then add other LLM providers

### Frontend Team
1. Use Zustand for state management (consistent with existing patterns)
2. Follow Shadcn UI component patterns for A2UI components
3. Ensure type safety with TypeScript throughout
4. Handle SSE reconnection and error states

### Protocol Design
1. A2UI and AG-UI messages must be distinguishable by `type` field
2. Surface IDs should be unique per conversation thread
3. Data model updates should be granular (use paths)
4. `beginRendering` is critical for preventing partial UI flash
