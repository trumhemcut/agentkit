"""
Salary Viewer Agent Graph

LangGraph workflow for salary viewer agent with OTP verification.

This graph demonstrates the A2UI tool loop pattern for interactive components
that require user input before continuing the conversation.

Graph Structure:
    START → salary_viewer_agent → END

The agent internally manages:
1. OTP tool invocation
2. Waiting for user input
3. Verification and response
"""

import logging
from langgraph.graph import StateGraph, END
from agents.salary_viewer_agent import SalaryViewerAgent
from agents.base_agent import AgentState

logger = logging.getLogger(__name__)


def create_salary_viewer_graph(model: str = None, provider: str = None, max_iterations: int = 5):
    """
    Create LangGraph workflow for salary viewer agent.
    
    The agent handles the complete flow:
    - First request: Ask for OTP verification
    - Tool call: Generate OTP input component
    - User input: Receive OTP code
    - Final response: Reveal salary information
    
    Args:
        model: Model name (e.g., "qwen:7b", "gpt-4")
        provider: Provider name (e.g., "ollama", "azure_openai")
        max_iterations: Maximum tool-calling loop iterations
        
    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Creating salary viewer agent graph")
    
    # Create state graph
    workflow = StateGraph(AgentState)
    
    # Initialize agent
    agent_provider = provider if provider else "ollama"
    agent_model = model if model else "qwen:7b"
    
    logger.info(f"Salary viewer agent: provider={agent_provider}, model={agent_model}, max_iterations={max_iterations}")
    salary_agent = SalaryViewerAgent(
        provider=agent_provider,
        model=agent_model,
        max_iterations=max_iterations
    )
    
    # Define agent node
    async def salary_viewer_node(state: AgentState, config=None):
        """Execute salary viewer agent and stream events"""
        logger.debug(f"Salary viewer node processing - thread: {state['thread_id']}")
        
        # Get event callback from config
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        # Stream events from agent
        async for event in salary_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Add node to graph
    workflow.add_node("salary_viewer_agent", salary_viewer_node)
    
    # Set entry and exit
    workflow.set_entry_point("salary_viewer_agent")
    workflow.add_edge("salary_viewer_agent", END)
    
    # Compile and return
    logger.info("Salary viewer graph compiled successfully")
    return workflow.compile()
