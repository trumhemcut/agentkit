"""
Tests for A2UI Agent

Tests the A2UIAgent implementation including:
- UI component generation
- Mixed A2UI + AG-UI event streaming
- State management
- Error handling
"""

import pytest
import json
from agents.a2ui_agent import A2UIAgent
from agents.base_agent import AgentState


class TestA2UIAgent:
    """Test A2UI agent functionality"""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test A2UI agent can be initialized"""
        agent = A2UIAgent()
        
        assert agent is not None
        assert agent.a2ui_encoder is not None
        assert agent.agui_encoder is not None
    
    @pytest.mark.asyncio
    async def test_agent_generates_events(self):
        """Test that agent generates events"""
        agent = A2UIAgent()
        
        state: AgentState = {
            "messages": [{"role": "user", "content": "Show me a checkbox"}],
            "thread_id": "test-thread-123",
            "run_id": "test-run-456"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Should generate multiple events
        assert len(events) > 0
    
    @pytest.mark.asyncio
    async def test_agent_generates_a2ui_messages(self):
        """Test that agent generates A2UI messages"""
        agent = A2UIAgent()
        
        state: AgentState = {
            "messages": [{"role": "user", "content": "Create a checkbox"}],
            "thread_id": "test-thread",
            "run_id": "test-run"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Parse events to extract A2UI messages
        a2ui_events = []
        for event in events:
            if "data: " in event:
                json_str = event.replace("data: ", "").strip()
                if json_str:
                    try:
                        data = json.loads(json_str)
                        if data.get("type") in ["surfaceUpdate", "dataModelUpdate", "beginRendering"]:
                            a2ui_events.append(data)
                    except json.JSONDecodeError:
                        pass
        
        # Should have A2UI messages
        assert len(a2ui_events) > 0
        
        # Check for required A2UI message types
        types = [e["type"] for e in a2ui_events]
        assert "surfaceUpdate" in types
        assert "dataModelUpdate" in types
        assert "beginRendering" in types
    
    @pytest.mark.asyncio
    async def test_agent_creates_checkbox_component(self):
        """Test that agent creates checkbox component"""
        agent = A2UIAgent()
        
        state: AgentState = {
            "messages": [{"role": "user", "content": "Show checkbox"}],
            "thread_id": "test",
            "run_id": "test"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Find surfaceUpdate event
        surface_update = None
        for event in events:
            if "surfaceUpdate" in event:
                json_str = event.replace("data: ", "").strip()
                data = json.loads(json_str)
                if data.get("type") == "surfaceUpdate":
                    surface_update = data
                    break
        
        # Should have checkbox component
        assert surface_update is not None
        components = surface_update.get("components", [])
        
        # Find checkbox in components
        checkbox_found = False
        for comp in components:
            if "Checkbox" in comp.get("component", {}):
                checkbox_found = True
                break
        
        assert checkbox_found, "Checkbox component should be in surfaceUpdate"
    
    @pytest.mark.asyncio
    async def test_agent_initializes_data_model(self):
        """Test that agent initializes data model"""
        agent = A2UIAgent()
        
        state: AgentState = {
            "messages": [{"role": "user", "content": "Test"}],
            "thread_id": "test",
            "run_id": "test"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Find dataModelUpdate event
        data_update = None
        for event in events:
            if "dataModelUpdate" in event:
                json_str = event.replace("data: ", "").strip()
                data = json.loads(json_str)
                if data.get("type") == "dataModelUpdate":
                    data_update = data
                    break
        
        # Should have data model update
        assert data_update is not None
        assert "contents" in data_update
        assert len(data_update["contents"]) > 0
    
    @pytest.mark.asyncio
    async def test_agent_signals_begin_rendering(self):
        """Test that agent sends beginRendering message"""
        agent = A2UIAgent()
        
        state: AgentState = {
            "messages": [],
            "thread_id": "test",
            "run_id": "test"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Find beginRendering event
        begin_rendering = None
        for event in events:
            if "beginRendering" in event:
                json_str = event.replace("data: ", "").strip()
                data = json.loads(json_str)
                if data.get("type") == "beginRendering":
                    begin_rendering = data
                    break
        
        # Should have beginRendering
        assert begin_rendering is not None
        assert "surfaceId" in begin_rendering
        assert "rootComponentId" in begin_rendering
    
    @pytest.mark.asyncio
    async def test_agent_generates_agui_text_messages(self):
        """Test that agent also generates AG-UI text messages"""
        agent = A2UIAgent()
        
        state: AgentState = {
            "messages": [{"role": "user", "content": "Test"}],
            "thread_id": "test",
            "run_id": "test"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Find AG-UI text message events
        agui_events = []
        for event in events:
            if "TEXT_MESSAGE" in event:
                json_str = event.replace("data: ", "").strip()
                try:
                    data = json.loads(json_str)
                    if "TEXT_MESSAGE" in data.get("type", ""):
                        agui_events.append(data)
                except json.JSONDecodeError:
                    pass
        
        # Should have AG-UI text events
        assert len(agui_events) > 0
    
    @pytest.mark.asyncio
    async def test_agent_event_order(self):
        """Test that events are generated in correct order"""
        agent = A2UIAgent()
        
        state: AgentState = {
            "messages": [],
            "thread_id": "test",
            "run_id": "test"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Extract event types
        event_types = []
        for event in events:
            if "data: " in event:
                json_str = event.replace("data: ", "").strip()
                try:
                    data = json.loads(json_str)
                    event_types.append(data.get("type"))
                except json.JSONDecodeError:
                    pass
        
        # Check order: surfaceUpdate -> dataModelUpdate -> beginRendering
        surface_idx = event_types.index("surfaceUpdate") if "surfaceUpdate" in event_types else -1
        data_idx = event_types.index("dataModelUpdate") if "dataModelUpdate" in event_types else -1
        begin_idx = event_types.index("beginRendering") if "beginRendering" in event_types else -1
        
        assert surface_idx >= 0
        assert data_idx >= 0
        assert begin_idx >= 0
        
        # Surface update should come before data update
        assert surface_idx < data_idx
        # Data update should come before begin rendering
        assert data_idx < begin_idx
    
    @pytest.mark.asyncio
    async def test_agent_with_different_messages(self):
        """Test agent with different user messages"""
        agent = A2UIAgent()
        
        test_messages = [
            "Show me a checkbox",
            "Create a terms agreement",
            "Display an interactive element"
        ]
        
        for msg in test_messages:
            state: AgentState = {
                "messages": [{"role": "user", "content": msg}],
                "thread_id": "test",
                "run_id": "test"
            }
            
            events = []
            async for event in agent.run(state):
                events.append(event)
            
            # Should generate events for all messages
            assert len(events) > 0


class TestA2UIAgentErrorHandling:
    """Test error handling in A2UI agent"""
    
    @pytest.mark.asyncio
    async def test_agent_with_empty_state(self):
        """Test agent handles empty state gracefully"""
        agent = A2UIAgent()
        
        state: AgentState = {
            "messages": [],
            "thread_id": "test",
            "run_id": "test"
        }
        
        # Should not raise exception
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        assert len(events) > 0
    
    @pytest.mark.asyncio
    async def test_agent_with_missing_fields(self):
        """Test agent handles missing state fields"""
        agent = A2UIAgent()
        
        # Missing messages field
        state: AgentState = {
            "thread_id": "test",
            "run_id": "test"
        }
        
        # Should handle gracefully
        events = []
        try:
            async for event in agent.run(state):
                events.append(event)
        except KeyError:
            pytest.fail("Agent should handle missing messages field")


class TestA2UIFormAgent:
    """Test A2UIFormAgent (future implementation)"""
    
    @pytest.mark.asyncio
    async def test_form_agent_not_implemented(self):
        """Test that form agent raises NotImplementedError"""
        from agents.a2ui_agent import A2UIFormAgent
        
        agent = A2UIFormAgent()
        state: AgentState = {
            "messages": [],
            "thread_id": "test",
            "run_id": "test"
        }
        
        with pytest.raises(NotImplementedError):
            generator = agent.run(state)
            async for _ in generator:
                pass
