"""
A2UI (Agent-to-UI) Protocol Message Types

This module defines Pydantic models for the A2UI protocol, which allows AI agents
to generate dynamic, interactive UI components as JSON that render natively in the frontend.

A2UI complements AG-UI by adding structured UI rendering capabilities:
- AG-UI: Real-time event streaming (text messages, status updates)
- A2UI: Declarative UI component generation (checkboxes, forms, cards)

Protocol Overview:
- surfaceUpdate: Define UI components (adjacency list model)
- dataModelUpdate: Update application state/data
- beginRendering: Signal client to start rendering from root component
- deleteSurface: Remove a UI surface

References:
- A2UI Specification: https://a2ui.org/specification/v0.8-a2ui/
- A2UI GitHub: https://github.com/google/a2ui
"""

from typing import Literal, Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field


class Component(BaseModel):
    """
    Base component with ID and type.
    
    Components use an adjacency list model where each component has:
    - id: Unique identifier within the surface
    - component: Dictionary with component type as key and properties as value
    
    Example:
        {
            "id": "checkbox-1",
            "component": {
                "Checkbox": {
                    "label": {"literalString": "I agree"},
                    "value": {"path": "/form/agreed"}
                }
            }
        }
    """
    id: str
    component: Dict[str, Any]


class SurfaceUpdate(BaseModel):
    """
    Define or update UI components in a surface.
    
    A surface is a collection of components that can be rendered independently.
    Components are stored in an adjacency list model for efficient lookups.
    
    Example:
        {
            "type": "surfaceUpdate",
            "surfaceId": "surface-abc123",
            "components": [
                {
                    "id": "checkbox-1",
                    "component": {"Checkbox": {...}}
                }
            ]
        }
    """
    type: Literal["surfaceUpdate"] = "surfaceUpdate"
    surface_id: str = Field(alias="surfaceId")
    components: List[Component]

    class Config:
        populate_by_name = True


class DataContent(BaseModel):
    """
    Data content for data model updates.
    
    Supports multiple value types:
    - valueString: String values
    - valueNumber: Numeric values
    - valueBoolean: Boolean values
    - valueMap: Nested objects
    """
    key: str
    value_string: Optional[str] = Field(None, alias="valueString")
    value_number: Optional[float] = Field(None, alias="valueNumber")
    value_boolean: Optional[bool] = Field(None, alias="valueBoolean")
    value_map: Optional[Dict[str, Any]] = Field(None, alias="valueMap")

    class Config:
        populate_by_name = True


class DataModelUpdate(BaseModel):
    """
    Update data model for components.
    
    Uses JSON Pointer paths to specify where in the data model to update.
    If path is None or "/", updates the entire root data model.
    
    Examples:
        # Update entire root
        {
            "type": "dataModelUpdate",
            "surfaceId": "surface-abc",
            "path": "/",
            "contents": [
                {"key": "userName", "valueString": "Alice"}
            ]
        }
        
        # Update nested path
        {
            "type": "dataModelUpdate",
            "surfaceId": "surface-abc",
            "path": "/form/settings",
            "contents": [
                {"key": "theme", "valueString": "dark"}
            ]
        }
    """
    type: Literal["dataModelUpdate"] = "dataModelUpdate"
    surface_id: str = Field(alias="surfaceId")
    path: Optional[str] = None
    contents: List[DataContent]

    class Config:
        populate_by_name = True


class BeginRendering(BaseModel):
    """
    Signal client to start rendering from a root component.
    
    This message tells the frontend which component is the root of the component
    tree and triggers the rendering process. Must be sent after surfaceUpdate
    and dataModelUpdate messages.
    
    Example:
        {
            "type": "beginRendering",
            "surfaceId": "surface-abc",
            "rootComponentId": "main-container"
        }
    """
    type: Literal["beginRendering"] = "beginRendering"
    surface_id: str = Field(alias="surfaceId")
    root_component_id: str = Field(alias="rootComponentId")

    class Config:
        populate_by_name = True


