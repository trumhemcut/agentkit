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
    create_button_component,
    create_textinput_component,
    create_bar_chart_component,
    create_otp_input_component
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


class ButtonTool(BaseComponentTool):
    """Tool to generate button components"""
    
    @property
    def name(self) -> str:
        return "create_button"
    
    @property
    def description(self) -> str:
        return """Create a button UI component. Use this when user wants:
        - A clickable button
        - An action button (submit, cancel, confirm, etc.)
        - A button to trigger an action
        
        Examples:
        - "Create a submit button"
        - "Add a button to confirm"
        - "Make a cancel button"
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Text to display on the button"
                },
                "action_name": {
                    "type": "string",
                    "description": "Name of action to trigger (e.g., 'submit', 'cancel', 'confirm')",
                    "default": "button_click"
                }
            },
            "required": ["label"]
        }
    
    def generate_component(
        self,
        label: str,
        action_name: str = "button_click",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate button component"""
        
        # Generate unique component ID
        component_id = f"button-{uuid.uuid4().hex[:8]}"
        
        # Create button component
        component = create_button_component(
            component_id=component_id,
            label_text=label,
            action_name=action_name
        )
        
        # Buttons don't need data model (they trigger actions, not store state)
        data_model = {
            "path": "/ui",
            "contents": []
        }
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
        }


class TextInputTool(BaseComponentTool):
    """Tool to generate text input components"""
    
    @property
    def name(self) -> str:
        return "create_textinput"
    
    @property
    def description(self) -> str:
        return """Create a text input UI component. Use this when user wants:
        - A text input field (textbox)
        - An input for entering text
        - A text area for multiple lines
        - A form input field
        
        Examples:
        - "Create a text input for name"
        - "Add a textbox for email"
        - "Make a text area for comments"
        - "Input field for phone number"
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "placeholder": {
                    "type": "string",
                    "description": "Placeholder text shown when input is empty"
                },
                "label": {
                    "type": "string",
                    "description": "Label text above the input (optional)"
                },
                "multiline": {
                    "type": "boolean",
                    "description": "Whether to allow multiple lines (textarea)",
                    "default": False
                },
                "data_path": {
                    "type": "string",
                    "description": "Path in data model to store value (e.g., '/form/name')",
                    "default": None
                }
            },
            "required": ["placeholder"]
        }
    
    def generate_component(
        self,
        placeholder: str,
        label: Optional[str] = None,
        multiline: bool = False,
        data_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text input component"""
        
        # Generate unique component ID
        component_id = f"textinput-{uuid.uuid4().hex[:8]}"
        
        # Generate data path if not provided
        if not data_path:
            data_path = f"/ui/{component_id}/value"
        
        # Create text input component
        component = create_textinput_component(
            component_id=component_id,
            placeholder=placeholder,
            value_path=data_path,
            label=label,
            multiline=multiline
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
                    value_string=""  # Initialize with empty string
                )
            ]
        }
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
        }


