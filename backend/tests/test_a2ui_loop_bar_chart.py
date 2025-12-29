"""
Test A2UI Loop Agent with Bar Charts

This test verifies that the loop agent can create bar charts with proper
data model path handling.
"""
import pytest
from agents.a2ui_agent_with_loop import A2UIAgentWithLoop
from protocols.a2ui_encoder import is_a2ui_message
import json


@pytest.mark.asyncio
async def test_loop_agent_bar_chart_single():
    """Test that loop agent can create a single bar chart"""
    agent = A2UIAgentWithLoop(provider="ollama", model="qwen2.5:7b")
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Create a bar chart showing Q1 and Q2 sales. Q1 revenue: 50000, profit: 15000. Q2 revenue: 60000, profit: 18000."
            }
        ],
        "thread_id": "test-loop-bar-1",
        "run_id": "test-run-1"
    }
    
    try:
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Verify A2UI messages were generated
        a2ui_events = [e for e in events if is_a2ui_message(e)]
        
        # Should have: surfaceUpdate, dataModelUpdate(s), beginRendering
        assert len(a2ui_events) >= 3, f"Expected at least 3 A2UI events, got {len(a2ui_events)}"
        
        # Verify bar chart component exists in surface update
        surface_updates = [e for e in a2ui_events if e.get("type") == "surfaceUpdate"]
        assert len(surface_updates) > 0, "No surface updates found"
        
        components = surface_updates[0].get("components", [])
        bar_chart_components = [
            c for c in components 
            if "BarChart" in c.get("component", {})
        ]
        assert len(bar_chart_components) > 0, f"No bar chart components found. Components: {components}"
        
        # Verify bar chart has correct structure
        bar_chart = bar_chart_components[0]["component"]["BarChart"]
        assert "title" in bar_chart
        assert "data" in bar_chart
        assert "path" in bar_chart["data"], "Bar chart should have data.path"
        
        # Verify data model update with correct path
        data_updates = [e for e in a2ui_events if e.get("type") == "dataModelUpdate"]
        assert len(data_updates) > 0, "No data model updates found"
        
        # Find the data update for the bar chart
        chart_data_path = bar_chart["data"]["path"]
        # Extract parent path (e.g., /ui/bar-chart-abc123 from /ui/bar-chart-abc123/chartData)
        expected_parent_path = '/'.join(chart_data_path.split('/')[:-1])
        
        matching_data_updates = [
            du for du in data_updates 
            if du.get("path") == expected_parent_path
        ]
        assert len(matching_data_updates) > 0, f"No data update found for path: {expected_parent_path}"
        
        # Verify the data content has chartData key
        data_update = matching_data_updates[0]
        contents = data_update.get("contents", [])
        assert len(contents) > 0, "Data model contents should not be empty"
        
        # Check for chartData in contents
        has_chart_data = any(
            c.get("key") == "chartData" or "data" in c.get("value_map", {})
            for c in contents
        )
        assert has_chart_data, f"Data contents should have chartData. Contents: {contents}"
        
        print("✓ Bar chart created successfully with proper data model path")
        
    except Exception as e:
        # If model doesn't support tools, test should pass with warning
        if "tool" in str(e).lower():
            pytest.skip(f"Model doesn't support tool calling: {e}")
        else:
            raise


@pytest.mark.asyncio
async def test_loop_agent_bar_chart_with_other_components():
    """Test that loop agent can create bar chart alongside other components"""
    agent = A2UIAgentWithLoop(provider="ollama", model="qwen2.5:7b")
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Create a bar chart showing monthly sales (Jan: 100, Feb: 150, Mar: 200) and add a submit button below it."
            }
        ],
        "thread_id": "test-loop-bar-2",
        "run_id": "test-run-2"
    }
    
    try:
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Verify A2UI messages
        a2ui_events = [e for e in events if is_a2ui_message(e)]
        assert len(a2ui_events) >= 3
        
        # Find surface update
        surface_updates = [e for e in a2ui_events if e.get("type") == "surfaceUpdate"]
        assert len(surface_updates) > 0
        
        components = surface_updates[0].get("components", [])
        
        # Should have bar chart
        bar_chart_components = [
            c for c in components 
            if "BarChart" in c.get("component", {})
        ]
        assert len(bar_chart_components) > 0, "Should have bar chart component"
        
        # Should have button
        button_components = [
            c for c in components 
            if "Button" in c.get("component", {})
        ]
        assert len(button_components) > 0, "Should have button component"
        
        # Should have Column container for multiple components
        column_containers = [
            c for c in components 
            if "Column" in c.get("component", {})
        ]
        assert len(column_containers) > 0, "Should have Column container for multiple components"
        
        # Verify multiple data model updates (one for each component)
        data_updates = [e for e in a2ui_events if e.get("type") == "dataModelUpdate"]
        assert len(data_updates) >= 2, f"Should have at least 2 data updates, got {len(data_updates)}"
        
        print("✓ Bar chart + button created successfully with separate data models")
        
    except Exception as e:
        if "tool" in str(e).lower():
            pytest.skip(f"Model doesn't support tool calling: {e}")
        else:
            raise


if __name__ == "__main__":
    import asyncio
    
    print("Running bar chart tests...")
    asyncio.run(test_loop_agent_bar_chart_single())
    print()
    asyncio.run(test_loop_agent_bar_chart_with_other_components())
    print("\nAll tests passed!")
