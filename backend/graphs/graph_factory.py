"""
Graph Factory for LangGraph Workflows

Provides centralized factory for creating LangGraph workflows based on agent_id.
Ensures all agent execution flows through LangGraph state graphs.
"""

import logging
from typing import Optional, Callable
from graphs.chat_graph import create_chat_graph
from graphs.canvas_graph import create_canvas_graph
from graphs.a2ui_graph import create_a2ui_graph
from graphs.a2ui_loop_graph import create_a2ui_loop_graph
from graphs.insurance_supervisor_graph import create_insurance_supervisor_graph
from graphs.salary_viewer_graph import create_salary_viewer_graph
from agents.agent_registry import agent_registry

logger = logging.getLogger(__name__)


class GraphFactory:
    """Factory for creating LangGraph workflows based on agent_id"""
    
    # Registry of graph creator functions
    _graph_creators = {
        "chat": create_chat_graph,
        "canvas": create_canvas_graph,
        "a2ui": create_a2ui_graph,
        "a2ui-loop": create_a2ui_loop_graph,  # A2UI with tool-calling loop
        "insurance-supervisor": create_insurance_supervisor_graph,
        "salary-viewer": create_salary_viewer_graph,  # Salary viewer with OTP verification
    }
    
    @classmethod
    def create_graph(
        cls, 
        agent_id: str, 
        model: Optional[str] = None, 
        provider: Optional[str] = None
    ):
        """
        Dynamically create and compile a graph for the given agent_id
        
        Args:
            agent_id: Identifier from agent registry (e.g., "chat", "canvas")
            model: Optional model name (e.g., "qwen:7b", "gemini-pro")
            provider: Optional provider name (e.g., "ollama", "gemini", "azure-openai")
            
        Returns:
            Compiled LangGraph workflow ready for execution (CompiledStateGraph)
            
        Raises:
            ValueError: If agent_id is not registered, unavailable, or no graph creator exists
            
        Example:
            >>> graph = graph_factory.create_graph("chat", model="qwen:7b", provider="ollama")
            >>> config = {"configurable": {"event_callback": callback_fn}}
            >>> result = await graph.ainvoke(state, config)
        """
        # Validate agent exists and is available
        if not agent_registry.is_available(agent_id):
            available_agents = [a.id for a in agent_registry.list_agents(available_only=True)]
            raise ValueError(
                f"Agent '{agent_id}' not available or not registered. "
                f"Available agents: {', '.join(available_agents)}"
            )
        
        # Get graph creator function
        creator = cls._graph_creators.get(agent_id)
        if not creator:
            raise ValueError(
                f"No graph creator found for agent '{agent_id}'. "
                f"Registered creators: {', '.join(cls._graph_creators.keys())}"
            )
        
        # Create and compile graph with model/provider parameters
        logger.info(f"Creating graph for agent '{agent_id}' with model={model}, provider={provider}")
        return creator(model=model, provider=provider)
    
    @classmethod
    def register_graph_creator(cls, agent_id: str, creator_func: Callable):
        """
        Register a new graph creator function
        
        Allows extending the factory with new agents without modifying this file.
        
        Args:
            agent_id: Unique agent identifier (must match agent_registry)
            creator_func: Function that creates and compiles a graph
                         Signature: (model: str, provider: str) -> CompiledGraph
                         
        Example:
            >>> def create_myagent_graph(model=None, provider=None):
            ...     workflow = StateGraph(MyAgentState)
            ...     # ... build graph ...
            ...     return workflow.compile()
            >>> 
            >>> graph_factory.register_graph_creator("myagent", create_myagent_graph)
        """
        if agent_id in cls._graph_creators:
            logger.warning(f"Overwriting existing graph creator for agent '{agent_id}'")
        
        cls._graph_creators[agent_id] = creator_func
        logger.info(f"Registered graph creator for agent '{agent_id}'")
    
    @classmethod
    def list_registered_creators(cls) -> list:
        """Get list of agent_ids with registered graph creators"""
        return list(cls._graph_creators.keys())


# Singleton instance
graph_factory = GraphFactory()
