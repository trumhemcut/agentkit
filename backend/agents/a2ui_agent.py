"""
A2UI Agent - Dynamic UI Component Generation (LLM-Powered)

This agent uses LLM + tool calling to dynamically generate UI components
based on user prompts.

The agent demonstrates modern A2UI capabilities by:
- Using LLM to understand user UI requests
- Calling component generation tools based on intent
- Streaming A2UI protocol messages to frontend
- Supporting extensible component types

Example Usage:
    from agents.a2ui_agent import A2UIAgent
    
    agent = A2UIAgent(provider="ollama", model="qwen2.5:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Create a checkbox for agreeing to terms"}],
        "thread_id": "thread-123",
        "run_id": "run-456"
    }
    
    async for event in agent.run(state):
        # Stream A2UI and AG-UI events to frontend
        print(event)
"""

import uuid
import logging
import json
from typing import AsyncGenerator, List, Dict, Any
from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    RunStartedEvent,
    RunFinishedEvent,
    BaseEvent
)
from ag_ui.encoder import EventEncoder
from agents.base_agent import BaseAgent, AgentState
from protocols.a2ui_types import (
    SurfaceUpdate,
    DataModelUpdate,
    BeginRendering,
    Component,
)
from protocols.a2ui_encoder import A2UIEncoder
from llm.provider_factory import LLMProviderFactory
from tools.a2ui_tools import ComponentToolRegistry
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class A2UIAgent(BaseAgent):
    """
    Agent that dynamically generates A2UI UI components using LLM + tools.
    
    Flow:
    1. User sends prompt: "Create a checkbox for terms agreement"
    2. LLM analyzes intent and calls appropriate tool (e.g., create_checkbox)
    3. Tool returns A2UI component structure
    4. Agent streams A2UI messages to frontend
    5. Frontend renders native UI component
    """
    
    def __init__(self, provider: str = "azure-openai", model: str = "gpt-5-mini"):
        """
        Initialize A2UI agent with LLM provider.
        
        Args:
            provider: LLM provider name (ollama, azure_openai, gemini)
            model: Model name
        """
        self.a2ui_encoder = A2UIEncoder()
        self.agui_encoder = EventEncoder(accept="text/event-stream")
        
        # Get LLM provider
        self.llm_provider = LLMProviderFactory.get_provider(provider, model)
        self.provider_name = provider
        self.model = model
        
        # Initialize component tool registry
        self.tool_registry = ComponentToolRegistry()
        
        logger.info(f"A2UI Agent initialized with {provider}/{model}")
    
    async def run(self, state: AgentState) -> AsyncGenerator[str, None]:
        """
        Generate UI components dynamically based on user prompt.
        
        Args:
            state: Agent state with messages, thread_id, run_id
        
        Yields:
            SSE-formatted strings (A2UI messages and AG-UI events)
        """
        messages = state.get("messages", [])
        thread_id = state["thread_id"]
        run_id = state["run_id"]
        
        # Get user message
        user_message = messages[-1].get("content", "") if messages else ""
        
        logger.info(f"A2UI Agent run - thread: {thread_id}, user: '{user_message}'")
        
        # Create unique surface ID
        surface_id = f"surface-{uuid.uuid4().hex[:8]}"
        
        # ===== Step 1: LLM decides which component to create =====
        try:
            component_data = await self._generate_component_with_llm(user_message)
        except Exception as e:
            logger.error(f"Failed to generate component: {e}")
            # Fallback to error message
            async for event in self._send_error_message(
                f"Sorry, I couldn't generate the UI component: {str(e)}"
            ):
                yield event
            return
        
        # ===== Step 2: Create A2UI Surface =====
        # Handle both single component and multiple components
        components_list = component_data.get("components") or [component_data.get("component")]
        component_ids = component_data.get("component_ids") or [component_data.get("component_id")]
        root_component_id = component_data.get("root_component_id") or component_data.get("component_id")
        
        # Create surface update with generated component(s)
        surface_update = SurfaceUpdate(
            surface_id=surface_id,
            components=components_list
        )
        
        logger.debug(f"Created surface with {len(components_list)} component(s): {component_ids}")
        yield self.a2ui_encoder.encode(surface_update)
        
        # ===== Step 3: Initialize Data Model =====
        data_model = component_data["data_model"]
        data_update = DataModelUpdate(
            surface_id=surface_id,
            path=data_model["path"],
            contents=data_model["contents"]
        )
        
        logger.debug("Initialized data model")
        yield self.a2ui_encoder.encode(data_update)
        
        # ===== Step 4: Begin Rendering =====
        begin_render = BeginRendering(
            surface_id=surface_id,
            root_component_id=root_component_id
        )
        
        logger.debug(f"Begin rendering from: {root_component_id}")
        yield self.a2ui_encoder.encode(begin_render)
        
        # ===== Step 5: Send AG-UI Confirmation Message =====
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        # Start text message
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text"}
        )
        yield self.agui_encoder.encode(text_start)
        
        # Send confirmation - handle single vs multiple components
        component_count = len(components_list)
        component_type = component_data.get('component_type', 'component')
        
        if component_count > 1:
            confirmation = f"I've created {component_count} {component_type}s for you. You can interact with them above."
        else:
            confirmation = f"I've created the {component_type} for you. You can interact with it above."
        
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=confirmation
        )
        yield self.agui_encoder.encode(text_content)
        
        # End text message
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(text_end)
        
        logger.info("A2UI Agent run completed")
    
    async def _generate_component_with_llm(self, user_prompt: str) -> Dict[str, Any]:
        """
        Use LLM with tool calling to generate component.
        
        Args:
            user_prompt: User's request (e.g., "Create a checkbox for terms")
        
        Returns:
            Dict with component, data_model, component_id, component_type
        """
        # Get tool schemas for LLM
        tool_schemas = self.tool_registry.get_tool_schemas()
        
        # Create system prompt
        system_prompt = """You are a UI component generator assistant.

Your job is to analyze user requests and create appropriate UI components.
Use the available tools to generate components based on user intent.

Guidelines:
- For SINGLE checkbox: use create_checkbox tool
  Examples: "checkbox for agreement", "I need to agree to terms"
  
- For MULTIPLE checkboxes: use create_checkboxes tool (note the 's')
  Examples: "3 checkboxes for flight plan", "create checkboxes for morning, afternoon, evening"
  When user mentions a number (e.g., "3 checkboxes") or lists multiple items, use create_checkboxes
  
- For BUTTON: use create_button tool
  Examples: "create a submit button", "add a confirm button", "button to cancel"
  Extract button action from context (submit, cancel, confirm, etc.)
  
- For TEXT INPUT: use create_textinput tool
  Examples: "text input for name", "textbox for email", "input field for phone"
  Set multiline=true for "text area" or "comments" requests

- For OTP INPUT: use create_otp_input tool
  Examples: "create OTP verification", "6-digit code input", "2FA authentication", "email verification code"
  Common lengths: 4, 5, or 6 digits
  Use separators for better UX (e.g., separator_positions=[3] for 6-digit code)
  
- Extract specific labels/placeholders from user's request when possible
  Example: "checkboxes for flight HN→SG, SG→DN, DN→HN" 
  -> labels: ["Chuyến bay HN → SG", "Chuyến bay SG → DN", "Chuyến bay DN → HN"]

Always call the most appropriate tool based on the user's request."""
        
        # Prepare messages for LLM using LangChain message format
        llm_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Get LLM model with tools bound
        model_with_tools = self.llm_provider.get_model_with_tools(tool_schemas)
        
        # Call LLM with tools
        logger.debug(f"Calling LLM with {len(tool_schemas)} tools")
        response = await model_with_tools.ainvoke(llm_messages)
        
        # Extract tool call from response
        if not hasattr(response, 'tool_calls') or not response.tool_calls:
            raise ValueError("LLM did not call any tool. Please rephrase your request to be more specific about the UI component you want.")
        
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        logger.debug(f"LLM called tool: {tool_name} with args: {tool_args}")
        
        # Get tool and generate component
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        component_data = tool.generate_component(**tool_args)
        component_data["component_type"] = tool_name.replace("create_", "")
        
        return component_data
    
    async def _send_error_message(self, error_text: str) -> AsyncGenerator[str, None]:
        """Send error message as AG-UI event"""
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "error"}
        )
        yield self.agui_encoder.encode(text_start)
        
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=error_text
        )
        yield self.agui_encoder.encode(text_content)
        
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(text_end)


class A2UIFormAgent(BaseAgent):
    """
    Specialized agent for generating form UIs.
    
    This agent can create more complex forms with:
    - Multiple input fields
    - Validation
    - Submit buttons
    - Error messages
    
    Future implementation.
    """
    
    def __init__(self):
        """Initialize form agent."""
        pass
    
    async def run(self, state: AgentState) -> AsyncGenerator[str, None]:
        """Generate form UI with multiple fields."""
        raise NotImplementedError("Form agent coming soon")
        # Make this a generator even though it raises
        yield  # This line will never execute but makes it a generator