class DeleteSurface(BaseModel):
    """
    Remove a UI surface and all its components.
    
    Example:
        {
            "type": "deleteSurface",
            "surfaceId": "surface-abc"
        }
    """
    type: Literal["deleteSurface"] = "deleteSurface"
    surface_id: str = Field(alias="surfaceId")

    class Config:
        populate_by_name = True


# Union type for all A2UI messages (server-to-client)
A2UIMessage = Union[SurfaceUpdate, DataModelUpdate, BeginRendering, DeleteSurface]


# Client-to-Server Messages (A2UI v0.9)

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
ClientToServerMessage = Union[UserAction, ErrorMessage]


# Helper functions for creating common A2UI messages

def create_checkbox_component(
    component_id: str,
    label_text: str,
    value_path: str
) -> Component:
    """
    Create a checkbox component.
    
    Args:
        component_id: Unique ID for the checkbox
        label_text: Text to display next to checkbox
        value_path: JSON Pointer path to boolean value in data model
    
    Returns:
        Component with checkbox configuration
    """
    return Component(
        id=component_id,
        component={
            "Checkbox": {
                "label": {"literalString": label_text},
                "value": {"path": value_path}
            }
        }
    )


def create_text_component(
    component_id: str,
    content: str
) -> Component:
    """
    Create a text component.
    
    Args:
        component_id: Unique ID for the text component
        content: Text content to display
    
    Returns:
        Component with text configuration
    """
    return Component(
        id=component_id,
        component={
            "Text": {
                "content": {"literalString": content}
            }
        }
    )


def create_button_component(
    component_id: str,
    label_text: str,
    action_name: str,
    action_context: Optional[Dict[str, Any]] = None,
    style: Optional[Dict[str, Any]] = None
) -> Component:
    """
    Create a button component with action.
    
    Args:
        component_id: Unique ID for the button
        label_text: Text to display on button
        action_name: Name of action to trigger on click
        action_context: Data to send with action (paths or literal values)
        style: Optional style properties
    
    Returns:
        Component with button configuration
        
    Example:
        create_button_component(
            component_id="submit_btn",
            label_text="Submit Form",
            action_name="submit_form",
            action_context={
                "email": {"path": "/user/email"},
                "name": {"path": "/user/name"}
            }
        )
    """
    button_config = {
        "label": {"literalString": label_text},
        "action": {
            "name": action_name,
            "context": action_context or {}
        }
    }
    
    if style:
        button_config["style"] = style
    
    return Component(
        id=component_id,
        component={
            "Button": button_config
        }
    )


def create_column_component(
    component_id: str,
    child_ids: List[str]
) -> Component:
    """
    Create a column (vertical layout) container component.
    
    Args:
        component_id: Unique ID for the column container
        child_ids: List of child component IDs to render vertically
    
    Returns:
        Component with column container configuration
    """
    return Component(
        id=component_id,
        component={
            "Column": {
                "children": child_ids
            }
        }
    )


def create_textinput_component(
    component_id: str,
    placeholder: str,
    value_path: str,
    label: str = None,
    multiline: bool = False
) -> Component:
    """
    Create a text input component with two-way binding.
    
    TextField automatically updates the data model at value_path as user types.
    No action needed for typing - actions are for form submission.
    
    Args:
        component_id: Unique ID for the text input
        placeholder: Placeholder text when empty
        value_path: Path in data model where value is stored
        label: Optional label text above input
        multiline: Whether to allow multiple lines (textarea)
    
    Returns:
        Component with text input configuration
    """
    input_config = {
        "placeholder": {"literalString": placeholder},
        "value": {"path": value_path},
        "multiline": multiline
    }
    
    if label:
        input_config["label"] = {"literalString": label}
    
    return Component(
        id=component_id,
        component={
            "TextInput": input_config
        }
    )


