from langgraph.graph import StateGraph, START, END
from agents.base_agent import AgentState
from agents.chat_agent import ChatAgent


def create_chat_graph():
    """Create LangGraph state graph for chat agent"""
    workflow = StateGraph(AgentState)
    
    chat_agent = ChatAgent()
    
    # Add agent node
    workflow.add_node("chat", chat_agent.run)
    
    # Define graph flow
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)
    
    return workflow.compile()
