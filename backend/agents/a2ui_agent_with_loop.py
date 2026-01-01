"""
A2UI Agent with Tool-Calling Loop Pattern

This agent uses a ReAct-style loop to:
1. Call LLM with tool binding
2. Execute tool(s) 
3. Feed results back to LLM
4. Repeat until LLM decides it's done

This enables:
- Multiple component generation in one request
- Complex UI composition
- Conditional tool calling based on previous results
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
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)


async def process_user_action(state: AgentState) -> AsyncGenerator[str, None]:
    """
    Process user action from A2UI components.
    
    This function handles userAction messages sent from the frontend when users
    interact with buttons, forms, or other actionable components.
    
    Args:
        state: Current agent state with user_action field
        
    Yields:
        SSE-formatted AG-UI events and A2UI messages
    """
    user_action = state.get("user_action")
    
    if not user_action:
        logger.warning("No user_action in state")
        return
    
    action_name = user_action.get("name")
    context = user_action.get("context", {})
    surface_id = user_action.get("surfaceId")
    
    logger.info(f"Processing action: {action_name} on surface {surface_id}")
    
    # Create encoders
    agui_encoder = EventEncoder(accept="text/event-stream")
    a2ui_encoder = A2UIEncoder()
    
    # Handle specific actions
    if action_name == "submit_form":
        # Extract form data from context
        email = context.get("email", "")
        name = context.get("name", "")
        
        # Generate funny response using LLM if we have the data
        if email or name:
            llm_response = await call_llm_for_funny_response(email, name, state)
            response_text = llm_response.get("text", "Hello, world!")
        else:
            response_text = "Form submitted successfully!"
        
        # Send AG-UI text message events
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text"}
        )
        yield agui_encoder.encode(text_start)
        
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=response_text
        )
        yield agui_encoder.encode(text_content)
        
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield agui_encoder.encode(text_end)


async def call_llm_for_funny_response(
    email: str,
    name: str,
    state: AgentState
) -> Dict[str, Any]:
    """
    Call LLM to generate a funny response based on form data.
    
    Args:
        email: Email from form
        name: Name from form
        state: Current agent state
        
    Returns:
        Dictionary with text response
    """
    prompt = f"""Generate a short, witty, and funny response (1-2 sentences) for a form submission.

Form data:
- Name: {name}
- Email: {email}

Make a clever observation or joke about the name or email address. Keep it lighthearted and friendly.
Examples:
- If email is "john@example.com": "Welcome John! Example.com, huh? That's... very example-ish!"
- If name is "Bob": "Bob! Short, sweet, and palindrome-adjacent. We love it!"

Return ONLY the funny message, nothing else."""
    
    try:
        provider = LLMProviderFactory.get_provider("ollama", "qwen:7b")
        llm = provider.get_model()
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        response_text = response.content if hasattr(response, "content") else str(response)
        
        return {"text": response_text.strip()}
        
    except Exception as e:
        logger.error(f"Error generating funny response: {e}", exc_info=True)
        return {"text": f"Thanks {name}! Your form has been submitted successfully!"}


async def call_llm_with_action_context(
    action_name: str,
    context: Dict[str, Any],
    state: AgentState
) -> AsyncGenerator[str, None]:
    """
    Call LLM to process user action with context.
    
    This allows the agent to use the LLM to decide how to respond to user actions,
    potentially generating new UI components or updating data models.
    
    Args:
        action_name: Name of the action triggered
        context: Context data from the action
        state: Current agent state
        
    Yields:
        SSE-formatted AG-UI events and A2UI messages
    """
    prompt = f"""
User performed action: {action_name}
Context data: {json.dumps(context, indent=2)}

Generate a response that includes:
1. Text feedback to the user
2. Any UI updates needed (describe what to update)

