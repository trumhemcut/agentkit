"""
Integration test for A2UI bar chart generation

This test verifies end-to-end bar chart generation from agent to A2UI messages.
"""
import pytest
from agents.a2ui_agent import A2UIAgent
from protocols.a2ui_encoder import is_a2ui_message


@pytest.mark.asyncio
async def test_bar_chart_generation_flow():
    """Test complete bar chart generation from agent"""
    agent = A2UIAgent(provider="ollama", model="qwen2.5")
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Create a bar chart showing desktop vs mobile users for Jan and Feb. Desktop: 186 and 305. Mobile: 80 and 200."
            }
        ],
        "thread_id": "test-thread",
        "run_id": "test-run"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Verify A2UI messages were generated
    a2ui_events = [e for e in events if is_a2ui_message(e)]
    
    # Should have: surfaceUpdate, dataModelUpdate, beginRendering
    assert len(a2ui_events) >= 3, f"Expected at least 3 A2UI events, got {len(a2ui_events)}"
    
    # Verify bar chart component exists
    surface_updates = [e for e in a2ui_events if e.get("type") == "surfaceUpdate"]
    assert len(surface_updates) > 0, "No surface updates found"
    
    components = surface_updates[0].get("components", [])
    bar_chart_components = [
        c for c in components 
        if "BarChart" in c.get("component", {})
    ]
    assert len(bar_chart_components) > 0, "No bar chart components found"


@pytest.mark.asyncio
async def test_bar_chart_with_custom_colors():
    """Test bar chart generation with custom colors"""
    agent = A2UIAgent(provider="ollama", model="qwen2.5")
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Create a bar chart for Q1 sales with revenue in green and profit in blue. Q1: revenue 50000, profit 15000. Q2: revenue 60000, profit 18000."
            }
        ],
        "thread_id": "test-thread-2",
        "run_id": "test-run-2"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Verify A2UI messages
    a2ui_events = [e for e in events if is_a2ui_message(e)]
    assert len(a2ui_events) >= 3
    
    # Find bar chart component
    surface_updates = [e for e in a2ui_events if e.get("type") == "surfaceUpdate"]
    assert len(surface_updates) > 0
    
    components = surface_updates[0].get("components", [])
    bar_chart_components = [
        c for c in components 
        if "BarChart" in c.get("component", {})
    ]
    assert len(bar_chart_components) > 0
    
    # Verify chart has title and data keys
    bar_chart = bar_chart_components[0]["component"]["BarChart"]
    assert "title" in bar_chart
    assert "dataKeys" in bar_chart


@pytest.mark.asyncio
async def test_bar_chart_data_model_update():
    """Test that data model updates include chart data"""
    agent = A2UIAgent(provider="ollama", model="qwen2.5")
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Show me a bar chart of monthly sales: Jan 100, Feb 150, Mar 200."
            }
        ],
        "thread_id": "test-thread-3",
        "run_id": "test-run-3"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Find data model updates
    a2ui_events = [e for e in events if is_a2ui_message(e)]
    data_model_updates = [e for e in a2ui_events if e.get("type") == "dataModelUpdate"]
    
    assert len(data_model_updates) > 0, "No data model updates found"
    
    # Verify one of them contains chart data
    has_chart_data = False
    for update in data_model_updates:
        contents = update.get("contents", [])
        for content in contents:
            if "chartData" in content.get("key", ""):
                has_chart_data = True
                break
    
    assert has_chart_data, "No chart data found in data model updates"


@pytest.mark.asyncio
async def test_bar_chart_rendering_signal():
    """Test that beginRendering event is sent after chart creation"""
    agent = A2UIAgent(provider="ollama", model="qwen2.5")
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Create a simple bar chart with categories A, B, C and values 10, 20, 30."
            }
        ],
        "thread_id": "test-thread-4",
        "run_id": "test-run-4"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Find beginRendering events
    a2ui_events = [e for e in events if is_a2ui_message(e)]
    rendering_events = [e for e in a2ui_events if e.get("type") == "beginRendering"]
    
    assert len(rendering_events) > 0, "No beginRendering event found"
    
    # Verify it has required fields
    rendering_event = rendering_events[0]
    assert "surfaceId" in rendering_event
    assert "rootComponentId" in rendering_event


@pytest.mark.asyncio
async def test_bar_chart_with_single_series():
    """Test bar chart with single data series"""
    agent = A2UIAgent(provider="ollama", model="qwen2.5")
    
    state = {
        "messages": [
            {
                "role": "user",
                "content": "Show a bar chart of product sales: Product A sold 50, Product B sold 75, Product C sold 30."
            }
        ],
        "thread_id": "test-thread-5",
        "run_id": "test-run-5"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Verify chart was created
    a2ui_events = [e for e in events if is_a2ui_message(e)]
    surface_updates = [e for e in a2ui_events if e.get("type") == "surfaceUpdate"]
    
    assert len(surface_updates) > 0
    components = surface_updates[0].get("components", [])
    bar_chart_components = [
        c for c in components 
        if "BarChart" in c.get("component", {})
    ]
    
    assert len(bar_chart_components) > 0


@pytest.mark.asyncio
async def test_bar_chart_tool_availability():
    """Test that bar chart tool is available in agent's toolset"""
    agent = A2UIAgent(provider="ollama", model="qwen2.5")
    
    # Get tool schemas
    from tools.a2ui_tools import ComponentToolRegistry
    registry = ComponentToolRegistry()
    schemas = registry.get_tool_schemas()
    
    # Find bar chart tool
    bar_chart_tools = [
        s for s in schemas 
        if s.get("function", {}).get("name") == "create_bar_chart"
    ]
    
    assert len(bar_chart_tools) == 1, "Bar chart tool not found in registry"
    
    tool_schema = bar_chart_tools[0]
    assert tool_schema["type"] == "function"
    assert "title" in tool_schema["function"]["parameters"]["properties"]
    assert "data" in tool_schema["function"]["parameters"]["properties"]
    assert "data_keys" in tool_schema["function"]["parameters"]["properties"]
