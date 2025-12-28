# Implementation Plan: Support Basic Charts (Bar Chart)

## Overview

Add support for **Bar Chart** visualization using Shadcn UI Chart components in the A2UI protocol. This extends the existing dynamic component generation system to support data visualization, starting with a basic bar chart component.

**Related Requirements:**
- `.docs/0-requirements/022-support-basic-charts.md`
- Builds on: `.docs/0-requirements/018-support-dynamic-frontend-components.md`

**Reference:**
- Shadcn UI Charts: https://ui.shadcn.com/docs/components/chart
- A2UI Protocol: `.docs/2-knowledge-base/a2ui-implementation-summary.md`

## Architecture Decision

Follow the existing A2UI component pattern:
1. **Backend**: LLM-driven tool calling to generate chart components dynamically
2. **Protocol**: A2UI messages for chart structure + data model
3. **Frontend**: React component rendering with Shadcn UI + Recharts

## Implementation Tasks

### 1. Backend: Chart Component Tool

**File:** `backend/tools/a2ui_tools.py`

**Delegate to:** Backend Agent (See [backend.agent.md](.github/agents/backend.agent.md))

#### Task 1.1: Create BarChartTool Class

Add new tool class following the existing pattern (CheckboxTool, ButtonTool):

```python
class BarChartTool(BaseComponentTool):
    """Tool to generate bar chart components"""
    
    @property
    def name(self) -> str:
        return "create_bar_chart"
    
    @property
    def description(self) -> str:
        return """Create a bar chart visualization component. Use this when user wants:
        - Display numeric data as bar chart
        - Compare data across categories
        - Visualize trends or comparisons
        - Show statistics or metrics
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Chart title"
                },
                "description": {
                    "type": "string",
                    "description": "Chart description (optional)",
                    "default": ""
                },
                "data": {
                    "type": "array",
                    "description": "Array of data points with category and values",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            # Support multiple series (e.g., desktop, mobile)
                            "values": {"type": "object"}
                        }
                    }
                },
                "data_keys": {
                    "type": "array",
                    "description": "Keys for data series to display (e.g., ['desktop', 'mobile'])",
                    "items": {"type": "string"}
                },
                "colors": {
                    "type": "object",
                    "description": "Color mapping for each data key",
                    "default": {}
                },
                "data_path": {
                    "type": "string",
                    "description": "Path in data model to store chart data",
                    "default": None
                }
            },
            "required": ["title", "data", "data_keys"]
        }
    
    def generate_component(
        self,
        title: str,
        data: List[Dict[str, Any]],
        data_keys: List[str],
        description: str = "",
        colors: Optional[Dict[str, str]] = None,
        data_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate bar chart component structure"""
        
        # Generate unique component ID
        component_id = f"bar-chart-{uuid.uuid4().hex[:8]}"
        
        # Generate data path if not provided
        if not data_path:
            data_path = f"/ui/{component_id}/chartData"
        
        # Create bar chart component
        component = create_bar_chart_component(
            component_id=component_id,
            title=title,
            description=description,
            data_keys=data_keys,
            colors=colors or {},
            data_path=data_path
        )
        
        # Create initial data model with chart data
        path_parts = data_path.split('/')
        data_key = path_parts[-1]
        parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else "/"
        
        data_model = {
            "path": parent_path,
            "contents": [
                DataContent(
                    key=data_key,
                    value_map={
                        "data": data,
                        "dataKeys": data_keys
                    }
                )
            ]
        }
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
        }
```

#### Task 1.2: Register BarChartTool

**File:** `backend/tools/a2ui_tools.py` - Update `ComponentToolRegistry`

Add to registry initialization:

```python
class ComponentToolRegistry:
    def __init__(self):
        self.tools: Dict[str, BaseComponentTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all default component tools"""
        self.register_tool(CheckboxTool())
        self.register_tool(MultipleCheckboxesTool())
        self.register_tool(ButtonTool())
        self.register_tool(TextTool())
        self.register_tool(TextInputTool())
        self.register_tool(BarChartTool())  # Add this
```

---

### 2. Protocol: Bar Chart Message Types

**File:** `backend/protocols/a2ui_types.py`

**Delegate to:** Backend Agent

#### Task 2.1: Create Bar Chart Component Helper

Add helper function following existing pattern:

