"""
A2UI Loop Agent Graph

LangGraph workflow for A2UI agent with tool-calling loop pattern.

This graph demonstrates the ReAct pattern:
- Reason: LLM decides which tool to call
- Act: Execute tool
- Observe: Feed result back to LLM
- Repeat: Continue until done

Key difference from basic a2ui_graph:
- Supports MULTIPLE tool calls in sequence
- LLM sees tool results and makes decisions
- Enables complex multi-component UIs
- Handles user actions from A2UI components
"""

import logging
from typing import TypedDict, List, Dict, Literal, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from agents.a2ui_agent_with_loop import A2UIAgentWithLoop, process_user_action
from agents.base_agent import AgentState

logger = logging.getLogger(__name__)


def create_a2ui_loop_graph(model: str = None, provider: str = None, max_iterations: int = 5):
    """
    Create LangGraph workflow for A2UI agent with tool-calling loop.
    
    Graph structure:
        START → detect_input_type → [a2ui_loop_agent OR process_user_action] → END
    
    The graph routes based on whether the state contains a user_action:
    - If user_action exists: route to process_user_action node
    - Otherwise: route to a2ui_loop_agent node (normal text input)
    
    The agent internally manages the tool-calling loop using LangChain's
    ToolMessage pattern. This is simpler than using LangGraph's ToolNode
    for this use case.
    
    Args:
        model: Model name (e.g., "qwen:7b", "gpt-4")
        provider: Provider name (e.g., "ollama", "azure_openai")
        max_iterations: Maximum tool-calling loop iterations
        
    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Creating A2UI loop agent graph with user action support")
    
    # Create state graph
    workflow = StateGraph(AgentState)
    
    # Initialize agent
    agent_provider = provider if provider else "ollama"
    agent_model = model if model else "qwen:7b"
    
    logger.info(f"A2UI loop agent: provider={agent_provider}, model={agent_model}, max_iterations={max_iterations}")
    a2ui_agent = A2UIAgentWithLoop(
        provider=agent_provider,
        model=agent_model,
        max_iterations=max_iterations
    )
    
    # Define detect input type node
    def detect_input_type(state: AgentState):
        """Detect whether we have text input or user action"""
        logger.debug(f"Detecting input type - has user_action: {bool(state.get('user_action'))}")
        return state
    
    # Define agent node (for text input)
    async def a2ui_loop_node(state: AgentState, config=None):
        """Execute A2UI loop agent and stream events"""
        logger.debug(f"A2UI loop node processing - thread: {state['thread_id']}")
        
        # Get event callback from config
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        # Stream events from agent (includes tool-calling loop internally)
        async for event in a2ui_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Define user action node
    async def user_action_node(state: AgentState, config=None):
        """Process user action from A2UI components"""
        logger.debug(f"User action node processing - thread: {state['thread_id']}")
        
        # Get event callback from config
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        # Process user action - iterate over async generator
        async for event in process_user_action(state):
            # Stream each event as it's generated
            if event_callback:
                await event_callback(event)
        
        # Return state unchanged (events were already streamed)
        return state
    
    # Routing function
    def route_input(state: AgentState) -> Literal["process_user_action", "a2ui_loop_agent"]:
        """Route based on whether we have text input or user action"""
        if state.get("user_action"):
            logger.debug("Routing to process_user_action")
            return "process_user_action"
        else:
            logger.debug("Routing to a2ui_loop_agent")
            return "a2ui_loop_agent"
    
    # Add nodes to graph
    workflow.add_node("detect_input_type", detect_input_type)
    workflow.add_node("a2ui_loop_agent", a2ui_loop_node)
    workflow.add_node("process_user_action", user_action_node)
    
    # Set entry point
    workflow.set_entry_point("detect_input_type")
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "detect_input_type",
        route_input,
        {
            "a2ui_loop_agent": "a2ui_loop_agent",
            "process_user_action": "process_user_action"
        }
    )
    
    # Both paths lead to END
    workflow.add_edge("a2ui_loop_agent", END)
    workflow.add_edge("process_user_action", END)
    
    # Compile and return
    return workflow.compile()


def create_a2ui_loop_graph_with_toolnode(model: str = None, provider: str = None):
    """
    Alternative implementation using LangGraph's ToolNode pattern.
    
    This approach explicitly models the tool-calling loop in the graph structure:
    
        START → agent → should_continue? 
                          ↓              ↓
                        tools          end
                          ↓              ↓
                        agent          END
    
    Advantages:
    - Explicit visualization of tool-calling loop in graph
    - LangGraph manages checkpointing at each step
    - Easier to add custom logic between tool calls
    
    Disadvantages:
    - More complex graph setup
    - Requires careful state management
    - Agent must be split into multiple functions
    
    Note: This is a template for future implementation if needed.
    """
    raise NotImplementedError("ToolNode pattern not yet implemented. Use create_a2ui_loop_graph() instead.")
    
    # Template for future implementation:
    """
    from langgraph.prebuilt import ToolNode
    from tools.a2ui_tools import ComponentToolRegistry
    
    # Extended state with tool calls
    class A2UILoopState(AgentState):
        tool_calls: List[Dict]
        components: List[Dict]
    
    workflow = StateGraph(A2UILoopState)
    
    # Agent node: decides to call tool or finish
    async def agent_node(state: A2UILoopState, config=None):
        # Call LLM with tools
        # Update state with tool_calls
        return state
    
    # Tool node: executes tools
    tool_registry = ComponentToolRegistry()
    tools = [tool_registry.get_tool(name) for name in tool_registry.list_tools()]
    tool_node = ToolNode(tools)
    
    # Routing function
    def should_continue(state: A2UILoopState) -> Literal["tools", "end"]:
        if state.get("tool_calls"):
            return "tools"
        return "end"
    
    # Build graph
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")  # Loop back
    workflow.set_entry_point("agent")
    
    return workflow.compile()
    """
