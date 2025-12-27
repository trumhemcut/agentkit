"""
A2UI Agent Graph

Simple LangGraph workflow for the A2UI agent that generates interactive UI components.
"""

import logging
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from agents.a2ui_agent import A2UIAgent
from agents.base_agent import AgentState

logger = logging.getLogger(__name__)


def create_a2ui_graph(model: str = None, provider: str = None):
    """
    Create LangGraph workflow for A2UI agent.
    
    This is a simple single-node graph since the A2UI agent doesn't require
    complex multi-agent orchestration. It uses LLM + tool calling to dynamically
    generate UI components based on user prompts.
    
    Args:
        model: Model name to use for component generation (e.g., "gpt-4o", "qwen:7b")
        provider: Provider type (e.g., "azure-openai", "ollama", "gemini")
    
    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Creating A2UI agent graph")
    
    # Create state graph
    workflow = StateGraph(AgentState)
    
    # Create A2UI agent instance with specified model and provider
    # Use defaults if not provided
    agent_provider = provider if provider else "ollama"
    agent_model = model if model else "qwen:7b"
    
    logger.info(f"Initializing A2UI agent with provider={agent_provider}, model={agent_model}")
    a2ui_agent = A2UIAgent(provider=agent_provider, model=agent_model)
    
    # Define agent node
    async def a2ui_node(state: AgentState, config=None):
        """Execute A2UI agent and stream events"""
        logger.debug(f"A2UI node processing - thread: {state['thread_id']}")
        
        # Get event callback from config (if available)
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        # Stream events from agent
        async for event in a2ui_agent.run(state):
            if event_callback:
                # Send event through callback for SSE streaming
                await event_callback(event)
        
        return state
    
    # Add node to graph
    workflow.add_node("a2ui_agent", a2ui_node)
    
    # Set entry point
    workflow.set_entry_point("a2ui_agent")
    
    # End after agent execution
    workflow.add_edge("a2ui_agent", END)
    
    # Compile and return
    return workflow.compile()
