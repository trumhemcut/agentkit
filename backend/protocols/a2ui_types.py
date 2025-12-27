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


# Union type for all A2UI messages
A2UIMessage = Union[SurfaceUpdate, DataModelUpdate, BeginRendering, DeleteSurface]


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
    action_name: str
) -> Component:
    """
    Create a button component.
    
    Args:
        component_id: Unique ID for the button
        label_text: Text to display on button
        action_name: Name of action to trigger on click
    
    Returns:
        Component with button configuration
    """
    return Component(
        id=component_id,
        component={
            "Button": {
                "label": {"literalString": label_text},
                "onPress": {"action": action_name}
            }
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

