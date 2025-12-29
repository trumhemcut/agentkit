# Implementation Plan: Support OTP Block Component

## Overview

Add support for **OTP (One-Time Password) input blocks** using Shadcn UI Input OTP components in the A2UI protocol. This extends the existing dynamic component generation system to support OTP input patterns, enabling agents to generate authentication UI components dynamically.

**Related Requirements:**
- `.docs/0-requirements/023-support-otp.md`
- Builds on: 
  - `.docs/0-requirements/017-support-a2ui-protocol.md`
  - `.docs/0-requirements/018-support-dynamic-frontend-components.md`

**Reference:**
- Shadcn UI OTP Blocks: https://ui.shadcn.com/blocks/otp
- Shadcn UI Input OTP: https://ui.shadcn.com/docs/components/input-otp
- A2UI Protocol: `.docs/2-knowledge-base/a2ui-implementation-summary.md`

## Architecture Decision

Follow the existing A2UI component pattern:
1. **Backend**: LLM-driven tool calling to generate OTP block components dynamically
2. **Protocol**: A2UI messages for OTP structure + data model
3. **Frontend**: React component rendering with Shadcn UI Input OTP components

**Key Features:**
- Support multiple OTP input lengths (4, 5, 6, or custom)
- Support separators between digit groups (e.g., `123-456` or `12-34-56`)
- Support controlled state management
- Support custom validation patterns (digits-only, alphanumeric)
- Support disabled/readonly states
- Block component includes title, description, and action button

## Implementation Tasks

---

### 1. Backend: OTP Block Component Tool

**File:** `backend/tools/a2ui_tools.py`

**Delegate to:** Backend Agent (See [.github/agents/backend.agent.md](.github/agents/backend.agent.md))

#### Task 1.1: Create OTPInputTool Class

Add new tool class following the existing pattern (CheckboxTool, ButtonTool, BarChartTool):

```python
class OTPInputTool(BaseComponentTool):
    """Tool to generate OTP input block components"""
    
    @property
    def name(self) -> str:
        return "create_otp_input"
    
    @property
    def description(self) -> str:
        return """Create an OTP (One-Time Password) input block component. Use this when user wants:
        - Verify user identity with OTP
        - Two-factor authentication input
        - Verification code entry (email, SMS, authenticator)
        - Multi-digit secure code input
        
        Examples:
        - "Create an OTP input for email verification"
        - "Add 6-digit code verification"
        - "Show 2FA authentication form"
        - "Create verification code input with 4 digits"
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title text for the OTP block (e.g., 'Verify your email')",
                    "default": "Enter verification code"
                },
                "description": {
                    "type": "string",
                    "description": "Descriptive text explaining the OTP purpose",
                    "default": "Please enter the verification code sent to your device."
                },
                "max_length": {
                    "type": "integer",
                    "description": "Number of OTP digits/characters (common: 4, 5, 6)",
                    "default": 6
                },
                "separator_positions": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Positions to insert separators (e.g., [3] for '123-456', [2, 4] for '12-34-56')",
                    "default": None
                },
                "pattern_type": {
                    "type": "string",
                    "enum": ["digits", "alphanumeric"],
                    "description": "Input pattern validation: 'digits' (numbers only) or 'alphanumeric' (letters + numbers)",
                    "default": "digits"
                },
                "button_text": {
                    "type": "string",
                    "description": "Submit button text",
                    "default": "Verify"
                },
                "disabled": {
                    "type": "boolean",
                    "description": "Whether the input is disabled",
                    "default": False
                },
                "data_path": {
                    "type": "string",
                    "description": "Path in data model to store OTP value",
                    "default": None
                }
            },
            "required": []
        }
    
    def generate_component(
        self,
        title: str = "Enter verification code",
        description: str = "Please enter the verification code sent to your device.",
        max_length: int = 6,
        separator_positions: Optional[List[int]] = None,
        pattern_type: str = "digits",
        button_text: str = "Verify",
        disabled: bool = False,
        data_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate OTP input block component structure"""
        
        # Generate unique component ID
        component_id = f"otp-input-{uuid.uuid4().hex[:8]}"
        
        # Generate data path if not provided
        if not data_path:
            data_path = f"/ui/{component_id}/value"
        
        # Create OTP input component
        component = create_otp_input_component(
            component_id=component_id,
            title=title,
            description=description,
            max_length=max_length,
            separator_positions=separator_positions,
            pattern_type=pattern_type,
            button_text=button_text,
            disabled=disabled,
            value_path=data_path
        )
        
        # Create initial data model
        path_parts = data_path.split('/')
        data_key = path_parts[-1]
        parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else "/"
        
        data_model = {
            "path": parent_path,
            "contents": [
                DataContent(
                    key=data_key,
                    value_string=""  # Initial empty OTP value
                )
            ]
        }
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
        }
```

