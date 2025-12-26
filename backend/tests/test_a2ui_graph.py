"""
Tests for A2UI Graph

Tests the LangGraph workflow for A2UI agent.
"""

import pytest
from graphs.a2ui_graph import create_a2ui_graph
from agents.base_agent import AgentState


class TestA2UIGraph:
    """Test A2UI graph creation and execution"""
    
    def test_create_a2ui_graph(self):
        """Test that A2UI graph can be created"""
        graph = create_a2ui_graph()
        
        assert graph is not None
        # Graph should be compiled
        assert hasattr(graph, 'ainvoke')
    
    @pytest.mark.asyncio
    async def test_a2ui_graph_execution(self):
        """Test that A2UI graph can execute"""
        graph = create_a2ui_graph()
        
        state: AgentState = {
            "messages": [{"role": "user", "content": "Show checkbox"}],
            "thread_id": "test-thread",
            "run_id": "test-run"
        }
        
        # Execute without callback
        result = await graph.ainvoke(state)
        
        assert result is not None
        assert result["thread_id"] == "test-thread"
        assert result["run_id"] == "test-run"
    
    @pytest.mark.asyncio
    async def test_a2ui_graph_with_callback(self):
        """Test that A2UI graph works with event callback"""
        graph = create_a2ui_graph()
        
        state: AgentState = {
            "messages": [],
            "thread_id": "test",
            "run_id": "test"
        }
        
        # Collect events via callback
        events = []
        
        async def event_callback(event):
            events.append(event)
        
        config = {"configurable": {"event_callback": event_callback}}
        
        # Execute with callback
        result = await graph.ainvoke(state, config)
        
        assert result is not None
        # Should have collected events
        assert len(events) > 0
        
        # Check for A2UI events
        a2ui_events = [e for e in events if "surfaceUpdate" in e or "dataModelUpdate" in e]
        assert len(a2ui_events) > 0
