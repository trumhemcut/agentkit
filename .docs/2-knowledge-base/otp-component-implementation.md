# OTP Input Component - Backend Implementation Summary

## Overview

Successfully implemented OTP (One-Time Password) input component support in the AgentKit A2UI system, enabling AI agents to dynamically generate verification code input interfaces.

## Implementation Date

December 29, 2025

## What Was Implemented

### 1. Protocol Helper Function

**File**: `backend/protocols/a2ui_types.py`

Added `create_otp_input_component()` helper function:

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
) -> Component
```

**Features**:
- Automatically calculates slot groups from separator positions
- Supports flexible group configurations (e.g., `[3]` for "123-456", `[2,4]` for "12-34-56")
- Returns properly formatted A2UI Component structure

**Example**:
```python
component = create_otp_input_component(
    component_id="otp-abc123",
    title="Verify Email",
    description="Enter 6-digit code",
    max_length=6,
    separator_positions=[3],
    pattern_type="digits",
    button_text="Verify",
    disabled=False,
    value_path="/ui/otp-abc123/value"
)
```

### 2. OTP Component Tool

**File**: `backend/tools/a2ui_tools.py`

Added `OTPInputTool` class following the BaseComponentTool pattern:

**Tool Properties**:
- **Name**: `create_otp_input`
- **Description**: Comprehensive description for LLM to understand when to use OTP inputs
- **Parameters**: Full JSON schema with 8 configurable properties

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| title | string | "Enter verification code" | Block title text |
| description | string | "Please enter the verification code..." | Descriptive text |
| max_length | integer | 6 | Number of OTP digits (4, 5, 6, custom) |
| separator_positions | array | None | Positions for separators |
| pattern_type | enum | "digits" | "digits" or "alphanumeric" |
| button_text | string | "Verify" | Submit button text |
| disabled | boolean | false | Disabled state |
| data_path | string | auto-generated | Data model path |

**Example Usage**:
```python
tool = OTPInputTool()
result = tool.generate_component(
    title="Two-Factor Authentication",
    max_length=6,
    separator_positions=[3]
)

# Returns:
# {
#   "component": Component(...),
#   "data_model": {...},
#   "component_id": "otp-input-abc123"
# }
```

### 3. Tool Registration

**File**: `backend/tools/a2ui_tools.py`

Updated `ComponentToolRegistry._register_default_tools()`:

```python
def _register_default_tools(self):
    self.register_tool(CheckboxTool())
    self.register_tool(MultipleCheckboxesTool())
    self.register_tool(ButtonTool())
    self.register_tool(TextInputTool())
    self.register_tool(BarChartTool())
    self.register_tool(OTPInputTool())  # ✅ NEW
```

### 4. Agent System Prompts

**Files**: 
- `backend/agents/a2ui_agent.py`
- `backend/agents/a2ui_agent_with_loop.py`

Updated system prompts to include OTP input guidance:

```python
- For OTP INPUT: use create_otp_input tool
  Examples: "create OTP verification", "6-digit code input", 
            "2FA authentication", "email verification code"
  Common lengths: 4, 5, or 6 digits
  Use separators for better UX (e.g., separator_positions=[3] for 6-digit code)
```

### 5. Test Suite

#### Unit Tests

**File**: `backend/tests/test_otp_input_tool.py`

**Coverage**: 15 tests, all passing ✅

**Test Categories**:
1. **Tool Metadata**: Name, description, parameters schema
2. **Basic Generation**: 6-digit, 4-digit OTP inputs
3. **Separator Configurations**: Single separator, multiple separators
4. **Pattern Types**: Digits-only, alphanumeric
5. **State Management**: Disabled state, custom button text
6. **Data Model**: Initialization, custom paths
7. **Uniqueness**: Unique component IDs
8. **Registry Integration**: Tool registration, schema generation

**Sample Tests**:
```python
def test_generate_6digit_otp_with_separator():
    """Test generating 6-digit OTP with separator at position 3 (123-456)"""
    result = tool.generate_component(
        max_length=6,
        separator_positions=[3]
    )
    
    assert len(otp_props["groups"]) == 2
    assert otp_props["groups"][0] == {"start": 0, "end": 3}
    assert otp_props["groups"][1] == {"start": 3, "end": 6}
```

#### Integration Tests

**File**: `backend/tests/test_a2ui_otp_integration.py`

**Coverage**: 9 integration tests

**Test Scenarios**:
- Basic OTP generation from natural language
- OTP with separator from prompt
- Email verification scenario
- Two-factor authentication scenario
- Phone verification (4-digit)
- Loop agent OTP generation
- Component structure validation
- Multiple prompt variations

**Sample Integration Test**:
```python
@pytest.mark.asyncio
async def test_a2ui_agent_generates_otp_basic():
    """Test A2UIAgent generates OTP component from natural language"""
    agent = A2UIAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Create a 6-digit verification code input"}],
        "thread_id": "test-thread-otp1",
        "run_id": "test-run-otp1"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Verify OTP component was generated
    otp_found = any('"OTPInput"' in event for event in events)
    assert otp_found
