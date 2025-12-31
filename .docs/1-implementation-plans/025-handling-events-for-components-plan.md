# Implementation Plan: Handling Events for Components

**Requirement**: [025-handling-events-for-components.md](../0-requirements/025-handling-events-for-components.md)  
**Created**: December 30, 2025  
**Status**: Planning  
**Dependencies**: 
- [017-support-a2ui-protocol-plan.md](017-support-a2ui-protocol-plan.md) - A2UI protocol foundation
- [018-support-dynamic-frontend-components-plan.md](018-support-dynamic-frontend-components-plan.md) - Dynamic component generation

## Executive Summary

This plan implements **bidirectional communication** for A2UI protocol, enabling the frontend to send user interactions (button clicks, form submissions, checkbox toggles) back to agents for processing. Currently, A2UI only supports one-way rendering from agent to frontend. This plan adds the missing reverse flow.

**Current State**: 
- ✅ Agent generates A2UI components → Frontend renders
- ❌ Frontend user interactions → No mechanism to notify agent

**Target State**:
- ✅ Agent generates A2UI components → Frontend renders
- ✅ Frontend user interactions → Agent processes events → Updates UI

**Key Protocol**: A2UI v0.9 `userAction` messages (client-to-server)

**Implementation Strategy**: 
- **Phase 1**: Implement for `a2ui-loop` agent first as proof-of-concept
- **Phase 2**: After validation, extend to other agents (canvas, salary viewer, etc.)

---

## A2UI v0.9 Protocol: Client-to-Server Messages