#### Task 1.2: Add create_otp_input_component Helper

**File:** `backend/protocols/a2ui_types.py`

Add helper function to create OTP component structure:

```python
def create_otp_input_component(
    component_id: str,
    title: str,
    description: str,
    max_length: int,
    separator_positions: Optional[List[int]],
    pattern_type: str,
    button_text: str,
    disabled: bool,
    value_path: str
) -> Component:
    """
    Create an OTP input block component structure
    
    Args:
        component_id: Unique identifier for component
        title: Block title text
        description: Block description text
        max_length: Number of OTP digits
        separator_positions: List of positions to insert separators
        pattern_type: 'digits' or 'alphanumeric'
        button_text: Submit button text
        disabled: Whether input is disabled
        value_path: Data model path for OTP value
    
    Returns:
        Component with OTP block structure
    """
    
    # Calculate slot groups based on separator positions
    groups = []
    if separator_positions:
        positions = sorted(separator_positions)
        start = 0
        for pos in positions:
            groups.append({"start": start, "end": pos})
            start = pos
        groups.append({"start": start, "end": max_length})
    else:
        # Single group with all slots
        groups.append({"start": 0, "end": max_length})
    
    return Component(
        id=component_id,
        type="OTPInput",
        properties={
            "title": title,
            "description": description,
            "maxLength": max_length,
            "groups": groups,
            "patternType": pattern_type,
            "buttonText": button_text,
            "disabled": disabled,
            "valuePath": value_path
        }
    )
```

#### Task 1.3: Register OTPInputTool

Update tool registry in `backend/tools/a2ui_tools.py`:

```python
# In ComponentToolRegistry class
def _initialize_tools(self):
    """Initialize all available tools"""
    self._tools = {
        "checkbox": CheckboxTool(),
        "checkboxes": MultipleCheckboxesTool(),
        "button": ButtonTool(),
        "text_input": TextInputTool(),
        "bar_chart": BarChartTool(),
        "otp_input": OTPInputTool(),  # NEW
    }
```

#### Task 1.4: Update A2UI Agents

**Files:**
- `backend/agents/a2ui_agent.py`
- `backend/agents/a2ui_agent_with_loop.py`

Both agents should automatically include the new OTP tool via the registry:

```python
# No code changes needed - tools are auto-loaded from registry
# But verify system prompts mention OTP verification use cases:

SYSTEM_PROMPT = """
You are a UI component generation assistant...

Available components:
- Checkbox: For agreements, toggles
- Button: For actions, CTAs
- Text Input: For user text input
- Bar Chart: For data visualization
- OTP Input: For verification codes, 2FA authentication  # NEW

...
"""
```

#### Task 1.5: Testing

**New Test File:** `backend/tests/test_otp_input_tool.py`

Test cases:
- ✅ Generate basic 6-digit OTP input
- ✅ Generate 4-digit OTP with separator at position 2 (`12-34`)
- ✅ Generate 6-digit OTP with separator at position 3 (`123-456`)
- ✅ Generate alphanumeric OTP (6 chars)
- ✅ Generate disabled OTP input
- ✅ Verify component structure matches A2UI protocol
- ✅ Verify data model initialization
- ✅ Verify tool is registered in registry
- ✅ Integration test with A2UI agent

