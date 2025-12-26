"""
Tests for Graph Factory with A2UI Agent

Tests that the graph factory correctly creates and manages A2UI graphs.
"""

import pytest
from graphs.graph_factory import GraphFactory


class TestGraphFactoryA2UI:
    """Test graph factory with A2UI agent"""
    
    def test_a2ui_creator_registered(self):
        """Test that A2UI graph creator is registered"""
        creators = GraphFactory.list_registered_creators()
        
        assert "a2ui" in creators
    
    def test_create_a2ui_graph(self):
        """Test that factory can create A2UI graph"""
        graph = GraphFactory.create_graph("a2ui")
        
        assert graph is not None
        assert hasattr(graph, 'ainvoke')
    
    def test_create_a2ui_graph_with_model(self):
        """Test that factory can create A2UI graph with model parameter"""
        # A2UI agent doesn't use model, but should accept the parameter
        graph = GraphFactory.create_graph("a2ui", model="qwen:7b", provider="ollama")
        
        assert graph is not None
    
    @pytest.mark.asyncio
    async def test_a2ui_graph_execution(self):
        """Test that factory-created A2UI graph can execute"""
        from agents.base_agent import AgentState
        
        graph = GraphFactory.create_graph("a2ui")
        
        state: AgentState = {
            "messages": [{"role": "user", "content": "Test"}],
            "thread_id": "test",
            "run_id": "test"
        }
        
        result = await graph.ainvoke(state)
        
        assert result is not None
        assert result["thread_id"] == "test"
