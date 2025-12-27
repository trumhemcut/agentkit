"""
A2UI Component Generation Tools

These tools are used by LLM agents to generate A2UI protocol messages
for creating dynamic frontend components.

Future: These will be replaced/augmented with MCP (Model Context Protocol) tools.
"""

import uuid
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from protocols.a2ui_types import (
    Component,
    SurfaceUpdate,
    DataModelUpdate,
    BeginRendering,
    DataContent,
    create_checkbox_component,
    create_text_component,
    create_button_component
)


class BaseComponentTool(ABC):
    """Base class for A2UI component generation tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for LLM to call"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description for LLM to understand tool purpose"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters"""
        pass
    
    @abstractmethod
    def generate_component(self, **kwargs) -> Dict[str, Any]:
        """
        Generate A2UI component structure
        
        Returns:
            Dict with:
            - component: Component object
            - data_model: Initial data model for component
            - component_id: ID of the generated component
        """
        pass


class CheckboxTool(BaseComponentTool):
    """Tool to generate checkbox components"""
    
    @property
    def name(self) -> str:
        return "create_checkbox"
    
    @property
    def description(self) -> str:
        return """Create a checkbox UI component. Use this when user wants:
        - A checkbox for agreement/confirmation
        - A toggleable option
        - A boolean selection control
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Text label for the checkbox"
                },
                "checked": {
                    "type": "boolean",
                    "description": "Initial checked state",
                    "default": False
                },
                "data_path": {
                    "type": "string",
                    "description": "Path in data model to store value (e.g., '/form/agreedToTerms')",
                    "default": None
                }
            },
            "required": ["label"]
        }
    
    def generate_component(
        self,
        label: str,
        checked: bool = False,
        data_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate checkbox component structure"""
        
        # Generate unique component ID
        component_id = f"checkbox-{uuid.uuid4().hex[:8]}"
        
        # Generate data path if not provided
        if not data_path:
            data_path = f"/ui/{component_id}/value"
        
        # Create checkbox component
        component = create_checkbox_component(
            component_id=component_id,
            label_text=label,
            value_path=data_path
        )
        
        # Create initial data model
        path_parts = data_path.split('/')
        data_key = path_parts[-1]
        parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else "/"
        
        data_model = {
            "path": parent_path,
            "contents": [
                DataContent(
                    key=data_key,
                    value_boolean=checked
                )
            ]
        }
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
        }


class MultipleCheckboxesTool(BaseComponentTool):
    """Tool to generate multiple checkbox components at once"""
    
    @property
    def name(self) -> str:
        return "create_checkboxes"
    
    @property
    def description(self) -> str:
        return """Create multiple checkbox UI components. Use this when user wants:
        - Multiple checkboxes for a list of items
        - A checklist (e.g., flight plan, todo list, options)
        - Several toggleable options
        
        Examples:
        - "Create 3 checkboxes for flight plan"
        - "Show checkboxes for morning, afternoon, evening"
        - "Make a checklist with 5 items"
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of text labels for each checkbox"
                },
                "checked_states": {
                    "type": "array",
                    "items": {"type": "boolean"},
                    "description": "Initial checked state for each checkbox (optional, defaults to all false)",
                    "default": None
                },
                "group_name": {
                    "type": "string",
                    "description": "Name for the checkbox group (e.g., 'flight_plan', 'tasks')",
                    "default": "checkbox_group"
                }
            },
            "required": ["labels"]
        }
    
    def generate_component(
        self,
        labels: List[str],
        checked_states: Optional[List[bool]] = None,
        group_name: str = "checkbox_group",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate multiple checkbox components wrapped in a Column container"""
        
        if not labels:
            raise ValueError("At least one label is required")
        
        # Generate checked states if not provided
        if not checked_states:
            checked_states = [False] * len(labels)
        elif len(checked_states) < len(labels):
            # Pad with False if not enough states provided
            checked_states.extend([False] * (len(labels) - len(checked_states)))
        
        # Generate components and data contents
        components = []
        data_contents = []
        component_ids = []
        
        for idx, label in enumerate(labels):
            component_id = f"checkbox-{group_name}-{idx}-{uuid.uuid4().hex[:6]}"
            data_path = f"/ui/{group_name}/checkbox_{idx}"
            
            # Create checkbox component
            component = create_checkbox_component(
                component_id=component_id,
                label_text=label,
                value_path=data_path
            )
            components.append(component)
            component_ids.append(component_id)
            
            # Add data content for this checkbox
            data_contents.append(
                DataContent(
                    key=f"checkbox_{idx}",
                    value_boolean=checked_states[idx]
                )
            )
        
        # Create Column container to hold all checkboxes
        container_id = f"column-{group_name}-{uuid.uuid4().hex[:6]}"
        from protocols.a2ui_types import create_column_component
        container = create_column_component(
            component_id=container_id,
            child_ids=component_ids
        )
        components.append(container)  # Add container to components list
        
        # Create data model for all checkboxes
        data_model = {
            "path": f"/ui/{group_name}",
            "contents": data_contents
        }
        
        return {
            "components": components,  # All checkboxes + container
            "data_model": data_model,
            "component_ids": component_ids,  # List of checkbox IDs
            "root_component_id": container_id  # Container is the root!
        }


class ComponentToolRegistry:
    """Registry for all A2UI component tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseComponentTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default component tools"""
        self.register_tool(CheckboxTool())
        self.register_tool(MultipleCheckboxesTool())
    
    def register_tool(self, tool: BaseComponentTool):
        """Register a component tool"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseComponentTool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[BaseComponentTool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get tool schemas in OpenAI function calling format
        
        Returns:
            List of tool schemas for LLM provider
        """
        schemas = []
        for tool in self.tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return schemas