**Test File:** `backend/tests/test_a2ui_otp_integration.py`

Integration test for end-to-end OTP generation through agent:

```python
import pytest
from agents.a2ui_agent import A2UIAgent
from graphs.a2ui_graph import A2UIGraph

@pytest.mark.asyncio
async def test_agent_generates_otp_from_prompt():
    """Test agent can generate OTP component from natural language"""
    agent = A2UIAgent()
    graph = A2UIGraph()
    
    prompts = [
        "Create a 6-digit verification code input",
        "Add 2FA authentication with OTP",
        "Show email verification form",
    ]
    
    for prompt in prompts:
        result = await graph.ainvoke({
            "messages": [{"role": "user", "content": prompt}]
        })
        
        # Verify OTP component was generated
        assert "surface_update" in result
        component = result["surface_update"]["component"]
        assert component["type"] == "OTPInput"
        assert "maxLength" in component["properties"]
```

---

### 2. Protocol: A2UI Message Contract

**No protocol changes needed** - OTP uses existing A2UI message types:
- `SurfaceUpdate` for component definition
- `DataModelUpdate` for OTP value state
- `BeginRendering` for rendering trigger

**Component Schema:**

```typescript
// A2UI Component Structure for OTP Input
{
  "id": "otp-input-a1b2c3d4",
  "type": "OTPInput",
  "properties": {
    "title": "Verify your email",
    "description": "Please enter the 6-digit code sent to your email.",
    "maxLength": 6,
    "groups": [
      {"start": 0, "end": 3},  // First group: slots 0-2
      {"start": 3, "end": 6}   // Second group: slots 3-5
    ],
    "patternType": "digits",
    "buttonText": "Verify",
    "disabled": false,
    "valuePath": "/ui/otp-input-a1b2c3d4/value"
  }
}
```

**Data Model Schema:**

```typescript
// A2UI Data Model for OTP value
{
  "path": "/ui/otp-input-a1b2c3d4",
  "contents": [
    {
      "key": "value",
      "value_string": "123456"  // User-entered OTP
    }
  ]
}
```

---

### 3. Frontend: OTP Block Component

**Delegate to:** Frontend Agent (See [.github/agents/frontend.agent.md](.github/agents/frontend.agent.md))

#### Task 3.1: Install Shadcn UI Input OTP

**Terminal Command:**
```bash
cd frontend
npx shadcn@latest add input-otp
```

This installs:
- `components/ui/input-otp.tsx` - InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator

#### Task 3.2: Create A2UIOTPInput Component

**New File:** `frontend/components/A2UI/components/A2UIOTPInput.tsx`