Return your response in this format:
TEXT: <your text response>
UI_UPDATES: <description of what to update in the UI, or "none" if no updates needed>
"""
    
    agui_encoder = EventEncoder(accept="text/event-stream")
    message_id = f"msg-{uuid.uuid4().hex[:8]}"
    
    try:
        # Get LLM provider
        provider = LLMProviderFactory.get_provider("azure-openai", "gpt-5-mini")
        llm = provider.get_model()
        
        # Call LLM
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # Parse response
        lines = response_text.strip().split("\n")
        text_response = ""
        
        for line in lines:
            if line.startswith("TEXT:"):
                text_response = line.replace("TEXT:", "").strip()
                break
        
        if not text_response:
            text_response = f"Received action '{action_name}' with data: {context}"
        
        # Send AG-UI text message events
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text"}
        )
        yield agui_encoder.encode(text_start)
        
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=text_response
        )
        yield agui_encoder.encode(text_content)
        
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield agui_encoder.encode(text_end)
        
    except Exception as e:
        logger.error(f"Error calling LLM for action processing: {e}", exc_info=True)
        
        # Send error message
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "error"}
        )
        yield agui_encoder.encode(text_start)
        
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=f"Error processing action '{action_name}': {str(e)}"
        )
        yield agui_encoder.encode(text_content)
        
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield agui_encoder.encode(text_end)


class A2UIAgentWithLoop(BaseAgent):
    """
    A2UI agent with tool-calling loop pattern.
    
    Differences from basic A2UIAgent:
    - Can call tools multiple times in sequence
    - LLM sees tool results and decides next action
    - Supports complex multi-component UIs
    - Follows ReAct pattern: Reason → Act → Observe → Repeat
    
    Example:
        User: "Create a signup form with email, password, and submit button"
        
        Loop iteration 1:
        - LLM: "I'll create email input" → calls create_textinput
        - Tool returns component data
        
        Loop iteration 2:
        - LLM: "Now I'll add password input" → calls create_textinput again
        - Tool returns component data
        
        Loop iteration 3:
        - LLM: "Finally, I'll add submit button" → calls create_button
        - Tool returns component data
        
        Loop ends:
        - LLM: "All components created, I'm done" → returns final message
    """
    
    def __init__(self, provider: str = "azure-openai", model: str = "gpt-5-mini", max_iterations: int = 5):
        """
        Initialize A2UI agent with tool-calling loop.
        
        Args:
            provider: LLM provider name
            model: Model name
            max_iterations: Max tool-calling loop iterations (safety limit)
        """
        self.a2ui_encoder = A2UIEncoder()
        self.agui_encoder = EventEncoder(accept="text/event-stream")
        
        self.llm_provider = LLMProviderFactory.get_provider(provider, model)
        self.provider_name = provider
        self.model = model
        self.max_iterations = max_iterations
        
        # Initialize tool registry
        self.tool_registry = ComponentToolRegistry()
        
        logger.info(f"A2UI Agent (with loop) initialized: {provider}/{model}, max_iterations={max_iterations}")
    
    async def run(self, state: AgentState) -> AsyncGenerator[str, None]:
        """
        Generate UI components with tool-calling loop.
        
        Flow:
        1. Send initial prompt to LLM with tools
        2. Loop:
           a. LLM decides to call tool(s) or finish
           b. If tool call: execute tool, feed result back to LLM
           c. If finish: break loop
        3. Collect all components from loop
        4. Send A2UI protocol messages
        5. Send confirmation message
        
        Args:
            state: Agent state
            
        Yields:
            SSE-formatted A2UI and AG-UI events
        """
        messages = state.get("messages", [])
        thread_id = state["thread_id"]
        run_id = state["run_id"]
        
        user_message = messages[-1].get("content", "") if messages else ""
        logger.info(f"A2UI Agent (loop) - thread: {thread_id}, user: '{user_message}'")
        
        # Create unique surface ID
        surface_id = f"surface-{uuid.uuid4().hex[:8]}"
        
        # ===== Tool-Calling Loop =====
        try:
            components_data = await self._tool_calling_loop(user_message)
        except Exception as e:
            logger.error(f"Failed in tool-calling loop: {e}")
            async for event in self._send_error_message(str(e)):
                yield event
            return
        
        # Extract all components and their data models
        all_components = []
        all_component_ids = []
        all_data_models = []  # Store separate data models instead of flattening
        
        for comp_data in components_data:
            if isinstance(comp_data.get("components"), list):
                # Multiple components from one tool call
                all_components.extend(comp_data["components"])
                all_component_ids.extend(comp_data.get("component_ids", []))
            else:
                # Single component
                all_components.append(comp_data["component"])
                all_component_ids.append(comp_data["component_id"])
            
            # Store data model with its path (don't flatten)
            data_model = comp_data["data_model"]
            all_data_models.append(data_model)
        
        # Determine root component ID
        if len(all_component_ids) == 1:
            # Single component: use it directly as root
            root_component_id = all_component_ids[0]
        elif len(all_component_ids) > 1:
            # Multiple components: wrap in a Column container
            container_id = f"column-container-{uuid.uuid4().hex[:8]}"
            container_component = Component(
                id=container_id,
                component={
                    "Column": {
                        "children": all_component_ids
                    }
                }
            )
            all_components.append(container_component)
            root_component_id = container_id
            logger.info(f"Wrapped {len(all_component_ids)} components in Column container")
        else:
            root_component_id = None
        
        # ===== Step 2: Create A2UI Surface =====
        surface_update = SurfaceUpdate(
            surface_id=surface_id,
            components=all_components
        )
        
        logger.info(f"Created surface with {len(all_components)} component(s)")
        yield self.a2ui_encoder.encode(surface_update)
        
        # ===== Step 3: Initialize Data Models =====
        # Send separate DataModelUpdate for each component's data model
        # This preserves the path hierarchy (e.g., /ui/bar-chart-abc/chartData)
        for data_model in all_data_models:
            data_update = DataModelUpdate(
                surface_id=surface_id,
                path=data_model["path"],
                contents=data_model["contents"]
            )
            logger.debug(f"Initialized data model at path: {data_model['path']}")
            yield self.a2ui_encoder.encode(data_update)
        
        # ===== Step 4: Begin Rendering =====
        begin_render = BeginRendering(
            surface_id=surface_id,
            root_component_id=root_component_id
        )
        
        logger.debug(f"Begin rendering from: {root_component_id}")
        yield self.a2ui_encoder.encode(begin_render)
        
        # ===== Step 5: Send AG-UI Confirmation =====
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text"}
        )
        yield self.agui_encoder.encode(text_start)
        
        confirmation = f"I've created {len(all_components)} UI component(s) for you. You can interact with them above."
        
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=confirmation
        )
        yield self.agui_encoder.encode(text_content)
        
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(text_end)
        
        logger.info("A2UI Agent (loop) completed")
    
    async def _tool_calling_loop(self, user_prompt: str) -> List[Dict[str, Any]]:
        """
        ReAct-style tool-calling loop.
        
        Loop structure:
        1. LLM with tools bound
        2. Check if LLM wants to call tool
        3. If yes: execute tool, add result to conversation
        4. If no: end loop
        5. Repeat until done or max iterations
        
        Args:
            user_prompt: User's UI generation request
            
        Returns:
            List of component data from all tool calls
        """
        # Get tool schemas
        tool_schemas = self.tool_registry.get_tool_schemas()
        
        # System prompt
        system_prompt = """You are a UI component generator assistant.

