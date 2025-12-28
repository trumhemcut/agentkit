"""
Insurance Supervisor Graph

LangGraph workflow implementing supervisor pattern for insurance domain.
Supervisor routes queries to specialized agents (policy, claims, quoting, support).
"""

import logging
from langgraph.graph import StateGraph, START, END
from typing import Literal
from agents.base_agent import AgentState
from agents.insurance import (
    InsuranceSupervisorAgent,
    InsurancePolicyAgent,
    ClaimsAgent,
    QuotingAgent,
    CustomerSupportAgent
)

logger = logging.getLogger(__name__)


def create_insurance_supervisor_graph(model: str = None, provider: str = None):
    """
    Create LangGraph workflow for insurance supervisor pattern
    
    Architecture:
        START → supervisor → [policy_agent | claims_agent | quoting_agent | support_agent] → END
    
    Args:
        model: Optional model name (e.g., 'qwen:7b')
        provider: Optional provider name (e.g., 'ollama', 'gemini')
    
    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(AgentState)
    
    # Initialize all agents with same model/provider
    supervisor = InsuranceSupervisorAgent(model=model, provider=provider)
    policy_agent = InsurancePolicyAgent(model=model, provider=provider)
    claims_agent = ClaimsAgent(model=model, provider=provider)
    quoting_agent = QuotingAgent(model=model, provider=provider)
    support_agent = CustomerSupportAgent(model=model, provider=provider)
    
    # Supervisor node
    async def supervisor_node(state: AgentState, config=None):
        """Supervisor analyzes query and determines routing"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        logger.info(f"Supervisor node: before run, selected_specialist={state.get('selected_specialist')}")
        
        async for event in supervisor.run(state):
            if event_callback:
                await event_callback(event)
        
        logger.info(f"Supervisor node: after run, selected_specialist={state.get('selected_specialist')}")
        
        return state
    
    # Policy agent node
    async def policy_node(state: AgentState, config=None):
        """Policy expert handles policy-related queries"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in policy_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Claims agent node
    async def claims_node(state: AgentState, config=None):
        """Claims expert handles claims-related queries"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in claims_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Quoting agent node
    async def quoting_node(state: AgentState, config=None):
        """Quoting expert handles pricing and quote requests"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in quoting_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Support agent node
    async def support_node(state: AgentState, config=None):
        """Support specialist handles general queries"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in support_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Routing function
    def route_to_specialist(state: AgentState) -> Literal["policy", "claims", "quoting", "support"]:
        """Route to appropriate specialist based on supervisor's decision"""
        selected = state.get("selected_specialist", "support")
        logger.info(f"Routing to specialist: {selected}")
        return selected
    
    # Build graph structure
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("policy", policy_node)
    workflow.add_node("claims", claims_node)
    workflow.add_node("quoting", quoting_node)
    workflow.add_node("support", support_node)
    
    # Define flow: START → supervisor → conditional routing to specialists → END
    workflow.add_edge(START, "supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        route_to_specialist,
        {
            "policy": "policy",
            "claims": "claims",
            "quoting": "quoting",
            "support": "support"
        }
    )
    
    # All specialists end the workflow
    workflow.add_edge("policy", END)
    workflow.add_edge("claims", END)
    workflow.add_edge("quoting", END)
    workflow.add_edge("support", END)
    
    return workflow.compile()