```

## Component Structure

### A2UI Message Format

```json
{
  "type": "surfaceUpdate",
  "surfaceId": "surface-123",
  "components": [
    {
      "id": "otp-input-abc123",
      "component": {
        "OTPInput": {
          "title": {"literalString": "Verify your email"},
          "description": {"literalString": "Enter the 6-digit code sent to your email."},
          "maxLength": 6,
          "groups": [
            {"start": 0, "end": 3},
            {"start": 3, "end": 6}
          ],
          "patternType": "digits",
          "buttonText": {"literalString": "Verify"},
          "disabled": false,
          "valuePath": "/ui/otp-input-abc123/value"
        }
      }
    }
  ]
}
```

### Data Model

```json
{
  "type": "dataModelUpdate",
  "path": "/ui/otp-input-abc123",
  "contents": [
    {
      "key": "value",
      "valueString": ""
    }
  ]
}
```

## Usage Examples

### Example 1: Email Verification

**User Prompt**: "Create email verification with 6-digit code"

**Agent Action**: Calls `create_otp_input` with:
- title: "Verify your email"
- max_length: 6
- pattern_type: "digits"

### Example 2: Two-Factor Authentication

**User Prompt**: "Add 2FA with 6-digit code split into two groups"

**Agent Action**: Calls `create_otp_input` with:
- title: "Two-Factor Authentication"
- max_length: 6
- separator_positions: [3]

### Example 3: Phone Verification

**User Prompt**: "Show phone verification with 4-digit code"

**Agent Action**: Calls `create_otp_input` with:
- title: "Verify your phone"
- max_length: 4
- separator_positions: [2]

## Technical Details

### Separator Logic

The component automatically calculates slot groups based on separator positions:

```python
# Input: max_length=6, separator_positions=[3]
# Output: groups = [{"start": 0, "end": 3}, {"start": 3, "end": 6}]

# Input: max_length=6, separator_positions=[2, 4]
# Output: groups = [
#   {"start": 0, "end": 2},
#   {"start": 2, "end": 4},
#   {"start": 4, "end": 6}
# ]
```

### Pattern Types

- **digits**: Only numeric input (0-9) - default
- **alphanumeric**: Letters and numbers (A-Z, 0-9)

Mapped to frontend validation patterns:
- `digits` → `REGEXP_ONLY_DIGITS`
- `alphanumeric` → `REGEXP_ONLY_DIGITS_AND_CHARS`

## Verification

### Manual Testing

Run manual test script:
```bash
cd backend
PYTHONPATH=/home/phihuynh/projects/agenkit/backend \
  .venv/bin/python tests/manual_test_otp.py
```

Output shows:
- ✅ Basic 6-digit OTP generation
- ✅ OTP with separator (123-456)
- ✅ 4-digit phone verification (12-34)
- ✅ Alphanumeric OTP

### Unit Tests

```bash
cd backend
pytest tests/test_otp_input_tool.py -v
```

**Result**: 15/15 tests passing ✅

### Integration Tests

```bash
cd backend
pytest tests/test_a2ui_otp_integration.py -v
```

**Note**: Integration tests require Ollama running with `qwen:7b` model

## Files Modified

1. ✅ `backend/protocols/a2ui_types.py` - Added `create_otp_input_component()`
2. ✅ `backend/tools/a2ui_tools.py` - Added `OTPInputTool` class and registration
3. ✅ `backend/agents/a2ui_agent.py` - Updated system prompt
4. ✅ `backend/agents/a2ui_agent_with_loop.py` - Updated system prompt

## Files Created

1. ✅ `backend/tests/test_otp_input_tool.py` - Unit tests (15 tests)
2. ✅ `backend/tests/test_a2ui_otp_integration.py` - Integration tests (9 tests)
3. ✅ `backend/tests/manual_test_otp.py` - Manual verification script

## Documentation Updated

1. ✅ `.docs/2-knowledge-base/a2ui-implementation-summary.md` - Added OTP section
2. ✅ `.docs/2-knowledge-base/otp-component-implementation.md` - This document

## Next Steps

### Frontend Implementation (Not Done Yet)

The backend is complete and ready for frontend integration. Frontend work includes:

1. **Install Shadcn UI Input OTP**: `npx shadcn@latest add input-otp`
2. **Create A2UIOTPInput Component**: React component in `frontend/components/A2UI/components/`
3. **Update A2UIRenderer**: Register OTPInput component type
4. **Update Types**: Add OTPInput types to `frontend/types/a2ui.ts`
5. **Frontend Tests**: Component tests in `frontend/tests/`

See `.docs/1-implementation-plans/023-support-otp-plan.md` for full frontend implementation guide.

## Success Criteria

### Backend ✅

- [x] OTPInputTool registered and callable
- [x] Agent generates OTP blocks from natural language
- [x] Component structure matches A2UI protocol
- [x] All unit tests passing (15/15)
- [x] Integration test structure in place
- [x] Documentation updated

### Frontend ⏳ (Pending)

- [ ] A2UIOTPInput component created
- [ ] Component registered in A2UIRenderer
- [ ] User can enter OTP digits
- [ ] Separators render correctly
- [ ] Button disabled until OTP complete
- [ ] Data model syncs with user input

## References

- Implementation Plan: `.docs/1-implementation-plans/023-support-otp-plan.md`
- Requirement: `.docs/0-requirements/023-support-otp.md`
- Shadcn UI OTP Blocks: https://ui.shadcn.com/blocks/otp
- Shadcn UI Input OTP: https://ui.shadcn.com/docs/components/input-otp
- A2UI Protocol: https://a2ui.org/specification/v0.8-a2ui/

## Notes

- OTP component follows existing A2UI patterns (Checkbox, Button, BarChart)
- Tool automatically generates unique component IDs
- Data model initialized with empty string value
- Groups array allows flexible separator configurations
- Compatible with both `a2ui_agent` and `a2ui_agent_with_loop`
- LLM can extract OTP requirements from natural language prompts