```typescript
"use client"

import React, { useState, useEffect } from "react"
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
  InputOTPSeparator,
} from "@/components/ui/input-otp"
import { Button } from "@/components/ui/button"
import { REGEXP_ONLY_DIGITS_AND_CHARS, REGEXP_ONLY_DIGITS } from "input-otp"

interface A2UIOTPInputProps {
  component: {
    id: string
    type: "OTPInput"
    properties: {
      title: string
      description: string
      maxLength: number
      groups: Array<{ start: number; end: number }>
      patternType: "digits" | "alphanumeric"
      buttonText: string
      disabled: boolean
      valuePath: string
    }
  }
  dataModel: Record<string, any>
  onUpdate: (path: string, value: any) => void
}

export function A2UIOTPInput({
  component,
  dataModel,
  onUpdate,
}: A2UIOTPInputProps) {
  const { properties } = component
  const [otpValue, setOtpValue] = useState("")
  
  // Extract current value from data model
  useEffect(() => {
    const pathParts = properties.valuePath.split("/")
    const key = pathParts[pathParts.length - 1]
    const currentValue = dataModel[key]
    if (currentValue && currentValue !== otpValue) {
      setOtpValue(currentValue)
    }
  }, [dataModel, properties.valuePath])
  
  const handleChange = (value: string) => {
    setOtpValue(value)
    onUpdate(properties.valuePath, value)
  }
  
  const handleSubmit = () => {
    // Trigger verification action
    console.log("OTP submitted:", otpValue)
    // Could emit custom event for backend handling
  }
  
  // Select pattern based on type
  const pattern =
    properties.patternType === "alphanumeric"
      ? REGEXP_ONLY_DIGITS_AND_CHARS
      : REGEXP_ONLY_DIGITS
  
  // Render slot groups with separators
  const renderGroups = () => {
    return properties.groups.map((group, groupIndex) => {
      const slots = []
      for (let i = group.start; i < group.end; i++) {
        slots.push(<InputOTPSlot key={i} index={i} />)
      }
      
      return (
        <React.Fragment key={groupIndex}>
          <InputOTPGroup>{slots}</InputOTPGroup>
          {groupIndex < properties.groups.length - 1 && <InputOTPSeparator />}
        </React.Fragment>
      )
    })
  }
  
  return (
    <div className="flex flex-col items-center space-y-6 p-8 border rounded-lg bg-card">
      {/* Title */}
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-semibold">{properties.title}</h3>
        <p className="text-sm text-muted-foreground max-w-md">
          {properties.description}
        </p>
      </div>
      
      {/* OTP Input */}
      <InputOTP
        maxLength={properties.maxLength}
        value={otpValue}
        onChange={handleChange}
        pattern={pattern}
        disabled={properties.disabled}
      >
        {renderGroups()}
      </InputOTP>
      
      {/* Value Display */}
      <div className="text-center text-sm text-muted-foreground">
        {otpValue === "" ? (
          <>Enter your verification code</>
        ) : (
          <>
            Entered: <span className="font-mono font-semibold">{otpValue}</span>
          </>
        )}
      </div>
      
      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={properties.disabled || otpValue.length < properties.maxLength}
        className="w-full max-w-xs"
      >
        {properties.buttonText}
      </Button>
    </div>
  )
}
```

#### Task 3.3: Register Component in A2UI Renderer

**File:** `frontend/components/A2UI/A2UIRenderer.tsx`

Update component registry to include OTPInput:

```typescript
import { A2UIOTPInput } from "./components/A2UIOTPInput"

// In component map
const componentMap: Record<string, React.ComponentType<any>> = {
  Text: A2UIText,
  Checkbox: A2UICheckbox,
  Button: A2UIButton,
  TextInput: A2UITextInput,
  BarChart: A2UIBarChart,
  OTPInput: A2UIOTPInput,  // NEW
}

// In renderComponent function
function renderComponent(component: A2UIComponent) {
  const ComponentType = componentMap[component.type]
  
  if (!ComponentType) {
    console.warn(`Unknown A2UI component type: ${component.type}`)
    return null
  }
  
  return (
    <ComponentType
      key={component.id}
      component={component}
      dataModel={dataModel}
      onUpdate={handleDataUpdate}
    />
  )
}
```

#### Task 3.4: Update A2UI Types

**File:** `frontend/types/a2ui.ts`

Add OTPInput component type:

```typescript
export type A2UIComponentType = 
  | "Text" 
  | "Checkbox" 
  | "Button" 
  | "TextInput" 
  | "BarChart"
  | "OTPInput"  // NEW

export interface OTPInputComponent extends BaseA2UIComponent {
  type: "OTPInput"
  properties: {
    title: string
    description: string
    maxLength: number
    groups: Array<{ start: number; end: number }>
    patternType: "digits" | "alphanumeric"
    buttonText: string
    disabled: boolean
    valuePath: string
  }
}
```

#### Task 3.5: Frontend Testing

**New Test File:** `frontend/tests/components/A2UI/A2UIOTPInput.test.tsx`

Test cases:
- ✅ Renders OTP input with correct number of slots
- ✅ Renders title and description
- ✅ Handles user input (controlled state)
- ✅ Renders separators at correct positions
- ✅ Validates input pattern (digits vs alphanumeric)
- ✅ Disables button when OTP incomplete
- ✅ Handles disabled state
- ✅ Updates data model on change
- ✅ Submits OTP on button click