class BarChartTool(BaseComponentTool):
    """Tool to generate bar chart components"""
    
    @property
    def name(self) -> str:
        return "create_bar_chart"
    
    @property
    def description(self) -> str:
        return """Create a bar chart visualization component. Use this when user wants:
        - Display numeric data as bar chart
        - Compare data across categories
        - Visualize trends or comparisons
        - Show statistics or metrics
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Chart title"
                },
                "description": {
                    "type": "string",
                    "description": "Chart description (optional)",
                    "default": ""
                },
                "data": {
                    "type": "array",
                    "description": "Array of data points with category and values",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "values": {"type": "object"}
                        }
                    }
                },
                "data_keys": {
                    "type": "array",
                    "description": "Keys for data series to display (e.g., ['desktop', 'mobile'])",
                    "items": {"type": "string"}
                },
                "colors": {
                    "type": "object",
                    "description": "Color mapping for each data key",
                    "default": {}
                },
                "data_path": {
                    "type": "string",
                    "description": "Path in data model to store chart data",
                    "default": None
                }
            },
            "required": ["title", "data", "data_keys"]
        }
    
    def generate_component(
        self,
        title: str,
        data: List[Dict[str, Any]],
        data_keys: List[str],
        description: str = "",
        colors: Optional[Dict[str, str]] = None,
        data_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate bar chart component structure"""
        
        # Generate unique component ID
        component_id = f"bar-chart-{uuid.uuid4().hex[:8]}"
        
        # Generate data path if not provided
        if not data_path:
            data_path = f"/ui/{component_id}/chartData"
        
        # Create bar chart component
        component = create_bar_chart_component(
            component_id=component_id,
            title=title,
            description=description,
            data_keys=data_keys,
            colors=colors or {},
            data_path=data_path
        )
        
        # Create initial data model with chart data
        path_parts = data_path.split('/')
        data_key = path_parts[-1]
        parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else "/"
        
        data_model = {
            "path": parent_path,
            "contents": [
                DataContent(
                    key=data_key,
                    value_map={
                        "data": data,
                        "dataKeys": data_keys
                    }
                )
            ]
        }
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
        }


class OTPInputTool(BaseComponentTool):
    """Tool to generate OTP input block components"""
    
    @property
    def name(self) -> str:
        return "create_otp_input"
    
    @property
    def description(self) -> str:
        return """Create an OTP (One-Time Password) input block component. Use this when user wants:
        - Verify user identity with OTP
        - Two-factor authentication input
        - Verification code entry (email, SMS, authenticator)
        - Multi-digit secure code input
        
        Examples:
        - "Create an OTP input for email verification"
        - "Add 6-digit code verification"
        - "Show 2FA authentication form"
        - "Create verification code input with 4 digits"
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title text for the OTP block (e.g., 'Verify your email')",
                    "default": "Enter verification code"
                },
                "description": {
                    "type": "string",
                    "description": "Descriptive text explaining the OTP purpose",
                    "default": "Please enter the verification code sent to your device."
                },
                "max_length": {
                    "type": "integer",
                    "description": "Number of OTP digits/characters (common: 4, 5, 6)",
                    "default": 6
                },
                "separator_positions": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Positions to insert separators (e.g., [3] for '123-456', [2, 4] for '12-34-56')",
                    "default": None
                },
                "pattern_type": {
                    "type": "string",
                    "enum": ["digits", "alphanumeric"],
                    "description": "Input pattern validation: 'digits' (numbers only) or 'alphanumeric' (letters + numbers)",
                    "default": "digits"
                },
                "button_text": {
                    "type": "string",
                    "description": "Submit button text",
                    "default": "Verify"
                },
                "disabled": {
                    "type": "boolean",
                    "description": "Whether the input is disabled",
                    "default": False
                },
                "data_path": {
                    "type": "string",
                    "description": "Path in data model to store OTP value",
                    "default": None
                }
            },
            "required": []
        }
    
    def generate_component(
        self,
        title: str = "Enter verification code",
        description: str = "Please enter the verification code sent to your device.",
        max_length: int = 6,
        separator_positions: Optional[List[int]] = None,
        pattern_type: str = "digits",
        button_text: str = "Verify",
        disabled: bool = False,
        data_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate OTP input block component structure"""
        
        # Generate unique component ID
        component_id = f"otp-input-{uuid.uuid4().hex[:8]}"
        
        # Generate data path if not provided
        if not data_path:
            data_path = f"/ui/{component_id}/value"
        
        # Create OTP input component
        component = create_otp_input_component(
            component_id=component_id,
            title=title,
            description=description,
            max_length=max_length,
            separator_positions=separator_positions,
            pattern_type=pattern_type,
            button_text=button_text,
            disabled=disabled,
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
                    value_string=""  # Initial empty OTP value
                )
            ]
        }
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
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
        self.register_tool(ButtonTool())
        self.register_tool(TextInputTool())
        self.register_tool(BarChartTool())
        self.register_tool(OTPInputTool())
    
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
