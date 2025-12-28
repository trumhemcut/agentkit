"""
Test suite for Bar Chart A2UI component generation
"""
import pytest
from tools.a2ui_tools import BarChartTool, ComponentToolRegistry
from protocols.a2ui_types import create_bar_chart_component


def test_bar_chart_tool_schema():
    """Test tool schema generation"""
    tool = BarChartTool()
    
    # Check tool properties
    assert tool.name == "create_bar_chart"
    assert "bar chart" in tool.description.lower()
    
    # Check parameters schema
    params = tool.parameters
    assert params["type"] == "object"
    assert "title" in params["properties"]
    assert "data" in params["properties"]
    assert "data_keys" in params["properties"]
    assert "title" in params["required"]
    assert "data" in params["required"]
    assert "data_keys" in params["required"]


def test_bar_chart_tool_name_and_description():
    """Test tool name and description"""
    tool = BarChartTool()
    
    assert tool.name == "create_bar_chart"
    assert "bar chart" in tool.description.lower()
    assert "visualization" in tool.description.lower()


def test_bar_chart_component_generation():
    """Test bar chart component generation"""
    tool = BarChartTool()
    
    result = tool.generate_component(
        title="User Statistics",
        description="Monthly users",
        data=[
            {"category": "Jan", "desktop": 186, "mobile": 80},
            {"category": "Feb", "desktop": 305, "mobile": 200},
        ],
        data_keys=["desktop", "mobile"],
        colors={"desktop": "#2563eb", "mobile": "#60a5fa"}
    )
    
    assert "component" in result
    assert "data_model" in result
    assert "component_id" in result
    assert result["component_id"].startswith("bar-chart-")
    
    # Check component structure
    component = result["component"]
    assert component.id == result["component_id"]
    assert "BarChart" in component.component
    
    bar_chart = component.component["BarChart"]
    assert bar_chart["title"]["literalString"] == "User Statistics"
    assert bar_chart["description"]["literalString"] == "Monthly users"
    assert bar_chart["dataKeys"]["literalString"] == "desktop,mobile"
    assert bar_chart["colors"]["literalMap"] == {"desktop": "#2563eb", "mobile": "#60a5fa"}
    
    # Check data model structure
    data_model = result["data_model"]
    assert "path" in data_model
    assert "contents" in data_model
    assert len(data_model["contents"]) == 1
    
    content = data_model["contents"][0]
    assert content.key == "chartData"
    assert content.value_map is not None
    assert "data" in content.value_map
    assert "dataKeys" in content.value_map
    assert len(content.value_map["data"]) == 2


def test_bar_chart_component_without_colors():
    """Test bar chart generation without custom colors"""
    tool = BarChartTool()
    
    result = tool.generate_component(
        title="Sales Data",
        data=[{"category": "Q1", "revenue": 50000}],
        data_keys=["revenue"]
    )
    
    component = result["component"]
    bar_chart = component.component["BarChart"]
    assert bar_chart["colors"]["literalMap"] == {}


def test_bar_chart_component_with_custom_data_path():
    """Test bar chart with custom data path"""
    tool = BarChartTool()
    
    result = tool.generate_component(
        title="Custom Path Chart",
        data=[{"category": "A", "value": 100}],
        data_keys=["value"],
        data_path="/custom/path/data"
    )
    
    component = result["component"]
    bar_chart = component.component["BarChart"]
    assert bar_chart["data"]["path"] == "/custom/path/data"
    
    # Check data model path
    data_model = result["data_model"]
    assert data_model["path"] == "/custom/path"


def test_bar_chart_tool_registry():
    """Test tool is registered in registry"""
    registry = ComponentToolRegistry()
    tools = registry.get_tool_schemas()
    
    tool_names = [t["function"]["name"] for t in tools]
    assert "create_bar_chart" in tool_names


def test_create_bar_chart_component_helper():
    """Test bar chart component helper function"""
    component = create_bar_chart_component(
        component_id="chart-123",
        title="Sales Data",
        description="Q1 Sales",
        data_keys=["revenue", "profit"],
        colors={"revenue": "#10b981", "profit": "#3b82f6"},
        data_path="/charts/sales/data"
    )
    
    assert component.id == "chart-123"
    assert "BarChart" in component.component
    
    bar_chart = component.component["BarChart"]
    assert bar_chart["title"]["literalString"] == "Sales Data"
    assert bar_chart["description"]["literalString"] == "Q1 Sales"
    assert bar_chart["dataKeys"]["literalString"] == "revenue,profit"
    assert bar_chart["colors"]["literalMap"] == {"revenue": "#10b981", "profit": "#3b82f6"}
    assert bar_chart["data"]["path"] == "/charts/sales/data"


def test_bar_chart_with_single_data_key():
    """Test bar chart with single data series"""
    tool = BarChartTool()
    
    result = tool.generate_component(
        title="Single Series",
        data=[
            {"category": "A", "value": 100},
            {"category": "B", "value": 200}
        ],
        data_keys=["value"]
    )
    
    component = result["component"]
    bar_chart = component.component["BarChart"]
    assert bar_chart["dataKeys"]["literalString"] == "value"


def test_bar_chart_with_multiple_data_keys():
    """Test bar chart with multiple data series"""
    tool = BarChartTool()
    
    result = tool.generate_component(
        title="Multiple Series",
        data=[
            {"category": "Q1", "revenue": 50000, "profit": 15000, "expenses": 35000},
            {"category": "Q2", "revenue": 60000, "profit": 18000, "expenses": 42000}
        ],
        data_keys=["revenue", "profit", "expenses"]
    )
    
    component = result["component"]
    bar_chart = component.component["BarChart"]
    assert bar_chart["dataKeys"]["literalString"] == "revenue,profit,expenses"


def test_bar_chart_tool_get_tool():
    """Test getting bar chart tool from registry"""
    registry = ComponentToolRegistry()
    tool = registry.get_tool("create_bar_chart")
    
    assert tool is not None
    assert isinstance(tool, BarChartTool)
    assert tool.name == "create_bar_chart"