```typescript
import { render, screen, fireEvent } from "@testing-library/react"
import { A2UIOTPInput } from "@/components/A2UI/components/A2UIOTPInput"

describe("A2UIOTPInput", () => {
  const mockComponent = {
    id: "otp-test",
    type: "OTPInput" as const,
    properties: {
      title: "Verify Email",
      description: "Enter 6-digit code",
      maxLength: 6,
      groups: [
        { start: 0, end: 3 },
        { start: 3, end: 6 },
      ],
      patternType: "digits" as const,
      buttonText: "Verify",
      disabled: false,
      valuePath: "/ui/otp-test/value",
    },
  }
  
  const mockDataModel = { value: "" }
  const mockOnUpdate = jest.fn()
  
  it("renders OTP input with correct title", () => {
    render(
      <A2UIOTPInput
        component={mockComponent}
        dataModel={mockDataModel}
        onUpdate={mockOnUpdate}
      />
    )
    
    expect(screen.getByText("Verify Email")).toBeInTheDocument()
  })
  
  it("renders correct number of input slots", () => {
    render(
      <A2UIOTPInput
        component={mockComponent}
        dataModel={mockDataModel}
        onUpdate={mockOnUpdate}
      />
    )
    
    const slots = screen.getAllByRole("textbox")
    expect(slots).toHaveLength(6)
  })
  
  it("calls onUpdate when OTP value changes", () => {
    render(
      <A2UIOTPInput
        component={mockComponent}
        dataModel={mockDataModel}
        onUpdate={mockOnUpdate}
      />
    )
    
    // Simulate user typing (implementation depends on InputOTP internals)
    // This is a conceptual test - actual implementation may vary
    const firstSlot = screen.getAllByRole("textbox")[0]
    fireEvent.change(firstSlot, { target: { value: "1" } })
    
    expect(mockOnUpdate).toHaveBeenCalled()
  })
  
  it("disables button when OTP is incomplete", () => {
    render(
      <A2UIOTPInput
        component={mockComponent}
        dataModel={{ value: "123" }}  // Incomplete
        onUpdate={mockOnUpdate}
      />
    )
    
    const button = screen.getByText("Verify")
    expect(button).toBeDisabled()
  })
})
```

---

## Integration Points

### Backend → Frontend
1. Agent receives user request for OTP verification
2. Agent calls `create_otp_input` tool with parameters
3. Tool generates A2UI `SurfaceUpdate` + `DataModelUpdate`
4. Messages sent via SSE to frontend
5. Frontend A2UIRenderer renders `A2UIOTPInput` component

### User Interaction Flow
1. User types OTP digits in input slots
2. Each keystroke updates local state
3. Component calls `onUpdate()` to sync with data model
4. When complete, user clicks "Verify" button
5. (Optional) Backend webhook/handler validates OTP

---

## Testing Strategy

### Backend Tests
- **Unit Tests**: OTPInputTool component generation
- **Integration Tests**: A2UI agent generates OTP from prompts
- **Protocol Tests**: OTP component structure validates against A2UI spec

### Frontend Tests
- **Unit Tests**: A2UIOTPInput rendering and state
- **Integration Tests**: Full A2UI pipeline (backend → SSE → frontend)
- **Visual Tests**: OTP blocks match Shadcn UI design

### End-to-End Tests
- User requests "Add email verification"
- Agent generates OTP input block
- Component renders with 6 slots
- User enters code
- Data model updates correctly

---

## Example Usage Scenarios

### Scenario 1: Email Verification
**User Prompt:**
> "Create email verification with 6-digit code"

**Agent Response:**
```json
{
  "surface_update": {
    "component": {
      "id": "otp-a1b2c3",
      "type": "OTPInput",
      "properties": {
        "title": "Verify your email",
        "description": "Enter the 6-digit code sent to your email",
        "maxLength": 6,
        "groups": [{"start": 0, "end": 6}],
        "patternType": "digits",
        "buttonText": "Verify Email",
        "disabled": false,
        "valuePath": "/ui/otp-a1b2c3/value"
      }
    }
  }
}
```