def create_checkbox_with_action(
    component_id: str,
    label_text: str,
    value_path: str,
    on_change_action: Optional[str] = None,
    on_change_context: Optional[Dict[str, Any]] = None
) -> Component:
    """
    Create a CheckBox component with optional onChange action.
    
    Args:
        component_id: Unique component ID
        label_text: Checkbox label
        value_path: JSON Pointer to boolean value in data model
        on_change_action: Optional action name to trigger on value change
        on_change_context: Optional context to send with onChange
    
    Returns:
        Component with checkbox configuration
        
    Example:
        create_checkbox_with_action(
            component_id="agree_terms",
            label_text="I agree to terms",
            value_path="/form/agreed",
            on_change_action="validate_form",
            on_change_context={"field": "terms"}
        )
    """
    checkbox_config = {
        "label": {"literalString": label_text},
        "value": {"path": value_path}
    }
    
    if on_change_action:
        checkbox_config["onChange"] = {
            "action": on_change_action,
            "context": on_change_context or {}
        }
    
    return Component(
        id=component_id,
        component={
            "Checkbox": checkbox_config
        }
    )


def create_bar_chart_component(
    component_id: str,
    title: str,
    description: str,
    data_keys: List[str],
    colors: Dict[str, str],
    data_path: str
) -> Component:
    """
    Create a bar chart component.
    
    Args:
        component_id: Unique ID for the bar chart
        title: Chart title
        description: Chart description
        data_keys: Keys for data series (e.g., ['desktop', 'mobile'])
        colors: Color mapping for each key
        data_path: Path to chart data in data model
    
    Returns:
        Component with bar chart configuration
    
    Example:
        component = create_bar_chart_component(
            component_id="chart-abc123",
            title="User Statistics",
            description="Monthly user counts",
            data_keys=["desktop", "mobile"],
            colors={"desktop": "#2563eb", "mobile": "#60a5fa"},
            data_path="/ui/chart-abc123/chartData"
        )
    """
    return Component(
        id=component_id,
        component={
            "BarChart": {
                "title": {"literalString": title},
                "description": {"literalString": description},
                "dataKeys": {"literalString": ",".join(data_keys)},
                "colors": {"literalMap": colors},
                "data": {"path": data_path}
            }
        }
    )


def create_otp_input_component(
    component_id: str,
    title: str,
    description: str,
    max_length: int,
    separator_positions: Optional[List[int]],
    pattern_type: str,
    button_text: str,
    disabled: bool,
    value_path: str,
    action_name: str = "verify_otp"
) -> Component:
    """
    Create an OTP (One-Time Password) input block component.
    
    Args:
        component_id: Unique identifier for component
        title: Block title text
        description: Block description text
        max_length: Number of OTP digits
        separator_positions: List of positions to insert separators (e.g., [3] for '123-456')
        pattern_type: 'digits' or 'alphanumeric'
        button_text: Submit button text
        disabled: Whether input is disabled
        value_path: Data model path for OTP value
        action_name: Name of action to trigger when button is clicked
    
    Returns:
        Component with OTP block structure
    
    Example:
        component = create_otp_input_component(
            component_id="otp-input-abc123",
            title="Verify your email",
            description="Enter the 6-digit code sent to your email.",
            max_length=6,
            separator_positions=[3],
            pattern_type="digits",
            button_text="Verify",
            disabled=False,
            value_path="/ui/otp-input-abc123/value",
            action_name="verify_otp"
        )
    """
    # Calculate slot groups based on separator positions
    groups = []
    if separator_positions:
        positions = sorted(separator_positions)
        start = 0
        for pos in positions:
            groups.append({"start": start, "end": pos})
            start = pos
        groups.append({"start": start, "end": max_length})
    else:
        # Single group with all slots
        groups.append({"start": 0, "end": max_length})
    
    return Component(
        id=component_id,
        component={
            "OTPInput": {
                "title": {"literalString": title},
                "description": {"literalString": description},
                "maxLength": max_length,
                "groups": groups,
                "patternType": pattern_type,
                "buttonText": {"literalString": button_text},
                "disabled": disabled,
                "value": {"path": value_path},
                "action": {
                    "name": action_name,
                    "context": {
                        "code": {"path": value_path}
                    }
                }
            }
        }
    )
