"""
Salary Viewer Agent with OTP Verification

This agent demonstrates the A2UI tool loop pattern by requiring OTP verification
before revealing confidential salary information.

User Flow:
1. User asks about salary information
2. Agent requests OTP verification
3. User enters OTP code
4. Agent verifies and reveals salary details
"""

import asyncio
import uuid
import logging
import json
from typing import AsyncGenerator, List, Dict, Any
from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
)
from ag_ui.encoder import EventEncoder
from agents.base_agent import BaseAgent, AgentState
from protocols.a2ui_types import (
    SurfaceUpdate,
    DataModelUpdate,
    BeginRendering,
)
from protocols.a2ui_encoder import A2UIEncoder
from llm.provider_factory import LLMProviderFactory
from tools.a2ui_tools import ComponentToolRegistry
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a playful and helpful salary information assistant.

Your task is to help the "Tổng tài" check their salary information, but this is confidential data that requires verification.

IMPORTANT RULES:
1. When the user first asks about salary, politely explain that this is confidential information and OTP verification is required
2. Use the create_otp_input tool to request a 6-digit OTP verification code
3. After the tool is executed and user provides input, consider the verification successful (for this demo, any code is accepted)
4. Once verified, reveal the salary information in a friendly, enthusiastic way:
   - Original salary: 5,000,000 VND
   - Increase percentage: 5%
   - New salary: 5,250,000 VND
   - Increase amount: 250,000 VND

CONVERSATION FLOW:
- First message: Request OTP verification
- After OTP tool call: Wait for user input
- After user input received: Congratulate and reveal salary details

