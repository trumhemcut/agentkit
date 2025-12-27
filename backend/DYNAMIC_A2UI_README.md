# Dynamic A2UI Component Generation - Backend Implementation

## Overview

This implementation transforms the A2UI agent to use **LLM + tool calling** for dynamic UI component generation. Instead of generating hardcoded components, the agent now analyzes user prompts and uses appropriate tools to generate components on demand.

## Architecture

```
User Prompt → A2UI Agent (LLM) → Component Tools → A2UI Protocol → Frontend
```

## Key Components

### 1. Component Generation Tools (`backend/tools/a2ui_tools.py`)

- **BaseComponentTool**: Abstract base class for all component tools
- **CheckboxTool**: Generates checkbox components
- **ComponentToolRegistry**: Manages and provides tool schemas to LLM

**Example Tool Usage:**
```python
tool = CheckboxTool()
result = tool.generate_component(
    label="I agree to terms",
    checked=False,
    data_path="/form/agreedToTerms"
)
# Returns: component, data_model, component_id
```

### 2. LLM Provider Tool Support

All LLM providers now support tool calling via `get_model_with_tools()`:

- **OllamaProvider** (`backend/llm/ollama_provider.py`)
- **AzureOpenAIProvider** (`backend/llm/azure_openai_provider.py`)
- **GeminiProvider** (`backend/llm/gemini_provider.py`)

**Example:**
```python
provider = LLMProviderFactory.get_provider("ollama", "qwen:7b")
tools = registry.get_tool_schemas()
model_with_tools = provider.get_model_with_tools(tools)
```

### 3. A2UI Agent with LLM (`backend/agents/a2ui_agent.py`)

Completely rewritten to use LLM for dynamic generation:

**Flow:**
1. User sends prompt: "Create a checkbox for agreeing to terms"
2. Agent calls LLM with tool schemas
3. LLM decides to call `create_checkbox` tool
4. Tool generates A2UI component structure
5. Agent streams A2UI messages to frontend

**Example Usage:**
```python
agent = A2UIAgent(provider="ollama", model="qwen:7b")

state = {
    "messages": [
        {"role": "user", "content": "Create a checkbox for terms agreement"}
    ],
    "thread_id": "thread-123",
    "run_id": "run-456"
}

async for event in agent.run(state):
    # Streams A2UI + AG-UI events
    print(event)
```

### 4. Tests (`backend/tests/test_a2ui_dynamic.py`)

Comprehensive test suite covering:

- ✅ Tool schema generation
- ✅ Component generation
- ✅ Tool registry management
- ✅ Agent initialization
- ✅ End-to-end generation flow (skips if model doesn't support tools)
- ✅ Error handling
- ✅ Provider tool support

## Tool Calling Format

Tools use OpenAI function calling format for compatibility:

```json
{
  "type": "function",
  "function": {
    "name": "create_checkbox",
    "description": "Create a checkbox UI component...",
    "parameters": {
      "type": "object",
      "properties": {
        "label": {"type": "string", "description": "..."},
        "checked": {"type": "boolean", "default": false}
      },
      "required": ["label"]
    }
  }
}
```

## LLM Requirements

**Models must support tool/function calling:**

✅ **Supported:**
- Azure OpenAI (gpt-4, gpt-3.5-turbo, gpt-4o)
- Google Gemini (gemini-1.5-flash, gemini-1.5-pro)
- Ollama with compatible models (qwen2.5, mistral-large, etc.)

❌ **Not Supported:**
- Ollama qwen:7b (older version without tool support)
- Models that don't support structured outputs

## Adding New Component Types

To add a new component type (e.g., Button, TextInput):

1. **Create tool class:**
```python
class ButtonTool(BaseComponentTool):
    @property
    def name(self) -> str:
        return "create_button"
    
    @property
    def description(self) -> str:
        return "Create a button UI component..."
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "variant": {"type": "string", "enum": ["primary", "secondary"]}
            },
            "required": ["label"]
        }
    
    def generate_component(self, label: str, variant: str = "primary", **kwargs):
        # Generate button component
        ...
```

2. **Register tool:**
```python
# In ComponentToolRegistry._register_default_tools()
self.register_tool(ButtonTool())
```

3. **Done!** The LLM will automatically discover and use the new tool.

## Future Enhancements

- [ ] **MCP Integration**: Replace/augment tools with Model Context Protocol
- [ ] **Multi-component generation**: Generate multiple components in one call
- [ ] **Component composition**: Nested component structures (forms, containers)
- [ ] **Validation tools**: Tools for input validation and error handling
- [ ] **State management tools**: Tools for complex data flows

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_a2ui_dynamic.py -v
```

**Note:** Some tests will skip if:
- Ollama is not running
- Selected model doesn't support tool calling

## Dependencies

- `langchain_ollama`: Ollama integration
- `langchain_openai`: Azure OpenAI integration  
- `langchain_google_genai`: Google Gemini integration
- `ag_ui`: AG-UI protocol support
- `protocols.a2ui_types`: A2UI protocol types

## Migration from Static Components

**Before (Hardcoded):**
```python
# Agent always generates same checkbox
checkbox = create_checkbox_component(...)
```

**After (Dynamic):**
```python
# Agent uses LLM to decide what to generate
component_data = await self._generate_component_with_llm(user_prompt)
```

Users can now request any supported component type naturally!