### Scenario 2: Two-Factor Authentication
**User Prompt:**
> "Add 2FA with 6-digit code split into two groups"

**Agent Response:**
```json
{
  "surface_update": {
    "component": {
      "id": "otp-2fa-x9y8",
      "type": "OTPInput",
      "properties": {
        "title": "Two-Factor Authentication",
        "description": "Enter the code from your authenticator app",
        "maxLength": 6,
        "groups": [
          {"start": 0, "end": 3},
          {"start": 3, "end": 6}
        ],
        "patternType": "digits",
        "buttonText": "Verify",
        "disabled": false,
        "valuePath": "/auth/2fa/code"
      }
    }
  }
}
```

### Scenario 3: Phone Verification
**User Prompt:**
> "Show phone verification with 4-digit code"

**Agent Response:**
```json
{
  "surface_update": {
    "component": {
      "id": "otp-phone-p5q6",
      "type": "OTPInput",
      "properties": {
        "title": "Verify your phone",
        "description": "Enter the 4-digit code sent via SMS",
        "maxLength": 4,
        "groups": [
          {"start": 0, "end": 2},
          {"start": 2, "end": 4}
        ],
        "patternType": "digits",
        "buttonText": "Verify Phone",
        "disabled": false,
        "valuePath": "/phone/verification/code"
      }
    }
  }
}
```

---

## Dependencies

### Backend
- ✅ Existing: `backend/protocols/a2ui_types.py`
- ✅ Existing: `backend/tools/a2ui_tools.py`
- ✅ Existing: `backend/agents/a2ui_agent.py`
- ✅ Existing: `backend/agents/a2ui_agent_with_loop.py`

### Frontend
- ⚠️ **New**: Install `input-otp` package via Shadcn CLI
- ✅ Existing: `frontend/components/A2UI/A2UIRenderer.tsx`
- ✅ Existing: `frontend/types/a2ui.ts`

---

## Success Criteria

### Backend
- ✅ OTPInputTool registered and callable
- ✅ Agent generates OTP blocks from natural language
- ✅ Component structure matches A2UI protocol
- ✅ All tests passing (unit + integration)

### Frontend
- ✅ A2UIOTPInput component renders correctly
- ✅ User can enter OTP digits
- ✅ Separators appear at correct positions
- ✅ Button disabled until OTP complete
- ✅ Data model syncs with user input
- ✅ Matches Shadcn UI design patterns

### Integration
- ✅ End-to-end flow works: user prompt → agent → component → render
- ✅ Multiple OTP blocks can coexist
- ✅ Works with both a2ui_agent and a2ui_agent_with_loop

---

## Future Enhancements

1. **Validation Callbacks**: Add backend webhook for OTP verification
2. **Error States**: Show error messages for invalid codes
3. **Resend Functionality**: Add "Resend code" button
4. **Timer Display**: Show countdown for code expiration
5. **Auto-Submit**: Submit automatically when all slots filled
6. **Paste Support**: Handle pasting full OTP code
7. **Custom Styling**: Theme customization (colors, borders)

---

## Related Documentation

After implementation, update:
- `.docs/2-knowledge-base/a2ui-implementation-summary.md` - Add OTP component section
- `.docs/2-knowledge-base/backend/tools/a2ui-tools.md` - Document OTPInputTool
- `.docs/2-knowledge-base/frontend/components/a2ui-components.md` - Document A2UIOTPInput

---

## Notes

- OTP blocks follow Shadcn UI design patterns: https://ui.shadcn.com/blocks/otp
- Input validation uses `input-otp` library patterns (`REGEXP_ONLY_DIGITS`, `REGEXP_ONLY_DIGITS_AND_CHARS`)
- Component is fully controlled - state managed via data model
- Separator positions calculated from groups array for flexibility
- Button disabled state ensures UX best practices (no partial submissions)