According to the [A2UI v0.9 specification](https://a2ui.org/specification/v0.9-a2ui/#client-to-server-messages), the protocol defines how clients send user interactions back to agents.

### `userAction` Message Structure

When a user interacts with a component that has an `action` defined (e.g., Button, CheckBox with onChange), the client sends:

```json
{
  "userAction": {
    "name": "submit_form",
    "surfaceId": "contact_form_1",
    "sourceComponentId": "submit_button",
    "timestamp": "2025-12-30T10:30:00Z",
    "context": {
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
}
```

**Properties**:
- `name` (string, required): The action name defined in the component
- `surfaceId` (string, required): ID of the surface where action originated
- `sourceComponentId` (string, required): ID of the component that triggered the action
- `timestamp` (string, required): ISO 8601 timestamp
- `context` (object, required): Data from the component's action context (e.g., form values resolved from data model paths)

### Two-Way Binding Pattern

According to A2UI v0.9 specification:

1. **Input components** (TextField, CheckBox, Slider) update the **client-side data model** immediately upon user interaction
2. These updates are **local only** - they don't automatically trigger network requests
3. When a **Button** with an `action` is clicked, the client:
   - Resolves all paths in the action's `context` from the current data model
   - Sends a `userAction` message to the server with the resolved values
4. The agent processes the `userAction` and can send new A2UI messages to update the UI

**Example Flow**:
```
1. Agent sends: TextField bound to /user/email
2. User types: "jane@example.com" → Client updates /user/email locally
3. User clicks: Button with action { name: "submit", context: { email: { path: "/user/email" } } }
4. Client sends: userAction with context: { email: "jane@example.com" }
5. Agent processes: Validates email, sends back success/error UI updates
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USER INTERACTION FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

Frontend (React)                Backend (FastAPI)              LangGraph Agent
─────────────────               ──────────────────             ───────────────
                                                                
1. User clicks Button    ─────>                                        
   with action defined                                                  
                                                                        
2. A2UIManager collects  ─────>                                        
   context from data model                                              
                                                                        
3. POST /agents/{id}/action ──> 4. Route receives               
   Body: UserActionRequest        userAction payload                   
                                                                        
                                5. Parse & validate      ────>  6. Agent receives
                                   userAction message              action event
                                                                        
                                                            7. Process action:
                                                               - Validate data
                                                               - Execute logic
                                                               - Update state
                                                                        
                                8. Stream response       <────  9. Generate new
                                   (AG-UI events +                A2UI messages
                                   A2UI updates)                  
                                                                        
10. Receive SSE stream   <─────                                        
    - TEXT_MESSAGE_CHUNK                                                
    - A2UI_MESSAGE (updateDataModel)                                   
    - A2UI_MESSAGE (updateComponents)                                  
                                                                        
11. A2UIManager updates                                                
    data model & re-renders                                             
    components                                                          
```

---

## Implementation Plan

### Phase 1: Backend - A2UI User Action Handling

**Owner**: Backend Agent (see [backend.agent.md](../../.github/agents/backend.agent.md))

#### 1.1 Add Client-to-Server Message Types

**File**: `backend/protocols/a2ui_types.py`

Add Pydantic models for client-to-server messages:

```python
from datetime import datetime

class UserAction(BaseModel):
    """
    Client-to-server message when user interacts with actionable components.
    
    Sent when user clicks a Button, submits a form, or triggers any component
    with an action defined.
    
    Example:
        {
            "userAction": {
                "name": "submit_booking",
                "surfaceId": "booking_form",
                "sourceComponentId": "submit_button",
                "timestamp": "2025-12-30T10:30:00Z",
                "context": {
                    "restaurantName": "The Gourmet",
                    "partySize": "4",
                    "reservationTime": "2025-12-30T19:00:00Z"
                }
            }
        }
    """
    name: str = Field(..., description="Action name from component definition")
    surface_id: str = Field(..., alias="surfaceId")
    source_component_id: str = Field(..., alias="sourceComponentId")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    context: Dict[str, Any] = Field(default_factory=dict, description="Resolved action context data")

    class Config:
        populate_by_name = True


class ErrorMessage(BaseModel):
    """
    Client-to-server message for reporting errors.
    
    Used to report validation failures, rendering errors, or other client-side issues.
    """
    code: str = Field(..., description="Error code (e.g., VALIDATION_FAILED)")
    surface_id: str = Field(..., alias="surfaceId")
    path: str = Field(..., description="JSON Pointer to field that failed")
    message: str = Field(..., description="Human-readable error description")

    class Config:
        populate_by_name = True


# Union type for all client-to-server messages
ClientToServerMessage = UserAction | ErrorMessage
```

**Dependencies**: None  
**Testing**: Unit tests in `backend/tests/test_a2ui_types.py`

---

#### 1.2 Create User Action Endpoint

**File**: `backend/api/routes.py`

Add new endpoint to receive user actions from frontend:

```python
from api.models import UserActionRequest
from protocols.a2ui_types import UserAction

@router.post("/agents/{agent_id}/action")
async def handle_user_action(
    agent_id: str,
    request: UserActionRequest,
    http_request: Request
):
    """
    Handle user actions from A2UI components.
    
    This endpoint receives userAction messages when users interact with 
    actionable components (buttons, form submissions, etc.) in the A2UI interface.
    
    Args:
        agent_id: Agent identifier ("a2ui_agent", "canvas", etc.)
        request: UserActionRequest containing userAction payload
        
    Returns:
        StreamingResponse with AG-UI events and A2UI updates
        
    Example:
        POST /agents/a2ui_agent/action
        {
            "userAction": {
                "name": "submit_form",
                "surfaceId": "contact_form",
                "sourceComponentId": "submit_button",
                "timestamp": "2025-12-30T10:30:00Z",
                "context": {
                    "email": "user@example.com",
                    "name": "John Doe"
                }
            },
            "thread_id": "thread-123",
            "run_id": "run-456"
        }
    """
    logger.info(f"Received userAction for agent={agent_id}: {request.user_action.name}")
    
    # Validate agent exists and supports A2UI
    agent_info = agent_registry.get_agent(agent_id)
    if not agent_info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Check if agent supports A2UI (either "a2ui" or "a2ui-protocol" feature)
    if "a2ui" not in agent_info.features and "a2ui-protocol" not in agent_info.features:
        raise HTTPException(
            status_code=400, 
            detail=f"Agent {agent_id} does not support A2UI actions"
        )
    
    # Get or create graph
    graph = graph_factory.get_graph(agent_id)
    
    # Prepare state with user action
    state = {
        "messages": [],  # No user text message
        "thread_id": request.thread_id,
        "run_id": request.run_id,
        "user_action": request.user_action.model_dump(by_alias=True)  # Add user action to state
    }
    
    async def event_stream():
        """Stream AG-UI events + A2UI updates"""
        encoder = EventEncoder()
        
        try:
            # Send RUN_STARTED
            yield encoder.encode(RunStartedEvent(
                run_id=request.run_id,
                thread_id=request.thread_id
            ))
            
            # Execute graph with user action
            async for chunk in graph.astream(state, {"thread_id": request.thread_id}):
                # Handle different event types
                for node_name, node_output in chunk.items():
                    if "ag_ui_events" in node_output:
                        # AG-UI events (THINKING, TEXT_MESSAGE_CHUNK, etc.)
                        for event in node_output["ag_ui_events"]:
                            yield encoder.encode(event)
                    
                    if "a2ui_messages" in node_output:
                        # A2UI protocol messages (updateComponents, updateDataModel)
                        from protocols.a2ui_encoder import A2UIEncoder
                        a2ui_encoder = A2UIEncoder()
                        for a2ui_msg in node_output["a2ui_messages"]:
                            # Wrap in AG-UI event
                            data_event = DataEvent(
                                run_id=request.run_id,
                                thread_id=request.thread_id,
                                data=a2ui_msg,
                                data_type="a2ui"
                            )
                            yield encoder.encode(data_event)
            
            # Send RUN_FINISHED
            yield encoder.encode(RunFinishedEvent(
                run_id=request.run_id,
                thread_id=request.thread_id
            ))
            
        except Exception as e:
            logger.error(f"Error processing user action: {e}", exc_info=True)
            yield encoder.encode(RunErrorEvent(
                run_id=request.run_id,
                thread_id=request.thread_id,
                error=str(e)
            ))
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Dependencies**: 
- `backend/api/models.py` (new UserActionRequest model)
- `backend/protocols/a2ui_types.py` (UserAction model)
- `backend/agents/agent_registry.py`

**Testing**: Integration tests in `backend/tests/test_a2ui_user_actions.py`

---

#### 1.3 Add Request Model

**File**: `backend/api/models.py`

Add Pydantic model for user action requests:

```python
from protocols.a2ui_types import UserAction

class UserActionRequest(BaseModel):
    """
    Request model for user action endpoint.
    
    Sent from frontend when user interacts with A2UI components.
    """
    user_action: UserAction = Field(..., alias="userAction")
    thread_id: str = Field(..., alias="threadId")
    run_id: str = Field(..., alias="runId")

    class Config:
        populate_by_name = True
```

**Dependencies**: `backend/protocols/a2ui_types.py`  
**Testing**: Covered by endpoint tests

---

#### 1.4 Update Agent Base to Handle User Actions

**File**: `backend/agents/base_agent.py`

Update `AgentState` to include user actions:

```python
from typing import Optional
from protocols.a2ui_types import UserAction

class AgentState(TypedDict):
    """
    Base state for all agents.
    """
    messages: List[Dict[str, str]]
    thread_id: str
    run_id: str
    # New: User action from A2UI components
    user_action: Optional[Dict[str, Any]]  # UserAction as dict
```

**Dependencies**: `backend/protocols/a2ui_types.py`  
**Testing**: Unit tests for state schema

---

#### 1.5 Implement User Action Handler in A2UI Loop Agent

**File**: `backend/agents/a2ui_agent_with_loop.py`

**Priority**: HIGH - This is the PRIMARY target for initial implementation.

Add logic to handle user actions in the a2ui-loop agent node:

```python
async def process_user_action(state: AgentState) -> AgentState:
    """
    Process user action from A2UI components.
    
    This node handles userAction messages sent from the frontend when users
    interact with buttons, forms, or other actionable components.
    
    Args:
        state: Current agent state with user_action field
        
    Returns:
        Updated state with new A2UI messages and AG-UI events
    """
    user_action = state.get("user_action")
    
    if not user_action:
        logger.warning("No user_action in state")
        return state
    
    action_name = user_action.get("name")
    context = user_action.get("context", {})
    surface_id = user_action.get("surfaceId")
    
    logger.info(f"Processing action: {action_name} on surface {surface_id}")
    
    # Generate AG-UI thinking event
    ag_ui_events = [
        ThinkingEvent(
            run_id=state["run_id"],
            thread_id=state["thread_id"],
            message=f"Processing your request: {action_name}"
        )
    ]
    
    # Handle specific actions
    a2ui_messages = []
    
    if action_name == "submit_form":
        # Example: Process form submission
        email = context.get("email")
        name = context.get("name")
        
        # Validate
        if not email or "@" not in email:
            # Send error via A2UI dataModelUpdate
            a2ui_messages.append(UpdateDataModel(
                surface_id=surface_id,
                path="/errors/email",
                op="replace",
                value={"message": "Invalid email address"}
            ))
        else:
            # Success: Update UI to show confirmation
            a2ui_messages.extend([
                # Update data model
                UpdateDataModel(
                    surface_id=surface_id,
                    path="/submission",
                    op="replace",
                    value={"status": "success", "message": f"Thanks {name}!"}
                ),
                # Add success message component
                UpdateComponents(
                    surface_id=surface_id,
                    components=[
                        Component(
                            id="success_message",
                            component={
                                "Text": {
                                    "text": {"path": "/submission/message"},
                                    "style": {"color": "green"}
                                }
                            }
                        )
                    ]
                )
            ])
            
            # AG-UI text message
            ag_ui_events.append(
                TextMessageChunkEvent(
                    run_id=state["run_id"],
                    thread_id=state["thread_id"],
                    chunk=f"Form submitted successfully! Email: {email}"
                )
            )
    
    elif action_name == "book_restaurant":
        # Example: Handle restaurant booking
        restaurant_name = context.get("restaurantName")
        
        # Use LLM to process the booking request
        llm_response = await call_llm_with_action_context(
            action_name=action_name,
            context=context
        )
        
        # Generate new A2UI based on LLM response
        # ... (parse LLM response and create A2UI messages)
    
    else:
        # Generic action handler
        logger.info(f"Generic handler for action: {action_name}")
        
        # Echo back the action context
        ag_ui_events.append(
            TextMessageChunkEvent(
                run_id=state["run_id"],
                thread_id=state["thread_id"],
                chunk=f"Received action '{action_name}' with data: {context}"
            )
        )
    
    return {
        **state,
        "ag_ui_events": ag_ui_events,
        "a2ui_messages": a2ui_messages
    }


async def call_llm_with_action_context(action_name: str, context: Dict[str, Any]) -> str:
    """
    Call LLM to process user action with context.
    
    This allows the agent to use the LLM to decide how to respond to user actions,
    potentially generating new UI components or updating data models.
    """
    prompt = f"""
    User performed action: {action_name}
    Context data: {json.dumps(context, indent=2)}
    
    Generate a response that includes:
    1. Text feedback to the user
    2. Any UI updates needed (describe what to update)
    
    Return your response in this format:
    TEXT: <your text response>
    UI_UPDATES: <description of what to update in the UI>
    """
    
    llm = get_llm_instance()
    response = await llm.ainvoke(prompt)
    
    return response
```

**Key Patterns**:
1. **Action Routing**: Use `action_name` to route to specific handlers
2. **Context Extraction**: Extract data from `context` dict (already resolved by client)
3. **Validation**: Validate data and send error updates via `updateDataModel`
4. **Response**: Generate both AG-UI events (text feedback) and A2UI messages (UI updates)
5. **LLM Integration**: Optionally use LLM to decide how to respond

**Dependencies**: 
- `backend/protocols/a2ui_types.py`
- `backend/llm/provider_factory.py`

**Testing**: Integration tests with mock LLM responses

---

#### 1.6 Update A2UI Loop Graph to Route User Actions

**File**: `backend/graphs/a2ui_loop_graph.py`

**Priority**: HIGH - Focus on a2ui_loop_graph first, other graphs later.

Update the a2ui-loop graph to detect and route user actions:

```python
def create_a2ui_loop_graph():
    """
    Create A2UI agent graph with user action handling.
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("detect_input_type", detect_input_type)
    workflow.add_node("process_text_input", process_text_input)
    workflow.add_node("process_user_action", process_user_action)  # NEW
    workflow.add_node("generate_response", generate_response)
    
    # Entry point
    workflow.set_entry_point("detect_input_type")
    
    # Conditional routing
    def route_input(state: AgentState) -> str:
        """Route based on whether we have text input or user action"""
        if state.get("user_action"):
            return "process_user_action"
        else:
            return "process_text_input"
    
    workflow.add_conditional_edges(
        "detect_input_type",
        route_input,
        {
            "process_text_input": "process_text_input",
            "process_user_action": "process_user_action"
        }
    )
    
    # Both paths lead to response generation
    workflow.add_edge("process_text_input", "generate_response")
    workflow.add_edge("process_user_action", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()
```

**Dependencies**: `backend/agents/a2ui_agent_with_loop.py`  
**Testing**: Graph execution tests with user action inputs

---

### Phase 2: Protocol - Action Definitions in Components

**Owner**: Backend Agent (Protocol Design)

#### 2.1 Update Component Helper Functions

**File**: `backend/protocols/a2ui_types.py`

Add helper functions to create components with actions:

```python
def create_button_component(
    component_id: str,
    label: str,
    action_name: str,
    action_context: Optional[Dict[str, Any]] = None,
    style: Optional[Dict[str, Any]] = None
) -> Component:
    """
    Create a Button component with action.
    
    Args:
        component_id: Unique component ID
        label: Button text
        action_name: Name of action to trigger on click
        action_context: Data to send with action (paths or literal values)
        style: Optional style properties
        
    Example:
        create_button_component(
            component_id="submit_btn",
            label="Submit Form",
            action_name="submit_form",
            action_context={
                "email": {"path": "/user/email"},
                "name": {"path": "/user/name"}
            }
        )
    """
    button_props = {
        "child": f"{component_id}_label",
        "action": {
            "name": action_name,
            "context": action_context or {}
        }
    }
    
    if style:
        button_props["style"] = style
    
    return Component(
        id=component_id,
        component={"Button": button_props}
    )


def create_checkbox_component(
    component_id: str,
    label: str,
    value_path: str,
    on_change_action: Optional[str] = None,
    on_change_context: Optional[Dict[str, Any]] = None
) -> Component:
    """
    Create a CheckBox component with optional onChange action.
    
    Args:
        component_id: Unique component ID
        label: Checkbox label
        value_path: JSON Pointer to boolean value in data model
        on_change_action: Optional action name to trigger on value change
        on_change_context: Optional context to send with onChange
        
    Example:
        create_checkbox_component(
            component_id="agree_terms",
            label="I agree to terms",
            value_path="/form/agreed",
            on_change_action="validate_form",
            on_change_context={"field": "terms"}
        )
    """
    checkbox_props = {
        "label": {"literalString": label},
        "value": {"path": value_path}
    }
    
    if on_change_action:
        checkbox_props["onChange"] = {
            "name": on_change_action,
            "context": on_change_context or {}
        }
    
    return Component(
        id=component_id,
        component={"CheckBox": checkbox_props}
    )


def create_text_field_component(
    component_id: str,
    label: str,
    text_path: str,
    placeholder: Optional[str] = None,
    usage_hint: str = "shortText"
) -> Component:
    """
    Create a TextField component with two-way binding.
    
    TextField automatically updates the data model at text_path as user types.
    No action needed for typing - actions are for form submission.
    
    Args:
        component_id: Unique component ID
        label: Field label
        text_path: JSON Pointer to string value in data model
        placeholder: Optional placeholder text
        usage_hint: Type hint ("shortText", "longText", "email", "password")
    """
    text_field_props = {
        "label": {"literalString": label},
        "text": {"path": text_path},
        "usageHint": usage_hint
    }
    
    if placeholder:
        text_field_props["placeholder"] = {"literalString": placeholder}
    
    return Component(
        id=component_id,
        component={"TextField": text_field_props}
    )
```

**Key Concepts**:
- **Button**: Always has an `action` with `name` and `context`
- **TextField/CheckBox**: Use two-way binding (no action needed for input)
- **Context Paths**: Use `{"path": "/data/model/path"}` to reference data model values
- **Context Literals**: Use literal values for static data

**Dependencies**: None  
**Testing**: Unit tests for component creation

---

### Phase 3: Frontend - A2UI User Action Client

**Owner**: Frontend Agent (see [frontend.agent.md](../../.github/agents/frontend.agent.md))

#### 3.1 Create UserAction Service

**File**: `frontend/services/a2uiUserActions.ts`

Create service to send user actions to backend:

```typescript
import { apiClient } from './api';

/**
 * UserAction message structure (A2UI v0.9)
 */
export interface UserAction {
  name: string;
  surfaceId: string;
  sourceComponentId: string;
  timestamp: string;
  context: Record<string, any>;
}

/**
 * Request payload for user action endpoint
 */
export interface UserActionRequest {
  userAction: UserAction;
  threadId: string;
  runId: string;
}

/**
 * A2UI User Action Service
 * 
 * Handles sending user actions from A2UI components to the backend.
 */
export class A2UIUserActionService {
  /**
   * Send a user action to the backend
   * 
   * @param agentId - Agent identifier
   * @param action - User action details
   * @param threadId - Thread ID for conversation context
   * @param runId - Run ID for this execution
   * @returns EventSource for streaming response
   */
  static sendAction(
    agentId: string,
    action: UserAction,
    threadId: string,
    runId: string
  ): EventSource {
    const url = `/agents/${agentId}/action`;
    
    // POST action and get SSE stream back
    const eventSource = apiClient.postWithSSE<UserActionRequest>(url, {
      userAction: action,
      threadId,
      runId
    });
    
    return eventSource;
  }
  
  /**
   * Create a UserAction from component interaction
   * 
   * @param actionName - Name of the action from component definition
   * @param surfaceId - ID of the surface containing the component
   * @param componentId - ID of the component that triggered the action
   * @param context - Resolved context data from data model
   * @returns UserAction object ready to send
   */
  static createUserAction(
    actionName: string,
    surfaceId: string,
    componentId: string,
    context: Record<string, any>
  ): UserAction {
    return {
      name: actionName,
      surfaceId,
      sourceComponentId: componentId,
      timestamp: new Date().toISOString(),
      context
    };
  }
}
```

**Dependencies**: `frontend/services/api.ts`  
**Testing**: Unit tests with mock API responses

---

#### 3.2 Update A2UIManager to Handle Actions

**File**: `frontend/lib/a2ui/A2UIManager.ts`

Update A2UIManager to detect and process component actions:

```typescript
import { A2UIUserActionService, UserAction } from '@/services/a2uiUserActions';

export class A2UIManager {
  private surfaces: Map<string, Surface>;
  private dataModels: Map<string, any>;
  private actionCallbacks: Map<string, (action: UserAction) => void>;
  
  constructor() {
    this.surfaces = new Map();
    this.dataModels = new Map();
    this.actionCallbacks = new Map();
  }
  
  /**
   * Register callback for when user actions occur
   */
  onAction(surfaceId: string, callback: (action: UserAction) => void): void {
    this.actionCallbacks.set(surfaceId, callback);
  }
  
  /**
   * Handle component action (called by rendered components)
   * 
   * This is called when a user clicks a Button or interacts with
   * any component that has an action defined.
   */
  handleComponentAction(
    surfaceId: string,
    componentId: string,
    actionName: string,
    actionContext: Record<string, any>
  ): void {
    // Resolve context paths from data model
    const resolvedContext = this.resolveActionContext(surfaceId, actionContext);
    
    // Create user action
    const userAction = A2UIUserActionService.createUserAction(
      actionName,
      surfaceId,
      componentId,
      resolvedContext
    );
    
    // Notify callback
    const callback = this.actionCallbacks.get(surfaceId);
    if (callback) {
      callback(userAction);
    } else {
      console.warn(`No action callback registered for surface: ${surfaceId}`);
    }
  }
  
  /**
   * Resolve action context by replacing path references with actual values
   * 
   * @param surfaceId - Surface ID to get data model from
   * @param context - Context from component action definition
   * @returns Resolved context with actual values
   * 
   * Example:
   *   Input:  { email: { path: "/user/email" }, literal: "value" }
   *   Output: { email: "user@example.com", literal: "value" }
   */
  private resolveActionContext(
    surfaceId: string,
    context: Record<string, any>
  ): Record<string, any> {
    const dataModel = this.dataModels.get(surfaceId) || {};
    const resolved: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(context)) {
      if (typeof value === 'object' && value.path) {
        // It's a path reference - resolve from data model
        resolved[key] = this.getValueAtPath(dataModel, value.path);
      } else {
        // It's a literal value
        resolved[key] = value;
      }
    }
    
    return resolved;
  }
  
  /**
   * Get value from data model using JSON Pointer path
   */
  private getValueAtPath(dataModel: any, path: string): any {
    if (!path || path === '/') return dataModel;
    
    const parts = path.split('/').filter(p => p.length > 0);
    let current = dataModel;
    
    for (const part of parts) {
      if (current === undefined || current === null) return undefined;
      current = current[part];
    }
    
    return current;
  }
  
  /**
   * Update data model value at path (for two-way binding)
   * 
   * Called when TextField/CheckBox/etc. values change.
   */
  updateDataModelValue(surfaceId: string, path: string, value: any): void {
    const dataModel = this.dataModels.get(surfaceId) || {};
    this.setValueAtPath(dataModel, path, value);
    this.dataModels.set(surfaceId, dataModel);
    
    // Trigger re-render of components bound to this path
    this.notifyDataModelUpdate(surfaceId, path);
  }
  
  private setValueAtPath(dataModel: any, path: string, value: any): void {
    if (!path || path === '/') {
      throw new Error('Cannot set root path');
    }
    
    const parts = path.split('/').filter(p => p.length > 0);
    let current = dataModel;
    
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!(part in current)) {
        current[part] = {};
      }
      current = current[part];
    }
    
    current[parts[parts.length - 1]] = value;
  }
  
  private notifyDataModelUpdate(surfaceId: string, path: string): void {
    // Emit event for components to re-render
    window.dispatchEvent(new CustomEvent('a2ui-data-update', {
      detail: { surfaceId, path }
    }));
  }
}
```

**Key Methods**:
- `handleComponentAction()`: Called by rendered components when user interacts
- `resolveActionContext()`: Resolves paths to actual values before sending
- `updateDataModelValue()`: Updates local data model for two-way binding
- `onAction()`: Registers callback for when actions occur

**Dependencies**: 
- `frontend/services/a2uiUserActions.ts`
- `frontend/types/a2ui.ts`

**Testing**: Unit tests for path resolution and action handling

---

#### 3.3 Update A2UI Component Renderer

**File**: `frontend/components/a2ui/A2UIComponentRenderer.tsx`

Update renderer to handle button clicks and other actions:

```typescript
import { A2UIManager } from '@/lib/a2ui/A2UIManager';

interface A2UIComponentRendererProps {
  component: A2UIComponent;
  surfaceId: string;
  a2uiManager: A2UIManager;
}

export const A2UIComponentRenderer: React.FC<A2UIComponentRendererProps> = ({
  component,
  surfaceId,
  a2uiManager
}) => {
  const componentType = Object.keys(component.component)[0];
  const props = component.component[componentType];
  
  switch (componentType) {
    case 'Button':
      return (
        <Button
          onClick={() => {
            if (props.action) {
              // Trigger user action
              a2uiManager.handleComponentAction(
                surfaceId,
                component.id,
                props.action.name,
                props.action.context || {}
              );
            }
          }}
        >
          {props.child || props.label}
        </Button>
      );
    
    case 'TextField':
      return (
        <Input
          placeholder={props.placeholder?.literalString}
          value={a2uiManager.getValueAtPath(surfaceId, props.text.path) || ''}
          onChange={(e) => {
            // Two-way binding: update data model immediately
            a2uiManager.updateDataModelValue(
              surfaceId,
              props.text.path,
              e.target.value
            );
          }}
        />
      );
    
    case 'CheckBox':
      return (
        <Checkbox
          checked={a2uiManager.getValueAtPath(surfaceId, props.value.path) || false}
          onCheckedChange={(checked) => {
            // Update data model
            a2uiManager.updateDataModelValue(
              surfaceId,
              props.value.path,
              checked
            );
            
            // If onChange action is defined, trigger it
            if (props.onChange) {
              a2uiManager.handleComponentAction(
                surfaceId,
                component.id,
                props.onChange.name,
                props.onChange.context || {}
              );
            }
          }}
        >
          {props.label.literalString}
        </Checkbox>
      );
    
    // ... other component types
  }
};
```

**Key Behaviors**:
- **Button**: Triggers `handleComponentAction()` on click
- **TextField**: Updates data model on every keystroke (two-way binding)
- **CheckBox**: Updates data model + optionally triggers onChange action

**Dependencies**: 
- `frontend/lib/a2ui/A2UIManager.ts`
- `frontend/components/ui/*` (Shadcn UI components)

**Testing**: Component tests with user interactions

---

#### 3.4 Integrate Action Handling in Chat Component

**File**: `frontend/components/chat/ChatInterface.tsx`

Update chat component to handle user actions:

```typescript
import { A2UIManager } from '@/lib/a2ui/A2UIManager';
import { A2UIUserActionService } from '@/services/a2uiUserActions';
import { useAgentStream } from '@/hooks/useAgentStream';

export const ChatInterface = () => {
  const a2uiManager = useRef(new A2UIManager()).current;
  const { startStream, stopStream } = useAgentStream();
  
  // Register action handler for all surfaces
  useEffect(() => {
    const handleUserAction = async (action: UserAction) => {
      console.log('User action triggered:', action);
      
      // Generate new run ID for this action
      const runId = `run-${Date.now()}`;
      
      // Send action to backend and get SSE stream
      const eventSource = A2UIUserActionService.sendAction(
        currentAgentId,
        action,
        threadId,
        runId
      );
      
      // Handle events from stream
      startStream(eventSource, {
        onMessage: (event) => {
          // Handle AG-UI events
          if (event.type === 'TEXT_MESSAGE_CHUNK') {
            appendToMessage(event.chunk);
          }
        },
        onA2UIMessage: (a2uiMsg) => {
          // Handle A2UI updates
          a2uiManager.processMessage(a2uiMsg);
        },
        onComplete: () => {
          console.log('Action processing complete');
        },
        onError: (error) => {
          console.error('Action error:', error);
        }
      });
    };
    
    // Register for all surfaces (could be surface-specific)
    a2uiManager.onAction('*', handleUserAction);
    
    return () => {
      // Cleanup
    };
  }, [currentAgentId, threadId]);
  
  return (
    <div>
      {/* Chat messages */}
      <ChatMessages messages={messages} a2uiManager={a2uiManager} />
      
      {/* Input */}
      <ChatInput onSend={handleSendMessage} />
    </div>
  );
};
```

**Flow**:
1. User clicks button in A2UI component
2. Component calls `a2uiManager.handleComponentAction()`
3. Manager resolves context and creates UserAction
4. Manager calls registered callback with UserAction
5. ChatInterface sends UserAction to backend via API
6. Backend streams back response (AG-UI + A2UI updates)
7. Frontend processes updates and re-renders

**Dependencies**: 
- `frontend/lib/a2ui/A2UIManager.ts`
- `frontend/services/a2uiUserActions.ts`
- `frontend/hooks/useAgentStream.ts`

**Testing**: E2E tests with user interactions

---

### Phase 4: Integration & Testing

**Owner**: Backend Agent + Frontend Agent

#### 4.1 Backend Integration Tests

**File**: `backend/tests/test_a2ui_user_actions.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app

def test_user_action_endpoint_exists():
    """Test that user action endpoint is registered"""
    client = TestClient(app)
    response = client.post("/agents/a2ui_agent/action", json={
        "userAction": {
            "name": "test_action",
            "surfaceId": "test_surface",
            "sourceComponentId": "test_component",
            "timestamp": "2025-12-30T10:00:00Z",
            "context": {}
        },
        "threadId": "test-thread",
        "runId": "test-run"
    })
    
    # Should not be 404 (might be 500 if not fully implemented)
    assert response.status_code != 404


def test_button_click_action():
    """Test processing a button click action"""
    client = TestClient(app)
    response = client.post("/agents/a2ui_agent/action", json={
        "userAction": {
            "name": "submit_form",
            "surfaceId": "form_surface",
            "sourceComponentId": "submit_button",
            "timestamp": "2025-12-30T10:00:00Z",
            "context": {
                "email": "test@example.com",
                "name": "Test User"
            }
        },
        "threadId": "thread-123",
        "runId": "run-456"
    })
    
    assert response.status_code == 200
    
    # Check SSE stream contains expected events
    events = list(response.iter_lines())
    assert any(b"RUN_STARTED" in line for line in events)
    assert any(b"TEXT_MESSAGE_CHUNK" in line for line in events)


def test_invalid_agent_id():
    """Test error handling for invalid agent ID"""
    client = TestClient(app)
    response = client.post("/agents/nonexistent_agent/action", json={
        "userAction": {
            "name": "test",
            "surfaceId": "test",
            "sourceComponentId": "test",
            "timestamp": "2025-12-30T10:00:00Z",
            "context": {}
        },
        "threadId": "test",
        "runId": "test"
    })
    
    assert response.status_code == 404
```

**Dependencies**: 
- `backend/api/routes.py`
- `backend/agents/a2ui_agent_with_loop.py`

---

#### 4.2 Frontend Integration Tests

**File**: `frontend/tests/a2ui/userActions.test.ts`

```typescript
import { A2UIManager } from '@/lib/a2ui/A2UIManager';
import { A2UIUserActionService } from '@/services/a2uiUserActions';

describe('A2UI User Actions', () => {
  it('should resolve action context from data model', () => {
    const manager = new A2UIManager();
    
    // Setup surface with data model
    manager.processMessage({
      createSurface: {
        surfaceId: 'test_surface',
        catalogId: 'https://a2ui.dev/standard'
      }
    });
    
    manager.processMessage({
      updateDataModel: {
        surfaceId: 'test_surface',
        path: '/',
        op: 'replace',
        value: {
          user: {
            email: 'test@example.com',
            name: 'Test User'
          }
        }
      }
    });
    
    // Resolve context with paths
    const context = manager['resolveActionContext']('test_surface', {
      email: { path: '/user/email' },
      name: { path: '/user/name' },
      literal: 'static_value'
    });
    
    expect(context).toEqual({
      email: 'test@example.com',
      name: 'Test User',
      literal: 'static_value'
    });
  });
  
  it('should trigger action callback on button click', () => {
    const manager = new A2UIManager();
    const mockCallback = jest.fn();
    
    manager.onAction('test_surface', mockCallback);
    
    // Simulate button click
    manager.handleComponentAction(
      'test_surface',
      'submit_button',
      'submit_form',
      { field: 'value' }
    );
    
    expect(mockCallback).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'submit_form',
        surfaceId: 'test_surface',
        sourceComponentId: 'submit_button',
        context: { field: 'value' }
      })
    );
  });
});
```

**Dependencies**: 
- `frontend/lib/a2ui/A2UIManager.ts`
- `frontend/services/a2uiUserActions.ts`

---

#### 4.3 End-to-End Test Scenario

**Test Case**: Form Submission with Validation

**Scenario**:
1. Agent sends A2UI form with TextField and Button
2. User types in TextField → data model updates locally
3. User clicks Submit Button
4. Frontend sends userAction to backend
5. Backend validates, sends success/error UI update
6. Frontend renders updated UI

**Files**:
- `backend/tests/test_e2e_form_submission.py`
- `frontend/tests/e2e/formSubmission.test.ts`

---

## Example Implementation: Restaurant Booking

Following the pattern from the Google A2UI sample, here's a complete example:

### Backend Agent Logic

```python
async def handle_restaurant_booking_action(state: AgentState) -> AgentState:
    """Handle restaurant booking user action"""
    user_action = state.get("user_action")
    action_name = user_action.get("name")
    context = user_action.get("context", {})
    surface_id = user_action.get("surfaceId")
    
    if action_name == "book_restaurant":
        # User clicked "Book" button on restaurant card
        restaurant_name = context.get("restaurantName")
        
        # Generate booking form
        a2ui_messages = [
            CreateSurface(
                surface_id="booking_form",
                catalog_id="https://a2ui.dev/standard"
            ),
            UpdateComponents(
                surface_id="booking_form",
                components=[
                    create_column_component("root", children=[
                        "restaurant_info",
                        "party_size_field",
                        "time_field",
                        "submit_button"
                    ]),
                    create_text_component(
                        "restaurant_info",
                        text=f"Booking: {restaurant_name}"
                    ),
                    create_text_field_component(
                        "party_size_field",
                        label="Party Size",
                        text_path="/booking/partySize"
                    ),
                    create_text_field_component(
                        "time_field",
                        label="Reservation Time",
                        text_path="/booking/time"
                    ),
                    create_button_component(
                        "submit_button",
                        label="Submit Booking",
                        action_name="submit_booking",
                        action_context={
                            "restaurantName": restaurant_name,
                            "partySize": {"path": "/booking/partySize"},
                            "time": {"path": "/booking/time"}
                        }
                    )
                ]
            ),
            UpdateDataModel(
                surface_id="booking_form",
                path="/",
                op="replace",
                value={
                    "booking": {
                        "partySize": "",
                        "time": ""
                    }
                }
            )
        ]
        
        return {
            **state,
            "a2ui_messages": a2ui_messages,
            "ag_ui_events": [
                TextMessageChunkEvent(
                    run_id=state["run_id"],
                    thread_id=state["thread_id"],
                    chunk=f"Please fill out the booking form for {restaurant_name}"
                )
            ]
        }
    
    elif action_name == "submit_booking":
        # User submitted booking form
        restaurant_name = context.get("restaurantName")
        party_size = context.get("partySize")
        time = context.get("time")
        
        # Validate
        if not party_size or not time:
            return {
                **state,
                "a2ui_messages": [
                    UpdateDataModel(
                        surface_id="booking_form",
                        path="/error",
                        op="replace",
                        value={"message": "Please fill all fields"}
                    )
                ]
            }
        
        # Success
        return {
            **state,
            "a2ui_messages": [
                DeleteSurface(surface_id="booking_form"),
                UpdateComponents(
                    surface_id=surface_id,
                    components=[
                        create_text_component(
                            "success_msg",
                            text=f"✅ Booking confirmed for {restaurant_name}!"
                        )
                    ]
                )
            ],
            "ag_ui_events": [
                TextMessageChunkEvent(
                    run_id=state["run_id"],
                    thread_id=state["thread_id"],
                    chunk=f"Your booking for {party_size} people at {time} is confirmed!"
                )
            ]
        }
```

---

## Testing Strategy

### Unit Tests
- [ ] A2UI message type validation
- [ ] Path resolution in A2UIManager
- [ ] Action context resolution
- [ ] Component helper functions

### Integration Tests
- [ ] User action endpoint receives and processes actions
- [ ] Graph routes user actions correctly
- [ ] A2UI messages stream properly in response

### E2E Tests
- [ ] Form submission flow (type → click → validate → update)
- [ ] Button action triggers backend processing
- [ ] Error handling and validation feedback
- [ ] Multiple surfaces and actions

---

## Documentation Updates

### Files to Update

1. **`backend/README.md`**: Document user action endpoint and patterns
2. **`backend/protocols/README.md`**: Document UserAction message structure
3. **`frontend/README.md`**: Document A2UIManager action handling
4. **`.docs/2-knowledge-base/a2ui-protocol.md`**: Add bidirectional communication patterns
5. **`.docs/2-knowledge-base/agent-patterns.md`**: Add user action handler patterns

---

## Rollout Plan

### Phase 1: Proof of Concept - A2UI Loop Agent Only (Week 1)
**Goal**: Get bidirectional communication working for a2ui-loop agent first

#### Backend (Days 1-3)
- [ ] Implement UserAction types and models
- [ ] Add user action endpoint (`/agents/{agent_id}/action`)
- [ ] Update AgentState to include user_action field
- [ ] Implement action handler in `a2ui_agent_with_loop.py`
- [ ] Update `a2ui_loop_graph.py` to route user actions
- [ ] Add action properties to component helpers (Button, CheckBox)

#### Frontend (Days 3-5)
- [ ] Implement A2UIUserActionService
- [ ] Update A2UIManager with action handling and context resolution
- [ ] Add action triggers to A2UI component renderer
- [ ] Integrate action callbacks in ChatInterface for a2ui-loop

#### Testing (Days 5-7)
- [ ] Unit tests for UserAction models and path resolution
- [ ] Integration tests for a2ui-loop action endpoint
- [ ] Manual testing with a2ui-loop agent
- [ ] Create simple test case (e.g., button click → text response)

### Phase 2: Validation & Refinement (Week 2)
**Goal**: Test thoroughly with a2ui-loop and refine based on findings

- [ ] E2E testing with multiple action types (button, checkbox, form)
- [ ] Error handling and validation
- [ ] Performance testing
- [ ] Documentation for a2ui-loop patterns
- [ ] Bug fixes and improvements

### Phase 3: Extension to Other Agents (Week 3+)
**Goal**: After a2ui-loop is stable, extend to other agents

- [ ] Extend to Canvas agent (if it uses A2UI)
- [ ] Extend to Salary Viewer agent
- [ ] Extend to other A2UI-enabled agents
- [ ] Update all agent graphs with action routing
- [ ] Comprehensive testing across all agents

### Phase 4: Production Readiness (Week 4)
- [ ] Security review
- [ ] Performance optimization
- [ ] Monitoring and logging
- [ ] Complete documentation
- [ ] Knowledge base updates

---

## Success Criteria

### Phase 1 Success Criteria (A2UI Loop Agent)

✅ **Backend**:
- User action endpoint accepts and processes actions for a2ui-loop agent
- `a2ui_agent_with_loop.py` can handle user actions and generate UI updates
- `a2ui_loop_graph.py` properly routes user actions vs text inputs
- Action handlers work for at least 2 action types (e.g., button click, form submit)

✅ **Frontend**:
- User clicks on Button in a2ui-loop generated UI → userAction sent
- A2UIManager resolves context paths from data model
- TextField two-way binding updates data model locally
- Action responses from a2ui-loop update UI correctly

✅ **Integration**:
- Complete round-trip works for a2ui-loop: user clicks → backend processes → UI updates
- Error handling works (e.g., validation errors shown in UI)
- Manual testing confirms bidirectional flow

✅ **Testing**:
- Unit tests pass for UserAction models
- Integration test for `/agents/a2ui-loop/action` endpoint
- Manual E2E test with simple button click scenario

### Phase 3 Success Criteria (All Agents)

✅ **All A2UI agents** support user action handling
✅ **Comprehensive tests** cover multiple agents and scenarios
✅ **Documentation** complete for all patterns

---

## References

### A2UI v0.9 Specification
- [Client-to-Server Messages](https://a2ui.org/specification/v0.9-a2ui/#client-to-server-messages)
- [Two-Way Binding](https://a2ui.org/specification/v0.9-a2ui/#two-way-binding-input-components)
- [Data Binding & Scope](https://a2ui.org/specification/v0.9-a2ui/#data-binding-scope-and-state-management)

### Sample Implementation
- [Google A2UI Restaurant Finder](https://github.com/google/A2UI/blob/main/samples/agent/adk/restaurant_finder/agent_executor.py)

### Internal Documentation
- [Backend Agent Patterns](../../.github/agents/backend.agent.md)
- [Frontend AG-UI Patterns](../../.github/agents/frontend.agent.md)
- [A2UI Protocol Plan](017-support-a2ui-protocol-plan.md)
- [Dynamic Components Plan](018-support-dynamic-frontend-components-plan.md)

---

## Notes for Implementation

### Key Considerations

1. **State Management**: User actions don't carry full conversation history - they only contain the action context. The agent should maintain conversation state in LangGraph memory.

2. **Error Handling**: Always validate user input server-side. Use `updateDataModel` to send error messages back to UI.

3. **Security**: Sanitize all user input from action context before processing.

4. **Performance**: Consider debouncing for rapid user actions (e.g., typing in TextField).

5. **Extensibility**: Design action handlers to be easily extended for new action types.

### Common Pitfalls

- ❌ Forgetting to resolve paths in action context
- ❌ Not validating action data on backend
- ❌ Mixing up one-way rendering vs two-way binding
- ❌ Not handling missing data model paths gracefully
- ❌ Sending too much data in action context
- ❌ Trying to implement for all agents at once (use phased approach!)

### Best Practices

- ✅ Use descriptive action names (`submit_form`, `book_restaurant`)
- ✅ Keep action context minimal - only send necessary data
- ✅ Validate on backend, show errors via `updateDataModel`
- ✅ Use two-way binding for inputs, actions for submissions
- ✅ Test with real user interaction patterns
- ✅ **Start with a2ui-loop agent, validate thoroughly before extending to others**
- ✅ Create simple test cases first (single button click) before complex flows

---

## Quick Start: Minimal Implementation for A2UI Loop

For the initial Phase 1 implementation focused on `a2ui-loop` agent, here's the minimal viable path:

### Backend Minimal Steps

1. **Add UserAction model** to `backend/protocols/a2ui_types.py`
2. **Add endpoint** in `backend/api/routes.py`: `POST /agents/a2ui-loop/action`
3. **Update** `backend/agents/a2ui_agent_with_loop.py`:
   - Add `process_user_action()` node
   - Handle one simple action type (e.g., "test_click")
4. **Update** `backend/graphs/a2ui_loop_graph.py`:
   - Add conditional routing for user actions
5. **Add Button helper** with action support to `backend/protocols/a2ui_types.py`

### Frontend Minimal Steps

1. **Create** `frontend/services/a2uiUserActions.ts` with `sendAction()` method
2. **Update** `frontend/lib/a2ui/A2UIManager.ts`:
   - Add `handleComponentAction()` method
   - Add `resolveActionContext()` method
3. **Update** `frontend/components/a2ui/A2UIComponentRenderer.tsx`:
   - Add Button onClick handler that calls manager
4. **Update** `frontend/components/chat/ChatInterface.tsx`:
   - Register action callback with A2UIManager
   - Handle SSE stream from action endpoint

### Minimal Test Case

Create a simple button that when clicked, sends action to backend and gets text response:

```
Agent sends: Button "Click Me" with action "test_click"
User clicks: Button
Frontend sends: userAction { name: "test_click", context: {} }
Backend processes: Returns text "Button clicked!"
Frontend receives: Displays text in chat
```

This minimal path gets the full round-trip working without complexity, validating the architecture before adding more features.
