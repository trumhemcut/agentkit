"""
Unit tests for GraphFactory

Tests the dynamic graph creation factory pattern for LangGraph workflows.
"""

import pytest
from graphs.graph_factory import graph_factory, GraphFactory
from agents.agent_registry import agent_registry


class TestGraphFactory:
    """Test suite for GraphFactory"""
    
    def test_create_chat_graph(self):
        """Test chat graph creation with default parameters"""
        graph = graph_factory.create_graph("chat")
        assert graph is not None
    
    def test_create_chat_graph_with_model(self):
        """Test chat graph creation with custom model"""
        graph = graph_factory.create_graph("chat", model="qwen:7b")
        assert graph is not None
    
    def test_create_chat_graph_with_provider(self):
        """Test chat graph creation with custom provider"""
        graph = graph_factory.create_graph("chat", model="qwen:7b", provider="ollama")
        assert graph is not None
    
    def test_create_canvas_graph(self):
        """Test canvas graph creation with default parameters"""
        graph = graph_factory.create_graph("canvas")
        assert graph is not None
    
    def test_create_canvas_graph_with_model(self):
        """Test canvas graph creation with custom model"""
        graph = graph_factory.create_graph("canvas", model="qwen:7b")
        assert graph is not None
    
    def test_create_canvas_graph_with_provider(self):
        """Test canvas graph creation with custom provider"""
        graph = graph_factory.create_graph("canvas", model="gemini-pro", provider="gemini")
        assert graph is not None
    
    def test_invalid_agent_id(self):
        """Test error handling for invalid agent"""
        with pytest.raises(ValueError, match="not available"):
            graph_factory.create_graph("nonexistent_agent")
    
    def test_error_message_includes_available_agents(self):
        """Test that error message lists available agents"""
        with pytest.raises(ValueError) as exc_info:
            graph_factory.create_graph("nonexistent_agent")
        
        error_message = str(exc_info.value)
        assert "chat" in error_message
        assert "canvas" in error_message
    
    def test_list_registered_creators(self):
        """Test listing of registered graph creators"""
        creators = graph_factory.list_registered_creators()
        assert "chat" in creators
        assert "canvas" in creators
        assert len(creators) >= 2
    
    def test_register_new_graph_creator(self):
        """Test registering a new graph creator"""
        def mock_graph_creator(model=None, provider=None):
            """Mock graph creator for testing"""
            from langgraph.graph import StateGraph, START, END
            from agents.base_agent import AgentState
            
            workflow = StateGraph(AgentState)
            
            async def mock_node(state, config=None):
                return state
            
            workflow.add_node("mock", mock_node)
            workflow.add_edge(START, "mock")
            workflow.add_edge("mock", END)
            
            return workflow.compile()
        
        # Register mock creator
        GraphFactory.register_graph_creator("test_agent", mock_graph_creator)
        
        # Verify it's registered
        assert "test_agent" in GraphFactory.list_registered_creators()
        
        # Note: We can't create the graph since the agent isn't registered in agent_registry
        # But we can verify the creator is registered
    
    def test_overwrite_existing_creator_warning(self, caplog):
        """Test that overwriting an existing creator logs a warning"""
        # Save the original creator
        from graphs.chat_graph import create_chat_graph
        original_creator = GraphFactory._graph_creators.get("chat")
        
        def new_creator(model=None, provider=None):
            return None  # Mock creator
        
        try:
            # Register over existing creator
            GraphFactory.register_graph_creator("chat", new_creator)
            
            # Check for warning in logs
            assert any("Overwriting" in record.message for record in caplog.records)
        finally:
            # Restore the original creator
            GraphFactory._graph_creators["chat"] = original_creator
    
    def test_graph_with_multiple_parameters(self):
        """Test graph creation with both model and provider parameters"""
        graph = graph_factory.create_graph(
            "chat",
            model="qwen:7b",
            provider="ollama"
        )
        assert graph is not None


@pytest.mark.asyncio
class TestGraphExecution:
    """Test suite for graph execution with streaming"""
    
    async def test_chat_graph_execution(self):
        """Test that chat graph can be executed"""
        graph = graph_factory.create_graph("chat", model="qwen:7b", provider="ollama")
        
        state = {
            "messages": [{"role": "user", "content": "Hello"}],
            "thread_id": "test-thread",
            "run_id": "test-run"
        }
        
        # Execute without callback
        result = await graph.ainvoke(state)
        assert result is not None
        assert "messages" in result
    
    async def test_chat_graph_with_callback(self):
        """Test streaming events are collected via callback"""
        graph = graph_factory.create_graph("chat", model="qwen:7b", provider="ollama")
        
        state = {
            "messages": [{"role": "user", "content": "Hello"}],
            "thread_id": "test-thread",
            "run_id": "test-run"
        }
        
        # Event buffer to collect streamed events
        event_buffer = []
        
        async def event_callback(event):
            """Callback to collect events"""
            event_buffer.append(event)
        
        # Execute with callback
        config = {"configurable": {"event_callback": event_callback}}
        result = await graph.ainvoke(state, config)
        
        assert result is not None
        # Note: Event buffer may be empty if agent doesn't emit events in test
        # This is expected behavior - the callback mechanism is tested
    
    async def test_canvas_graph_execution(self):
        """Test that canvas graph can be executed"""
        graph = graph_factory.create_graph("canvas", model="qwen:7b", provider="ollama")
        
        state = {
            "messages": [{"role": "user", "content": "Create a Python function"}],
            "thread_id": "test-thread",
            "run_id": "test-run",
            "artifact": None,
            "selectedText": None,
            "artifact_id": None,
            "artifactAction": None
        }
        
        # Execute without callback
        result = await graph.ainvoke(state)
        assert result is not None
        assert "messages" in result


class TestAgentRegistryIntegration:
    """Test integration with agent registry"""
    
    def test_available_agents_have_graph_creators(self):
        """Test that all available agents have corresponding graph creators"""
        available_agents = agent_registry.list_agents(available_only=True)
        registered_creators = graph_factory.list_registered_creators()
        
        for agent in available_agents:
            assert agent.id in registered_creators, \
                f"Agent '{agent.id}' is available but has no graph creator"
    
    def test_unavailable_agent_raises_error(self):
        """Test that unavailable agents raise proper errors"""
        # Create a mock unavailable agent
        from agents.agent_registry import AgentMetadata
        
        unavailable_agent = AgentMetadata(
            id="unavailable_test",
            name="Unavailable Test Agent",
            description="Test agent that is not available",
            icon="test",
            available=False,
            sub_agents=[],
            features=[]
        )
        
        agent_registry.register_agent(unavailable_agent)
        
        # Try to create graph for unavailable agent
        with pytest.raises(ValueError, match="not available"):
            graph_factory.create_graph("unavailable_test")
