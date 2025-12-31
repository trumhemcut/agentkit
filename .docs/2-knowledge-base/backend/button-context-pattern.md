# Button Context Pattern - Collecting Form Data

## Problem
When you click a button, the `context` field in `userAction` is empty because the frontend doesn't know what data to collect.

## Solution
**Configure the button with `action_context` paths** that tell the frontend which data model values to collect when clicked.

---

## How It Works

### 1. Backend: Create Components with Data Model Paths

```python
# Create text input that stores value at /user/email
text_input = create_textinput_component(
    component_id="email_input",
    label_text="Email",
    value_path="/user/email"  # ← Data stored here
)

# Create button that collects that value
submit_button = create_button_component(
    component_id="submit_btn",
    label_text="Submit",
    action_name="submit_form",
    action_context={
        "email": {"path": "/user/email"},  # ← Collect from here
        "name": {"path": "/user/name"}
    }
)
```

### 2. Frontend: Automatic Data Resolution

When user clicks the button:
```typescript
// A2UIManager.handleComponentAction() automatically:
// 1. Sees action.context = { email: {path: "/user/email"}, name: {path: "/user/name"} }
// 2. Resolves paths from data model
// 3. Sends userAction with resolved values

{
  name: "submit_form",
  surfaceId: "surface-abc",
  sourceComponentId: "submit_btn",
  timestamp: "2025-12-31T...",
  context: {
    email: "user@example.com",  // ← Resolved from data model
    name: "John Doe"            // ← Resolved from data model
  }
}
```

### 3. Backend: Process Action with Context Data

```python
async def process_user_action(state: AgentState):
    user_action = state.get("user_action")
    context = user_action.get("context", {})
    
    # Now context has the data!
    email = context.get("email")  # "user@example.com"
    name = context.get("name")    # "John Doe"
    
    # Validate and process
    if email and "@" in email:
        # Success!
        return {
            **state,
            "ag_ui_events": [{
                "type": "text_message",
                "content": f"Form submitted! Email: {email}"
            }]
        }
```

---

## Using ButtonTool with Context Paths

### Old Way (Context Empty)
```python
tool = ButtonTool()
result = tool.generate_component(
    label="Submit",
    action_name="submit_form"
)
# Result: button with empty context = {}
```

### New Way (Context Populated)
```python
tool = ButtonTool()
result = tool.generate_component(
    label="Submit",
    action_name="submit_form",
    context_paths={
        "email": "/user/email",
        "name": "/user/name",
        "age": "/user/age"
    }
)
# Result: button that collects these values when clicked
```

---

## Complete Form Example

### Backend Tool Calls
```python
# Step 1: Create text inputs with data paths
email_input = create_textinput(
    label="Email Address",
    value_path="/form/email"
)

name_input = create_textinput(
    label="Full Name",
    value_path="/form/name"
)

# Step 2: Create button that references those paths
submit_button = create_button(
    label="Submit Form",
    action_name="submit_form",
    context_paths={
        "email": "/form/email",  # Collect email input value
        "name": "/form/name"      # Collect name input value
    }
)
```

### User Interaction Flow
```
1. User types "john@example.com" in email field
   → Data model updated: /form/email = "john@example.com"

2. User types "John Doe" in name field
   → Data model updated: /form/name = "John Doe"

3. User clicks "Submit Form" button
   → Frontend resolves context paths
   → Sends userAction with:
      {
        context: {
          email: "john@example.com",
          name: "John Doe"
        }
      }

4. Backend receives action with populated context
   → Can now validate and process the form data!
```

---

## LLM Agent Instructions

When creating forms with the LLM agent, instruct it like this:

**Prompt:**
```
Create a signup form with email, password, and submit button
```

**Agent Should Call:**
```python
# 1. Create email input
create_textinput(
    label="Email",
    type="email",
    value_path="/signup/email"
)

# 2. Create password input  
create_textinput(
    label="Password",
    type="password",
    value_path="/signup/password"
)

# 3. Create submit button that collects both values
create_button(
    label="Sign Up",
    action_name="submit_signup",
    context_paths={
        "email": "/signup/email",
        "password": "/signup/password"
    }
)
```

---

## Key Takeaways

✅ **Text inputs** store values at data model paths (`value_path`)  
✅ **Buttons** collect values from those paths (`context_paths`)  
✅ **Frontend** automatically resolves paths before sending action  
✅ **Backend** receives populated `context` with actual values  

❌ **Without context_paths**: `context = {}`  
✅ **With context_paths**: `context = {email: "...", name: "..."}`  

---

## Testing

Run the test to verify button context functionality:
```bash
pytest backend/tests/test_button_context.py -v
```

Expected output:
```
✓ test_button_without_context
✓ test_button_with_context_paths  
✓ test_button_with_single_context_path
```