```python
def create_bar_chart_component(
    component_id: str,
    title: str,
    description: str,
    data_keys: List[str],
    colors: Dict[str, str],
    data_path: str
) -> Component:
    """
    Create A2UI bar chart component.
    
    Args:
        component_id: Unique component identifier
        title: Chart title
        description: Chart description
        data_keys: Keys for data series (e.g., ['desktop', 'mobile'])
        colors: Color mapping for each key
        data_path: Path to chart data in data model
    
    Returns:
        Component with BarChart type
    
    Example:
        component = create_bar_chart_component(
            component_id="chart-abc123",
            title="User Statistics",
            description="Monthly user counts",
            data_keys=["desktop", "mobile"],
            colors={"desktop": "#2563eb", "mobile": "#60a5fa"},
            data_path="/charts/userStats/data"
        )
    """
    return Component(
        id=component_id,
        component={
            "BarChart": {
                "title": {"literalString": title},
                "description": {"literalString": description},
                "dataKeys": {"literalString": ",".join(data_keys)},
                "colors": {"literalMap": colors},
                "data": {"path": data_path}
            }
        }
    )
```

---

### 3. Frontend: Bar Chart Component

**Delegate to:** Frontend Agent (See [frontend.agent.md](.github/agents/frontend.agent.md))

#### Task 3.1: Install Recharts Dependency

**File:** `frontend/package.json`

```bash
npm install recharts
```

Add to dependencies:
```json
{
  "dependencies": {
    "recharts": "^2.13.3"
  }
}
```

#### Task 3.2: Create A2UIBarChart Component

**File:** `frontend/components/A2UI/components/A2UIBarChart.tsx`

Create new component following A2UI pattern with Shadcn UI:

```tsx
'use client';

import React, { useMemo } from 'react';
import { Bar, BarChart, CartesianGrid, XAxis } from 'recharts';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from '@/components/ui/chart';
import type { A2UIDataModel } from '@/types/a2ui';

interface A2UIBarChartProps {
  id: string;
  props: {
    title: { literalString: string };
    description?: { literalString: string };
    dataKeys: { literalString: string }; // comma-separated: "desktop,mobile"
    colors?: { literalMap: Record<string, string> };
    data: { path: string };
  };
  dataModel: A2UIDataModel;
  surfaceId: string;
}

export const A2UIBarChart: React.FC<A2UIBarChartProps> = ({
  id,
  props,
  dataModel,
  surfaceId,
}) => {
  // Extract props
  const title = props.title?.literalString || 'Chart';
  const description = props.description?.literalString || '';
  const dataKeysString = props.dataKeys?.literalString || '';
  const dataKeys = dataKeysString.split(',').filter(Boolean);
  const colors = props.colors?.literalMap || {};
  const dataPath = props.data?.path || '';

  // Get chart data from data model
  const chartData = useMemo(() => {
    if (!dataPath || !dataModel) return [];
    
    // Navigate data model path
    const pathParts = dataPath.split('/').filter(Boolean);
    let current: any = dataModel;
    
    for (const part of pathParts) {
      current = current?.[part];
    }
    
    return current?.data || [];
  }, [dataPath, dataModel]);

  // Build chart config from data keys and colors
  const chartConfig = useMemo(() => {
    const config: ChartConfig = {};
    
    dataKeys.forEach((key) => {
      config[key] = {
        label: key.charAt(0).toUpperCase() + key.slice(1),
        color: colors[key] || `hsl(var(--chart-${dataKeys.indexOf(key) + 1}))`,
      };
    });
    
    return config;
  }, [dataKeys, colors]);

  if (!chartData || chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">No data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
          <BarChart accessibilityLayer data={chartData}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="category"
              tickLine={false}
              tickMargin={10}
              axisLine={false}
              tickFormatter={(value) => {
                // Truncate long labels
                return value.length > 10 ? value.slice(0, 10) + '...' : value;
              }}
            />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            {dataKeys.map((key) => (
              <Bar
                key={key}
                dataKey={key}
                fill={`var(--color-${key})`}
                radius={4}
              />
            ))}
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
};
```

#### Task 3.3: Update A2UIRenderer

**File:** `frontend/components/A2UI/A2UIRenderer.tsx`

Add bar chart to component mapping:

```tsx
import { A2UIBarChart } from './components/A2UIBarChart';

// Inside renderComponent switch statement:
case 'BarChart':
  return (
    <A2UIBarChart
      key={component.id}
      id={component.id}
      props={props}
      dataModel={surface.dataModel}
      surfaceId={surfaceId}
    />
  );
```

