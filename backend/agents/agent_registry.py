"""
Agent Registry System

Centralized registry for managing available agents in the system.
Provides metadata and discovery capabilities for all registered agents.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AgentMetadata:
    """Metadata describing an agent"""
    id: str  # Unique identifier (e.g., "chat", "canvas")
    name: str  # Display name (e.g., "Chat Agent", "Canvas Agent")
    description: str  # Brief description of agent capabilities
    icon: str  # Icon identifier for frontend
    available: bool  # Whether agent is currently available
    sub_agents: List[str]  # List of sub-agent IDs in graph
    features: List[str]  # List of feature tags


class AgentRegistry:
    """Registry for managing available agents"""
    
    def __init__(self):
        self._agents: Dict[str, AgentMetadata] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize default agents"""
        # Register ChatAgent
        self.register_agent(AgentMetadata(
            id="chat",
            name="Chat Agent",
            description="General purpose conversational agent",
            icon="message-circle",
            available=True,
            sub_agents=[],
            features=["conversation", "streaming"]
        ))
        
        # Register CanvasAgent
        self.register_agent(AgentMetadata(
            id="canvas",
            name="Canvas Agent",
            description="Multi-agent system with artifact generation and editing",
            icon="layout",
            available=True,
            sub_agents=["generator", "editor"],
            features=["artifacts", "code-generation", "multi-step"]
        ))
        
        # Register A2UIAgent
        self.register_agent(AgentMetadata(
            id="a2ui",
            name="A2UI Agent",
            description="Agent that generates interactive UI components using A2UI protocol",
            icon="layout-grid",
            available=True,
            sub_agents=[],
            features=["ui-components", "interactive", "a2ui-protocol"]
        ))
        
        # Register A2UI Loop Agent
        self.register_agent(AgentMetadata(
            id="a2ui-loop",
            name="A2UI Agent (Loop)",
            description="Multi-component UI generation with tool-calling loop pattern for complex forms",
            icon="layout-grid",
            available=True,
            sub_agents=[],
            features=["ui-components", "multi-component", "tool-loop", "react-pattern", "complex-ui"]
        ))
        
        # Register Insurance Supervisor Agent
        self.register_agent(AgentMetadata(
            id="insurance-supervisor",
            name="Insurance Supervisor",
            description="Multi-agent system for insurance queries with specialized agents for policies, claims, quotes, and customer support",
            icon="shield",
            available=True,
            sub_agents=["policy_agent", "claims_agent", "quoting_agent", "support_agent"],
            features=["insurance", "supervisor-pattern", "multi-agent", "vietnamese", "quoting"]
        ))
    
    def register_agent(self, metadata: AgentMetadata):
        """Register a new agent"""
        self._agents[metadata.id] = metadata
    
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID"""
        return self._agents.get(agent_id)
    
    def list_agents(self, available_only: bool = True) -> List[AgentMetadata]:
        """List all registered agents"""
        agents = list(self._agents.values())
        if available_only:
            agents = [a for a in agents if a.available]
        return agents
    
    def is_available(self, agent_id: str) -> bool:
        """Check if agent is available"""
        agent = self.get_agent(agent_id)
        return agent.available if agent else False


# Global registry instance
agent_registry = AgentRegistry()