Remember to be playful and use emojis when revealing the salary! 😄💰
"""


class SalaryViewerAgent(BaseAgent):
    """
    Agent that requires OTP verification before revealing salary information.
    
    This demonstrates the A2UI tool loop pattern:
    1. Agent calls OTP input tool
    2. User provides input through A2UI component
    3. Agent receives input and continues
    4. Agent reveals information
    """
    
    def __init__(self, provider: str = "azure-openai", model: str = "gpt-5-mini", max_iterations: int = 5):
        """
        Initialize Salary Viewer agent with OTP verification capability.
        
        Args:
            provider: LLM provider name
            model: Model name
            max_iterations: Max tool-calling loop iterations
        """
        self.a2ui_encoder = A2UIEncoder()
        self.agui_encoder = EventEncoder(accept="text/event-stream")
        
        self.llm_provider = LLMProviderFactory.get_provider(provider, model)
        self.provider_name = provider
        self.model = model
        self.max_iterations = max_iterations
        
        # Initialize tool registry (includes OTP input tool)
        self.tool_registry = ComponentToolRegistry()
        
        # Track verification state
        self.verification_status = "none"  # none, pending, verified
        
        logger.info(f"Salary Viewer Agent initialized: {provider}/{model}")
    
    async def run(self, state: AgentState) -> AsyncGenerator[str, None]:
        """
        Handle salary inquiry with OTP verification.
        
        Flow:
        1. Check if this is first message → request OTP
        2. If OTP tool called → wait for user input
        3. If user action received → echo OTP and reveal salary
        
        Args:
            state: Agent state
            
        Yields:
            SSE-formatted A2UI and AG-UI events
        """
        messages = state.get("messages", [])
        thread_id = state["thread_id"]
        run_id = state["run_id"]
        user_action = state.get("user_action")  # A2UI protocol user action
        
        user_message = messages[-1].get("content", "") if messages else ""
        logger.info(f"Salary Viewer Agent - thread: {thread_id}, user: '{user_message}', user_action: {user_action}")
        
        # Create unique surface ID
        surface_id = f"surface-{uuid.uuid4().hex[:8]}"
        
        # Check if user action received (Verify button clicked)
        if user_action:
            action_name = user_action.get("name")
            action_context = user_action.get("context", {})
            
            logger.info(f"User action received: {action_name}, context: {action_context}")
            
            # Extract OTP from action context
            otp_code = action_context.get("code", "")
            
            if action_name == "verify_otp" and otp_code:
                self.verification_status = "verified"
                
                # Echo OTP back to user
                async for event in self._echo_otp_message(otp_code):
                    yield event
                
                # Reveal salary information
                async for event in self._reveal_salary_info():
                    yield event
                return
            else:
                # Unknown action or missing OTP
                async for event in self._send_error_message(
                    "Invalid verification attempt. Please try again."
                ):
                    yield event
                return
        
        # Check verification status in message history
        has_otp_request = any(
            "otp" in str(msg).lower() or "verification" in str(msg).lower() 
            for msg in messages[:-1]  # Check previous messages
        )
        
        if has_otp_request and self.verification_status == "none":
            self.verification_status = "pending"
        
        # Execute tool-calling loop to request OTP
        try:
            components_data = await self._tool_calling_loop(user_message)
        except Exception as e:
            logger.error(f"Failed in tool-calling loop: {e}")
            async for event in self._send_error_message(str(e)):
                yield event
            return
        
        # If we got components (OTP input), send them via A2UI protocol
        if components_data:
            self.verification_status = "pending"
            
            # Extract components and data models
            all_components = []
            all_component_ids = []
            all_data_models = []
            
            for comp_data in components_data:
                if isinstance(comp_data.get("components"), list):
                    all_components.extend(comp_data["components"])
                    all_component_ids.extend(comp_data.get("component_ids", []))
                else:
                    all_components.append(comp_data["component"])
                    all_component_ids.append(comp_data["component_id"])
                
                all_data_models.append(comp_data["data_model"])
            
            logger.info(f"Generated {len(all_components)} components: {all_component_ids}")
            
            # Send A2UI protocol messages
            async for event in self._send_a2ui_components(
                surface_id, 
                all_components, 
                all_data_models
            ):
                yield event
            
            # Send confirmation message
            async for event in self._send_confirmation_message():
                yield event
    
    async def _tool_calling_loop(self, user_message: str) -> List[Dict]:
        """
        Execute tool-calling loop to request OTP input.
        
        Args:
            user_message: User's message
            
        Returns:
            List of component data dictionaries
        """
        # Prepare messages with system prompt
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]
        
        # Get available tools
        tool_schemas = self.tool_registry.get_tool_schemas()
        logger.info(f"Available tool schemas: {len(tool_schemas)}")
        
        # Bind tools to LLM
        llm_with_tools = self.llm_provider.get_model_with_tools(tool_schemas)
        
        components_data = []
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Tool-calling loop iteration {iteration}/{self.max_iterations}")
            
            # Call LLM
            response = await llm_with_tools.ainvoke(messages)
            logger.info(f"LLM response type: {type(response)}, has tool_calls: {hasattr(response, 'tool_calls')}")
            
            # Add AI message to conversation
            messages.append(AIMessage(content=response.content or "", tool_calls=getattr(response, 'tool_calls', [])))
            
            # Check if LLM wants to call tools
            tool_calls = getattr(response, 'tool_calls', [])
            
            if not tool_calls:
                # No more tools to call, we're done
                logger.info("No tool calls, loop finished")
                break
            
            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", str(uuid.uuid4()))
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                try:
                    # Get tool from registry
                    tool = self.tool_registry.get_tool(tool_name)
                    if not tool:
                        error_msg = f"Tool '{tool_name}' not found in registry"
                        logger.error(error_msg)
                        messages.append(ToolMessage(
                            content=json.dumps({"error": error_msg}),
                            tool_call_id=tool_id
                        ))
                        continue
                    
                    # Execute tool
                    result = tool.generate_component(**tool_args)
                    components_data.append(result)
                    
                    # Add tool result to messages
                    messages.append(ToolMessage(
                        content=json.dumps({"success": True, "component_id": result["component_id"]}),
                        tool_call_id=tool_id
                    ))
                    
                    logger.info(f"Tool executed successfully: {result['component_id']}")
                    
                except Exception as e:
                    error_msg = f"Tool execution failed: {str(e)}"
                    logger.error(error_msg)
                    messages.append(ToolMessage(
                        content=json.dumps({"error": error_msg}),
                        tool_call_id=tool_id
                    ))
        
        if iteration >= self.max_iterations:
            logger.warning(f"Reached max iterations ({self.max_iterations})")
        
        return components_data
    
    async def _send_a2ui_components(
        self, 
        surface_id: str, 
        components: List[Dict], 
        data_models: List[Dict]
    ) -> AsyncGenerator[str, None]:
        """Send A2UI protocol messages for components"""
        
        # Determine root component ID
        root_component_id = components[0].id if components else None
        
        # 1. Surface Update with all components
        surface_update = SurfaceUpdate(
            surface_id=surface_id,
            components=components
        )
        sse_event = self.a2ui_encoder.encode(surface_update)
        yield sse_event
        
        # 2. Data Model Updates (send each separately)
        for data_model in data_models:
            data_model_update = DataModelUpdate(
                surface_id=surface_id,
                path=data_model["path"],
                contents=data_model["contents"]
            )
            sse_event = self.a2ui_encoder.encode(data_model_update)
            yield sse_event
        
        # 3. Begin Rendering (must come after surface update and data models)
        begin_rendering = BeginRendering(
            surface_id=surface_id,
            root_component_id=root_component_id
        )
        sse_event = self.a2ui_encoder.encode(begin_rendering)
        yield sse_event
    
    async def _send_confirmation_message(self) -> AsyncGenerator[str, None]:
        """Send confirmation message asking user to enter OTP"""
        message_text = "Lương là bảo mật lắm anh ạ, vui lòng nhập mã OTP đã gửi đến thiết bị của bạn để xác minh danh tính nhé! 🔐📲"
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        # Start message
        start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text", "agentId": "salary-viewer", "agentName": "Salary Viewer"}
        )
        yield self.agui_encoder.encode(start_event)
        
        # Content
        content_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=message_text
        )
        yield self.agui_encoder.encode(content_event)
        
        # End message
        end_event = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(end_event)
    
    async def _echo_otp_message(self, otp_code: str) -> AsyncGenerator[str, None]:
        """
        Send message echoing the OTP code entered by user.
        
        Args:
            otp_code: The OTP code entered by user
            
        Yields:
            SSE-formatted AG-UI text message events
        """
        message_text = f"📩 Đã nhận mã OTP\n\nĐang xác thực..."
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        # Start message
        start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text", "agentId": "salary-viewer", "agentName": "Salary Viewer"}
        )
        yield self.agui_encoder.encode(start_event)
        
        # Content
        content_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=message_text
        )
        yield self.agui_encoder.encode(content_event)
        
        # End message
        end_event = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(end_event)
    
    async def _reveal_salary_info(self) -> AsyncGenerator[str, None]:
        """Send message revealing salary information"""
        message_text = """✅ Verification successful!

Here's your salary information:

💰 **Original Salary**: 5,000,000 VND
📈 **Increase**: 5%
✨ **New Salary**: 5,250,000 VND
💵 **Increase Amount**: +250,000 VND

Congratulations on your raise! 🎉😄"""
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        # Start message
        start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text", "agentId": "salary-viewer", "agentName": "Salary Viewer"}
        )
        yield self.agui_encoder.encode(start_event)
        
        # Content
        content_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=message_text
        )
        yield self.agui_encoder.encode(content_event)
        
        # End message
        end_event = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(end_event)
    
    async def _send_error_message(self, error: str) -> AsyncGenerator[str, None]:
        """Send error message to user"""
        message_text = f"❌ An error occurred: {error}"
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        # Start message
        start_event = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text", "agentId": "salary-viewer", "agentName": "Salary Viewer"}
        )
        yield self.agui_encoder.encode(start_event)
        
        # Content
        content_event = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=message_text
        )
        yield self.agui_encoder.encode(content_event)
        
        # End message
        end_event = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(end_event)