#### Task 3.4: Add Chart TypeScript Types

**File:** `frontend/types/a2ui.ts`

Add bar chart component type definition:

```typescript
export interface A2UIBarChartComponent {
  BarChart: {
    title: { literalString: string };
    description?: { literalString: string };
    dataKeys: { literalString: string };
    colors?: { literalMap: Record<string, string> };
    data: { path: string };
  };
}

// Update A2UIComponentType union
export type A2UIComponentType = 
  | A2UICheckboxComponent
  | A2UIButtonComponent
  | A2UITextComponent
  | A2UIInputComponent
  | A2UIBarChartComponent;  // Add this
```

---

### 4. Testing

**Delegate to:** Backend Agent + Frontend Agent

#### Task 4.1: Backend Tests

**File:** `backend/tests/test_bar_chart_tool.py`

Create comprehensive test suite:

```python
"""
Test suite for Bar Chart A2UI component generation
"""
import pytest
from tools.a2ui_tools import BarChartTool, ComponentToolRegistry
from protocols.a2ui_types import create_bar_chart_component

def test_bar_chart_tool_schema():
    """Test tool schema generation"""
    tool = BarChartTool()
    schema = tool.get_tool_schema()
    
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "create_bar_chart"
    assert "title" in schema["function"]["parameters"]["properties"]
    assert "data" in schema["function"]["parameters"]["properties"]

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

def test_bar_chart_tool_registry():
    """Test tool is registered in registry"""
    registry = ComponentToolRegistry()
    tools = registry.get_tool_schemas()
    
    tool_names = [t["function"]["name"] for t in tools]
    assert "create_bar_chart" in tool_names

def test_create_bar_chart_component():
    """Test bar chart component helper"""
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
    assert component.component["BarChart"]["title"]["literalString"] == "Sales Data"
```

#### Task 4.2: Integration Test

**File:** `backend/tests/test_a2ui_bar_chart_integration.py`

Test end-to-end chart generation:

```python
"""
Integration test for A2UI bar chart generation
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
    assert len(a2ui_events) >= 3
    
    # Verify bar chart component exists
    surface_updates = [e for e in a2ui_events if e.get("type") == "surfaceUpdate"]
    assert len(surface_updates) > 0
    
    components = surface_updates[0].get("components", [])
    bar_chart_components = [
        c for c in components 
        if "BarChart" in c.get("component", {})
    ]
    assert len(bar_chart_components) > 0
```

#### Task 4.3: Frontend Tests

**File:** `frontend/tests/components/A2UI/A2UIBarChart.test.tsx`

Test React component rendering:

```tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { A2UIBarChart } from '@/components/A2UI/components/A2UIBarChart';

describe('A2UIBarChart', () => {
  const mockDataModel = {
    ui: {
      'chart-123': {
        chartData: {
          data: [
            { category: 'Jan', desktop: 186, mobile: 80 },
            { category: 'Feb', desktop: 305, mobile: 200 },
          ],
          dataKeys: ['desktop', 'mobile'],
        },
      },
    },
  };

  it('renders chart with title', () => {
    render(
      <A2UIBarChart
        id="chart-123"
        props={{
          title: { literalString: 'User Stats' },
          dataKeys: { literalString: 'desktop,mobile' },
          data: { path: '/ui/chart-123/chartData' },
        }}
        dataModel={mockDataModel}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('User Stats')).toBeInTheDocument();
  });

  it('shows no data message when data is empty', () => {
    render(
      <A2UIBarChart
        id="chart-123"
        props={{
          title: { literalString: 'Empty Chart' },
          dataKeys: { literalString: 'desktop' },
          data: { path: '/invalid/path' },
        }}
        dataModel={{}}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('No data available')).toBeInTheDocument();
  });
});
```

---

### 5. Documentation

#### Task 5.1: Update Knowledge Base

**File:** `.docs/2-knowledge-base/a2ui-implementation-summary.md`

Add section documenting bar chart support:

```markdown
### Bar Chart Component

**Backend Tool:** `BarChartTool` in `backend/tools/a2ui_tools.py`
**Frontend Component:** `A2UIBarChart` in `frontend/components/A2UI/components/A2UIBarChart.tsx`

**Features:**
- LLM-driven chart generation from natural language
- Multiple data series support (e.g., desktop vs mobile)
- Customizable colors and labels
- Built with Shadcn UI + Recharts
- Responsive design with Tailwind CSS

**Example Usage:**

Agent prompt: "Create a bar chart showing Q1 sales data"

Generated A2UI message:
```json
{
  "type": "surfaceUpdate",
  "surfaceId": "surface-abc",
  "components": [{
    "id": "chart-123",
    "component": {
      "BarChart": {
        "title": {"literalString": "Q1 Sales Data"},
        "dataKeys": {"literalString": "revenue,profit"},
        "data": {"path": "/ui/chart-123/chartData"}
      }
    }
  }]
}
```

**Chart Data Format:**
```json
{
  "data": [
    {"category": "Jan", "revenue": 50000, "profit": 15000},
    {"category": "Feb", "revenue": 60000, "profit": 18000}
  ],
  "dataKeys": ["revenue", "profit"]
}
```
```

#### Task 5.2: Create Chart Component README

**File:** `backend/CHART_COMPONENTS_README.md`

Document chart component patterns for future extensions (line chart, pie chart, etc.)

---

## AG-UI Protocol Contract

### Backend → Frontend Events

**Event Flow:**
1. **surfaceUpdate**: Define bar chart component structure
2. **dataModelUpdate**: Provide chart data and configuration
3. **beginRendering**: Signal frontend to render chart

**Message Format:**

```json
{
  "type": "surfaceUpdate",
  "surfaceId": "surface-abc123",
  "components": [
    {
      "id": "bar-chart-xyz",
      "component": {
        "BarChart": {
          "title": {"literalString": "User Statistics"},
          "description": {"literalString": "Monthly active users"},
          "dataKeys": {"literalString": "desktop,mobile"},
          "colors": {
            "literalMap": {
              "desktop": "#2563eb",
              "mobile": "#60a5fa"
            }
          },
          "data": {"path": "/ui/bar-chart-xyz/chartData"}
        }
      }
    }
  ]
}
```

---

## Dependencies

### Backend
- Existing: `langchain`, `langgraph`, `pydantic`
- No new dependencies required

### Frontend
- **New:** `recharts` (^2.13.3) - Chart rendering library
- Existing: Shadcn UI, Tailwind CSS, TypeScript

---

## Testing Strategy

### Unit Tests
✅ Backend tool schema validation
✅ Component generation logic
✅ Protocol message encoding
✅ Frontend component rendering

### Integration Tests
✅ End-to-end agent → chart generation
✅ Data model updates
✅ A2UI event streaming

### Manual Testing
- [ ] Test with Ollama `qwen2.5` model
- [ ] Test with Azure OpenAI
- [ ] Test with Google Gemini
- [ ] Verify chart responsiveness
- [ ] Test with various data sizes

---

## Future Extensions

After bar chart is working, consider adding:

1. **Line Chart**: Time-series data visualization
2. **Pie Chart**: Proportional data display
3. **Area Chart**: Cumulative trends
4. **Mixed Charts**: Combining multiple chart types
5. **Interactive Features**: Click handlers, drill-downs
6. **Export Options**: Download as PNG/SVG

Reference: https://ui.shadcn.com/docs/components/chart

---

## Implementation Order

1. ✅ **Backend Tool** (Task 1.1, 1.2) - Create BarChartTool and register
2. ✅ **Protocol Types** (Task 2.1) - Add helper functions
3. ✅ **Frontend Component** (Task 3.1-3.4) - Create React component
4. ✅ **Testing** (Task 4.1-4.3) - Comprehensive test suite
5. ✅ **Documentation** (Task 5.1-5.2) - Update knowledge base

---

## Acceptance Criteria

- [ ] Backend agent can generate bar chart from natural language prompt
- [ ] Bar chart renders correctly in frontend with Shadcn UI styling
- [ ] Multiple data series supported (e.g., desktop vs mobile)
- [ ] Custom colors can be specified
- [ ] Chart is responsive and accessible
- [ ] All tests passing (backend + frontend)
- [ ] Documentation updated

---

## References

- **Shadcn UI Charts:** https://ui.shadcn.com/docs/components/chart
- **A2UI Spec:** https://a2ui.org/specification/v0.8-a2ui/
- **Recharts Docs:** https://recharts.org/
- **Existing Implementation:** `.docs/2-knowledge-base/a2ui-implementation-summary.md`
- **Backend Patterns:** [.github/agents/backend.agent.md](.github/agents/backend.agent.md)
- **Frontend Patterns:** [.github/agents/frontend.agent.md](.github/agents/frontend.agent.md)
