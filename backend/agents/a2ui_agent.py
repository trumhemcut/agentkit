"""
A2UI Agent - Generates Interactive UI Components

This agent specializes in generating A2UI (Agent-to-UI) protocol messages
that create dynamic, interactive UI components in the frontend.

The agent demonstrates A2UI capabilities by:
- Creating UI components (checkboxes, buttons, text, etc.)
- Managing data models for component state
- Mixing A2UI messages with AG-UI events for rich interactions
- Supporting progressive rendering via SSE streaming

Example Usage:
    from agents.a2ui_agent import A2UIAgent
    from llm.provider_factory import LLMProviderFactory
    
    provider = LLMProviderFactory.get_provider("ollama")
    agent = A2UIAgent()
    
    state = {
        "messages": [{"role": "user", "content": "Show me a terms agreement checkbox"}],
        "thread_id": "thread-123",
        "run_id": "run-456"
    }
    
    async for event in agent.run(state):
        # Stream A2UI and AG-UI events to frontend
        print(event)
"""

import uuid
import logging
from typing import AsyncGenerator
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
    DataContent,
    create_checkbox_component,
    create_text_component,
    create_button_component
)
from protocols.a2ui_encoder import A2UIEncoder

logger = logging.getLogger(__name__)


class A2UIAgent(BaseAgent):
    """
    Agent that generates A2UI UI components.
    
    This agent creates interactive UI elements by emitting A2UI protocol messages
    alongside traditional AG-UI events. It supports:
    - Multiple component types (Checkbox, Button, Text, etc.)
    - Data model management for component state
    - Progressive rendering via streaming
    - Mixed A2UI + AG-UI event streams
    """
    
    def __init__(self):
        """Initialize A2UI agent with encoders."""
        self.a2ui_encoder = A2UIEncoder()
        self.agui_encoder = EventEncoder(accept="text/event-stream")
        logger.info("A2UI Agent initialized")
    
    async def run(self, state: AgentState) -> AsyncGenerator[str, None]:
        """
        Generate A2UI UI components and stream to frontend.
        
        This method demonstrates A2UI protocol by creating a simple interactive
        UI with a checkbox and accompanying text. The flow is:
        
        1. surfaceUpdate: Define UI components (checkbox)
        2. dataModelUpdate: Initialize component state
        3. beginRendering: Signal frontend to render
        4. AG-UI events: Send text messages for context
        
        Args:
            state: Agent state with messages, thread_id, run_id
        
        Yields:
            SSE-formatted strings (A2UI messages and AG-UI events)
        """
        messages = state.get("messages", [])
        thread_id = state["thread_id"]
        run_id = state["run_id"]
        
        # Get user message for context
        user_message = messages[-1].get("content", "") if messages else ""
        
        logger.info(f"A2UI Agent run started - thread: {thread_id}, run: {run_id}")
        logger.debug(f"User message: {user_message}")
        
        # Create unique surface ID
        surface_id = f"surface-{uuid.uuid4().hex[:8]}"
        
        # ===== Step 1: Create Surface with Components =====
        # Define checkbox component
        checkbox_id = "terms-checkbox"
        checkbox = create_checkbox_component(
            component_id=checkbox_id,
            label_text="I agree to the terms and conditions",
            value_path="/form/agreedToTerms"
        )
        
        # Optional: Add a text component for description
        text_id = "description-text"
        text_component = create_text_component(
            component_id=text_id,
            content="Please review and accept the terms to continue."
        )
        
        # Create surface update with components
        surface_update = SurfaceUpdate(
            surface_id=surface_id,
            components=[text_component, checkbox]
        )
        
        logger.debug(f"Created surface with {len(surface_update.components)} components")
        yield self.a2ui_encoder.encode(surface_update)
        
        # ===== Step 2: Initialize Data Model =====
        # Set initial checkbox state to unchecked
        data_update = DataModelUpdate(
            surface_id=surface_id,
            path="/form",
            contents=[
                DataContent(
                    key="agreedToTerms",
                    value_boolean=False
                )
            ]
        )
        
        logger.debug("Initialized data model")
        yield self.a2ui_encoder.encode(data_update)
        
        # ===== Step 3: Begin Rendering =====
        # Tell frontend to start rendering from the text component as root
        # (In a real app, you'd use a container component as root)
        begin_render = BeginRendering(
            surface_id=surface_id,
            root_component_id=checkbox_id  # Start rendering from checkbox
        )
        
        logger.debug(f"Begin rendering from root: {checkbox_id}")
        yield self.a2ui_encoder.encode(begin_render)
        
        # ===== Step 4: Send AG-UI Text Message =====
        # Provide context using standard AG-UI events
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        # Start text message
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text"}
        )
        yield self.agui_encoder.encode(text_start)
        
        # Send message content
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta="I've created an interactive checkbox for you. Please check the box above to agree to the terms."
        )
        yield self.agui_encoder.encode(text_content)
        
        # End text message
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(text_end)
        
        logger.info(f"A2UI Agent run completed")
    
    async def run_with_llm_generation(self, state: AgentState) -> AsyncGenerator[str, None]:
        """
        Future: Generate A2UI components dynamically using LLM.
        
        This method would use structured output from an LLM to generate
        A2UI components based on user requests. For example:
        
        User: "Show me a form with name and email fields"
        LLM: Generates A2UI JSON for form components
        Agent: Streams A2UI messages to frontend
        
        Not implemented yet - placeholder for future enhancement.
        """
        raise NotImplementedError("LLM-powered A2UI generation coming soon")


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
