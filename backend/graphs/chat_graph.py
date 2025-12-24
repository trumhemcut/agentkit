from langgraph.graph import StateGraph, START, END
from agents.base_agent import AgentState
from agents.chat_agent import ChatAgent


def create_chat_graph(model: str = None):
    """Create LangGraph state graph for chat agent with streaming support
    
    Args:
        model: Optional model name to use (e.g., 'qwen:7b', 'llama2:13b')
    """
    workflow = StateGraph(AgentState)
    
    # Create chat agent with optional model
    chat_agent = ChatAgent(model=model)
    
    async def chat_node(state: AgentState, config=None):
        """Wrapper node that dispatches agent events"""
        # Get event callback from config
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in chat_agent.run(state):
            # If callback is provided, call it with the event
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Add agent node
    workflow.add_node("chat", chat_node)
    
    # Define graph flow
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
    
    return workflow.compile()