Your job is to create UI components by calling the appropriate tools.

Available tools:
- create_checkbox: Single checkbox
- create_checkboxes: Multiple checkboxes
- create_button: Button component (use context_paths to collect form data)
- create_textinput: Text input field (stores value at data model path)
- create_bar_chart: Bar chart visualization
- create_otp_input: OTP/verification code input (for 2FA, email verification, phone verification)

Guidelines:
1. Analyze user's request carefully
2. Break down complex UIs into individual components
3. Call tools one at a time OR multiple tools in parallel
4. After tool execution, you'll see the result
5. Decide if more components are needed
6. When all components are created, respond with text message

**IMPORTANT - Form Data Collection:**
When creating forms with inputs and a submit button:
1. Create text inputs with value paths (e.g., value_path="/user/email")
2. Create button with context_paths that reference those same paths
   Example: context_paths={"email": "/user/email", "name": "/user/name"}
3. This makes the button collect input values when clicked

Examples:
- "Create email and password inputs" → Call create_textinput twice
- "Signup form with submit button" → 
  * create_textinput(label="Email", value_path="/user/email")
  * create_textinput(label="Password", type="password", value_path="/user/password")
  * create_button(label="Submit", action_name="submit_form", context_paths={"email": "/user/email", "password": "/user/password"})
- "3 checkboxes for options" → Call create_checkboxes once with count=3
- "6-digit verification code" → Call create_otp_input with max_length=6

Always verify tool results before proceeding."""
        
        # Initialize conversation
        conversation = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Get model with tools
        model_with_tools = self.llm_provider.get_model_with_tools(tool_schemas)
        
        # Collected components
        components_data = []
        
        # Tool-calling loop
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"Tool-calling loop iteration {iteration}")
            
            # Call LLM
            response = await model_with_tools.ainvoke(conversation)
            
            # Add AI response to conversation
            conversation.append(response)
            
            # Check if LLM called any tools
            if not hasattr(response, 'tool_calls') or not response.tool_calls:
                # No tool calls - LLM is done
                logger.info(f"LLM finished after {iteration} iteration(s)")
                break
            
            # Execute all tool calls from this iteration
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call.get("id", str(uuid.uuid4()))
                
                logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
                
                try:
                    # Get tool
                    tool = self.tool_registry.get_tool(tool_name)
                    if not tool:
                        raise ValueError(f"Unknown tool: {tool_name}")
                    
                    # Generate component
                    component_data = tool.generate_component(**tool_args)
                    component_data["component_type"] = tool_name.replace("create_", "")
                    
                    # Store component data
                    components_data.append(component_data)
                    
                    # Create tool message with result
                    tool_result = f"Successfully created {component_data['component_type']} component with ID: {component_data.get('component_id', 'N/A')}"
                    
                    tool_message = ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call_id
                    )
                    conversation.append(tool_message)
                    
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    # Send error back to LLM
                    error_message = ToolMessage(
                        content=f"Error: {str(e)}",
                        tool_call_id=tool_call_id
                    )
                    conversation.append(error_message)
        
        # Check if we hit max iterations
        if iteration >= self.max_iterations:
            logger.warning(f"Reached max iterations ({self.max_iterations})")
        
        # Validate we got at least one component
        if not components_data:
            raise ValueError("No components were generated. Please rephrase your request.")
        
        return components_data
    
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
            delta=f"Sorry, I encountered an error: {error_text}"
        )
        yield self.agui_encoder.encode(text_content)
        
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(text_end)
