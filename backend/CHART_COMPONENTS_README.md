# Chart Components in A2UI

## Overview

This document describes the chart component patterns in the AgentKit A2UI system. Chart components enable LLM agents to generate data visualizations from natural language prompts.

## Architecture

Chart components follow the standard A2UI component pattern:

1. **Backend Tool**: LLM-callable tool for generating chart structure
2. **Protocol Message**: A2UI message encoding (surfaceUpdate + dataModelUpdate)
3. **Frontend Component**: React component that renders the chart

## Currently Supported Charts

### Bar Chart

**Tool**: `BarChartTool` (`backend/tools/a2ui_tools.py`)  
**Use Cases**:
- Comparing data across categories
- Visualizing trends and comparisons
- Displaying statistics or metrics
- Multi-series data (e.g., desktop vs mobile)

**Component Structure**:
```json
{
  "id": "bar-chart-xyz",
  "component": {
    "BarChart": {
      "title": {"literalString": "Chart Title"},
      "description": {"literalString": "Chart Description"},
      "dataKeys": {"literalString": "series1,series2"},
      "colors": {"literalMap": {"series1": "#color1", "series2": "#color2"}},
      "data": {"path": "/ui/bar-chart-xyz/chartData"}
    }
  }
}
```

**Data Format**:
```python
{
  "data": [
    {"category": "Category A", "series1": 100, "series2": 80},
    {"category": "Category B", "series1": 150, "series2": 120}
  ],
  "dataKeys": ["series1", "series2"]
}
```

**Example**:
```python
from tools.a2ui_tools import BarChartTool

tool = BarChartTool()
result = tool.generate_component(
    title="Monthly Sales",
    description="Revenue vs Profit",
    data=[
        {"category": "Jan", "revenue": 50000, "profit": 15000},
        {"category": "Feb", "revenue": 60000, "profit": 18000},
        {"category": "Mar", "revenue": 55000, "profit": 16500}
    ],
    data_keys=["revenue", "profit"],
    colors={"revenue": "#10b981", "profit": "#3b82f6"}
)
```

## Creating New Chart Types

To add a new chart type (e.g., Line Chart, Pie Chart), follow this pattern:

### 1. Create Chart Tool

Create a new tool class in `backend/tools/a2ui_tools.py`:

```python
class LineChartTool(BaseComponentTool):
    @property
    def name(self) -> str:
        return "create_line_chart"
    
    @property
    def description(self) -> str:
        return """Create a line chart visualization. Use for:
        - Time-series data
        - Trend visualization
        - Continuous data over time
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "data": {"type": "array"},
                "data_keys": {"type": "array"},
                # Add chart-specific parameters
            },
            "required": ["title", "data", "data_keys"]
        }
    
    def generate_component(self, **kwargs) -> Dict[str, Any]:
        # Generate component ID
        component_id = f"line-chart-{uuid.uuid4().hex[:8]}"
        
        # Create component using helper
        component = create_line_chart_component(...)
        
        # Create data model
        data_model = {...}
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
        }
```

### 2. Add Protocol Helper

Add a helper function in `backend/protocols/a2ui_types.py`:

```python
def create_line_chart_component(
    component_id: str,
    title: str,
    # ... other parameters
) -> Component:
    """Create a line chart component."""
    return Component(
        id=component_id,
        component={
            "LineChart": {
                "title": {"literalString": title},
                # ... other properties
            }
        }
    )
```

### 3. Register Tool

Register the tool in `ComponentToolRegistry._register_default_tools()`:

```python
def _register_default_tools(self):
    self.register_tool(CheckboxTool())
    self.register_tool(BarChartTool())
    self.register_tool(LineChartTool())  # Add new tool
```

### 4. Add Tests

Create test file `tests/test_line_chart_tool.py`:

```python
def test_line_chart_tool_schema():
    """Test tool schema generation"""
    tool = LineChartTool()
    assert tool.name == "create_line_chart"
    # ... more tests

def test_line_chart_component_generation():
    """Test component generation"""
    tool = LineChartTool()
    result = tool.generate_component(...)
    assert "component" in result
    assert "data_model" in result
```

### 5. Update Frontend

Add React component in `frontend/components/A2UI/components/`:

```tsx
export const A2UILineChart: React.FC<A2UILineChartProps> = ({
  id, props, dataModel, surfaceId
}) => {
  // Render line chart using Shadcn UI + Recharts
};
```

Update renderer in `frontend/components/A2UI/A2UIRenderer.tsx`:

```tsx
case 'LineChart':
  return <A2UILineChart ... />;
```

## Chart Data Model Pattern

All charts follow this data model pattern:

```python
{
  "path": "/ui/{component_id}",
  "contents": [
    {
      "key": "chartData",
      "valueMap": {
        "data": [...],         # Array of data points
        "dataKeys": [...]      # Array of series keys
      }
    }
  ]
}
```

This ensures:
- Consistent data access pattern
- Type safety with Pydantic validation
- Easy data updates from backend

## LLM Integration

Charts are automatically available to LLM agents through tool schemas:

```python
from tools.a2ui_tools import ComponentToolRegistry

registry = ComponentToolRegistry()
tool_schemas = registry.get_tool_schemas()
# Pass to LLM provider as available tools
```

The LLM can then call chart tools based on user prompts:
- "Show me a bar chart of sales data"
- "Create a line chart for monthly trends"
- "Visualize the comparison as a bar chart"

## Best Practices

1. **Data Validation**: Always validate data format in tool
2. **Unique IDs**: Use UUID for component IDs to avoid conflicts
3. **Color Schemes**: Provide default colors but allow customization
4. **Responsive Design**: Charts should adapt to container size
5. **Accessibility**: Include proper labels and descriptions
6. **Error Handling**: Gracefully handle missing or invalid data

## Testing Strategy

For each chart type, test:

1. **Tool Schema**: Parameter validation
2. **Component Generation**: Correct structure
3. **Data Model**: Proper initialization
4. **Registry**: Tool registration
5. **Integration**: End-to-end agent flow

## Frontend Integration

Charts use:
- **Shadcn UI Chart Components**: https://ui.shadcn.com/docs/components/chart
- **Recharts**: Underlying chart library
- **Tailwind CSS**: Styling and responsive design

## Future Chart Types

Consider adding:

1. **Line Chart**: Time-series and trends
2. **Pie Chart**: Proportional data
3. **Area Chart**: Cumulative trends
4. **Scatter Plot**: Correlation data
5. **Mixed Chart**: Multiple chart types combined
6. **Heatmap**: Matrix data visualization

## References

- **A2UI Protocol**: `.docs/2-knowledge-base/a2ui-implementation-summary.md`
- **Shadcn Charts**: https://ui.shadcn.com/docs/components/chart
- **Recharts Docs**: https://recharts.org/
- **Implementation Plan**: `.docs/1-implementation-plans/022-support-basic-charts-plan.md`

## Related Files

- `backend/tools/a2ui_tools.py` - Chart tool implementations
- `backend/protocols/a2ui_types.py` - Protocol message helpers
- `backend/tests/test_bar_chart_tool.py` - Chart tool tests
- `backend/tests/test_a2ui_bar_chart_integration.py` - Integration tests
