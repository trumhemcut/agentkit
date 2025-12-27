# Implementation Plan: Support Dynamic Frontend Components

**Requirement**: [018-support-dynamic-frontend-components.md](../0-requirements/018-support-dynamic-frontend-components.md)  
**Created**: December 27, 2025  
**Status**: Planning  
**Dependencies**: [017-support-a2ui-protocol-plan.md](017-support-a2ui-protocol-plan.md)

## Executive Summary

This plan transforms the A2UI agent from generating static checkboxes to **dynamically generating frontend components** based on user prompts using LLM-powered tool calling. The agent will use tools (future MCP integration) to create UI components on demand.

**Current State**: A2UI agent generates hardcoded checkbox components  
**Target State**: A2UI agent dynamically generates components based on user intent using LLM + tools

**Key Changes**:
- Add LLM integration to A2UI agent for understanding user UI requests
- Create component generation tools (checkbox tool as starting point)
- Use structured output/tool calling to generate A2UI JSON
- Extensible architecture for future component types

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                          USER REQUEST                            │
│         "Create a checkbox to agree to terms"                    │
└───────────────────┬──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                    A2UI AGENT (with LLM)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. LLM analyzes user intent                               │ │
│  │  2. LLM decides which component tool to call               │ │
│  │  3. Tool generates A2UI component JSON                     │ │
│  │  4. Agent streams A2UI messages + AG-UI events             │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────┬──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                     COMPONENT TOOLS                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Checkbox     │  │ Button       │  │ Form         │          │
│  │ Tool         │  │ Tool         │  │ Tool         │  ...     │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                  │
│                            │                                     │
│                  Returns A2UI JSON                              │
└───────────────────┬──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                    A2UI PROTOCOL                                 │
│  • surfaceUpdate: Component tree                                │
│  • dataModelUpdate: Initial state                               │
│  • beginRendering: Trigger render                               │
└───────────────────┬──────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                              │
│  • Parse A2UI messages                                           │
│  • Render native Shadcn UI components                           │
│  • Handle user interactions                                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Backend - LLM-Powered Component Generation

**Owner**: Backend Agent (see [backend.agent.md](../../.github/agents/backend.agent.md))

### 1.1 Create Component Generation Tools

These tools are callable by the LLM to generate A2UI component structures.

#### File: `backend/tools/a2ui_tools.py` (NEW)

Create base tool class and checkbox tool:

```python
"""
A2UI Component Generation Tools

These tools are used by LLM agents to generate A2UI protocol messages
for creating dynamic frontend components.

Future: These will be replaced/augmented with MCP (Model Context Protocol) tools.
"""

import uuid
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from protocols.a2ui_types import (
    Component,
    SurfaceUpdate,
    DataModelUpdate,
    BeginRendering,
    DataContent,
    create_checkbox_component,
    create_text_component,
    create_button_component
)


class BaseComponentTool(ABC):
    """Base class for A2UI component generation tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for LLM to call"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description for LLM to understand tool purpose"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON schema for tool parameters"""
        pass
    
    @abstractmethod
    def generate_component(self, **kwargs) -> Dict[str, Any]:
        """
        Generate A2UI component structure
        
        Returns:
            Dict with:
            - component: Component object
            - data_model: Initial data model for component
            - component_id: ID of the generated component
        """
        pass


class CheckboxTool(BaseComponentTool):
    """Tool to generate checkbox components"""
    
    @property
    def name(self) -> str:
        return "create_checkbox"
    
    @property
    def description(self) -> str:
        return """Create a checkbox UI component. Use this when user wants:
        - A checkbox for agreement/confirmation
        - A toggleable option
        - A boolean selection control
        """
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Text label for the checkbox"
                },
                "checked": {
                    "type": "boolean",
                    "description": "Initial checked state",
                    "default": False
                },
                "data_path": {
                    "type": "string",
                    "description": "Path in data model to store value (e.g., '/form/agreedToTerms')",
                    "default": None
                }
            },
            "required": ["label"]
        }
    
    def generate_component(
        self,
        label: str,
        checked: bool = False,
        data_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate checkbox component structure"""
        
        # Generate unique component ID
        component_id = f"checkbox-{uuid.uuid4().hex[:8]}"
        
        # Generate data path if not provided
        if not data_path:
            data_path = f"/ui/{component_id}/value"
        
        # Create checkbox component
        component = create_checkbox_component(
            component_id=component_id,
            label_text=label,
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
                    value_boolean=checked
                )
            ]
        }
        
        return {
            "component": component,
            "data_model": data_model,
            "component_id": component_id
        }


class ComponentToolRegistry:
    """Registry for all A2UI component tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseComponentTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default component tools"""
        self.register_tool(CheckboxTool())
    
    def register_tool(self, tool: BaseComponentTool):
        """Register a component tool"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseComponentTool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[BaseComponentTool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get tool schemas in OpenAI function calling format
        
        Returns:
            List of tool schemas for LLM provider
        """
        schemas = []
        for tool in self.tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return schemas
```

**Key Points**:
- Extensible architecture: Easy to add new component types
- Tool calling pattern: Compatible with OpenAI/Anthropic/Ollama function calling
- Future MCP integration: Structure designed to migrate to MCP later
- Returns both component and data model for complete A2UI setup

**Dependencies**: 
- `protocols/a2ui_types.py` (existing)

---

### 1.2 Update A2UI Agent with LLM Integration

#### File: `backend/agents/a2ui_agent.py` (MODIFY)

Transform the agent to use LLM + tools for dynamic generation:

```python
"""
A2UI Agent - Dynamic UI Component Generation (LLM-Powered)

This agent uses LLM + tool calling to dynamically generate UI components
based on user prompts.
"""

import uuid
import logging
import json
from typing import AsyncGenerator, List, Dict, Any
from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    RunStartedEvent,
    RunFinishedEvent,
)
from ag_ui.encoder import EventEncoder
from agents.base_agent import BaseAgent, AgentState
from protocols.a2ui_types import (
    SurfaceUpdate,
    DataModelUpdate,
    BeginRendering,
    Component,
)
from protocols.a2ui_encoder import A2UIEncoder
from llm.provider_factory import LLMProviderFactory
from tools.a2ui_tools import ComponentToolRegistry

logger = logging.getLogger(__name__)


class A2UIAgent(BaseAgent):
    """
    Agent that dynamically generates A2UI UI components using LLM + tools.
    
    Flow:
    1. User sends prompt: "Create a checkbox for terms agreement"
    2. LLM analyzes intent and calls appropriate tool (e.g., create_checkbox)
    3. Tool returns A2UI component structure
    4. Agent streams A2UI messages to frontend
    5. Frontend renders native UI component
    """
    
    def __init__(self, provider: str = "ollama", model: str = "qwen2.5:7b"):
        """
        Initialize A2UI agent with LLM provider.
        
        Args:
            provider: LLM provider name (ollama, azure_openai, etc.)
            model: Model name
        """
        self.a2ui_encoder = A2UIEncoder()
        self.agui_encoder = EventEncoder(accept="text/event-stream")
        
        # Get LLM provider
        self.llm_provider = LLMProviderFactory.get_provider(provider)
        self.model = model
        
        # Initialize component tool registry
        self.tool_registry = ComponentToolRegistry()
        
        logger.info(f"A2UI Agent initialized with {provider}/{model}")
    
    async def run(self, state: AgentState) -> AsyncGenerator[str, None]:
        """
        Generate UI components dynamically based on user prompt.
        
        Args:
            state: Agent state with messages, thread_id, run_id
        
        Yields:
            SSE-formatted strings (A2UI messages and AG-UI events)
        """
        messages = state.get("messages", [])
        thread_id = state["thread_id"]
        run_id = state["run_id"]
        
        # Get user message
        user_message = messages[-1].get("content", "") if messages else ""
        
        logger.info(f"A2UI Agent run - thread: {thread_id}, user: '{user_message}'")
        
        # Create unique surface ID
        surface_id = f"surface-{uuid.uuid4().hex[:8]}"
        
        # ===== Step 1: LLM decides which component to create =====
        try:
            component_data = await self._generate_component_with_llm(user_message)
        except Exception as e:
            logger.error(f"Failed to generate component: {e}")
            # Fallback to error message
            yield await self._send_error_message(
                f"Sorry, I couldn't generate the UI component: {str(e)}"
            )
            return
        
        # ===== Step 2: Create A2UI Surface =====
        # Create surface update with generated component
        surface_update = SurfaceUpdate(
            surface_id=surface_id,
            components=[component_data["component"]]
        )
        
        logger.debug(f"Created surface with component: {component_data['component_id']}")
        yield self.a2ui_encoder.encode(surface_update)
        
        # ===== Step 3: Initialize Data Model =====
        data_model = component_data["data_model"]
        data_update = DataModelUpdate(
            surface_id=surface_id,
            path=data_model["path"],
            contents=data_model["contents"]
        )
        
        logger.debug("Initialized data model")
        yield self.a2ui_encoder.encode(data_update)
        
        # ===== Step 4: Begin Rendering =====
        begin_render = BeginRendering(
            surface_id=surface_id,
            root_component_id=component_data["component_id"]
        )
        
        logger.debug(f"Begin rendering from: {component_data['component_id']}")
        yield self.a2ui_encoder.encode(begin_render)
        
        # ===== Step 5: Send AG-UI Confirmation Message =====
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        # Start text message
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "text"}
        )
        yield self.agui_encoder.encode(text_start)
        
        # Send confirmation
        confirmation = f"I've created the {component_data.get('component_type', 'component')} for you. You can interact with it above."
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=confirmation
        )
        yield self.agui_encoder.encode(text_content)
        
        # End text message
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(text_end)
        
        logger.info("A2UI Agent run completed")
    
    async def _generate_component_with_llm(self, user_prompt: str) -> Dict[str, Any]:
        """
        Use LLM with tool calling to generate component.
        
        Args:
            user_prompt: User's request (e.g., "Create a checkbox for terms")
        
        Returns:
            Dict with component, data_model, component_id, component_type
        """
        # Get tool schemas for LLM
        tool_schemas = self.tool_registry.get_tool_schemas()
        
        # Create system prompt
        system_prompt = """You are a UI component generator assistant.
        
Your job is to analyze user requests and create appropriate UI components.
Use the available tools to generate components based on user intent.

Examples:
- "checkbox for agreement" -> use create_checkbox tool
- "I need to agree to terms" -> use create_checkbox tool
- "show me a checkbox" -> use create_checkbox tool

Always call the most appropriate tool based on the user's request."""
        
        # Prepare messages for LLM
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Get LLM client
        client = self.llm_provider.get_client(self.model)
        
        # Call LLM with tools
        response = await client.generate_with_tools(
            messages=llm_messages,
            tools=tool_schemas,
            temperature=0.3  # Lower temperature for consistent tool calling
        )
        
        # Extract tool call from response
        if not response.get("tool_calls"):
            raise ValueError("LLM did not call any tool")
        
        tool_call = response["tool_calls"][0]
        tool_name = tool_call["function"]["name"]
        tool_args = json.loads(tool_call["function"]["arguments"])
        
        logger.debug(f"LLM called tool: {tool_name} with args: {tool_args}")
        
        # Get tool and generate component
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        component_data = tool.generate_component(**tool_args)
        component_data["component_type"] = tool_name.replace("create_", "")
        
        return component_data
    
    async def _send_error_message(self, error_text: str) -> str:
        """Send error message as AG-UI event"""
        message_id = f"msg-{uuid.uuid4().hex[:8]}"
        
        text_start = TextMessageStartEvent(
            type=EventType.TEXT_MESSAGE_START,
            message_id=message_id,
            role="assistant",
            metadata={"message_type": "error"}
        )
        yield self.agui_encoder.encode(text_start)
        
        text_content = TextMessageContentEvent(
            type=EventType.TEXT_MESSAGE_CONTENT,
            message_id=message_id,
            delta=error_text
        )
        yield self.agui_encoder.encode(text_content)
        
        text_end = TextMessageEndEvent(
            type=EventType.TEXT_MESSAGE_END,
            message_id=message_id
        )
        yield self.agui_encoder.encode(text_end)
```

**Key Changes**:
- Added LLM provider initialization
- Replaced hardcoded checkbox with LLM + tool calling flow
- Dynamic component generation based on user intent
- Error handling for failed tool calls
- Extensible to multiple component types

**Dependencies**:
- `tools/a2ui_tools.py` (new)
- `llm/provider_factory.py` (existing)
- LLM provider must support tool/function calling (Ollama with qwen2.5, OpenAI, etc.)

---

### 1.3 Add Tool Calling Support to LLM Providers

#### File: `backend/llm/provider_client.py` (MODIFY)

Add abstract method for tool calling:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMProviderClient(ABC):
    """Base class for LLM provider clients"""
    
    # ... existing methods ...
    
    @abstractmethod
    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response with tool calling support.
        
        Args:
            messages: Conversation messages
            tools: Tool schemas in OpenAI function calling format
            temperature: Sampling temperature
            **kwargs: Provider-specific parameters
        
        Returns:
            Dict with:
            - content: Text response (if no tool called)
            - tool_calls: List of tool calls (if tools called)
        """
        pass
```

#### File: `backend/llm/ollama_client.py` (MODIFY)

Implement tool calling for Ollama:

```python
async def generate_with_tools(
    self,
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]],
    temperature: float = 0.7,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate response with tool calling (Ollama format).
    
    Ollama supports tools via the `tools` parameter in chat completion.
    """
    import httpx
    
    payload = {
        "model": self.model,
        "messages": messages,
        "tools": tools,
        "temperature": temperature,
        "stream": False
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()
    
    # Extract tool calls from response
    message = result.get("message", {})
    
    if "tool_calls" in message:
        return {
            "content": message.get("content", ""),
            "tool_calls": message["tool_calls"]
        }
    else:
        return {
            "content": message.get("content", ""),
            "tool_calls": []
        }
```

#### File: `backend/llm/azure_openai_client.py` (MODIFY)

Implement tool calling for Azure OpenAI (already standard):

```python
async def generate_with_tools(
    self,
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]],
    temperature: float = 0.7,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate response with tool calling (Azure OpenAI format).
    
    Azure OpenAI uses standard OpenAI tool calling format.
    """
    response = await self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        tools=tools,
        temperature=temperature,
        tool_choice="auto"  # Let model decide when to call tools
    )
    
    message = response.choices[0].message
    
    if message.tool_calls:
        return {
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        }
    else:
        return {
            "content": message.content or "",
            "tool_calls": []
        }
```

**Dependencies**: 
- Ollama 0.5+ with tool calling support
- Azure OpenAI with gpt-4 or gpt-3.5-turbo

---

### 1.4 Update Tests

#### File: `backend/tests/test_a2ui_dynamic.py` (NEW)

Create tests for dynamic component generation:

```python
"""
Tests for Dynamic A2UI Component Generation

Test LLM-powered component generation with tool calling.
"""

import pytest
from agents.a2ui_agent import A2UIAgent
from tools.a2ui_tools import CheckboxTool, ComponentToolRegistry


class TestCheckboxTool:
    """Test checkbox tool generation"""
    
    def test_checkbox_tool_schema(self):
        """Test tool schema format"""
        tool = CheckboxTool()
        schema = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        }
        
        assert schema["function"]["name"] == "create_checkbox"
        assert "label" in schema["function"]["parameters"]["properties"]
    
    def test_checkbox_generation(self):
        """Test checkbox component generation"""
        tool = CheckboxTool()
        result = tool.generate_component(
            label="I agree to terms",
            checked=False
        )
        
        assert "component" in result
        assert "data_model" in result
        assert "component_id" in result
        assert result["component"].id == result["component_id"]


class TestComponentToolRegistry:
    """Test tool registry"""
    
    def test_registry_initialization(self):
        """Test registry has default tools"""
        registry = ComponentToolRegistry()
        assert len(registry.get_all_tools()) > 0
        assert registry.get_tool("create_checkbox") is not None
    
    def test_get_tool_schemas(self):
        """Test tool schema generation"""
        registry = ComponentToolRegistry()
        schemas = registry.get_tool_schemas()
        
        assert len(schemas) > 0
        assert schemas[0]["type"] == "function"
        assert "name" in schemas[0]["function"]


@pytest.mark.asyncio
class TestA2UIAgentDynamic:
    """Test dynamic A2UI agent with LLM"""
    
    async def test_agent_initialization(self):
        """Test agent initializes with LLM provider"""
        agent = A2UIAgent(provider="ollama", model="qwen2.5:7b")
        
        assert agent.llm_provider is not None
        assert agent.tool_registry is not None
        assert len(agent.tool_registry.get_all_tools()) > 0
    
    async def test_component_generation_flow(self):
        """Test end-to-end component generation"""
        agent = A2UIAgent(provider="ollama", model="qwen2.5:7b")
        
        state = {
            "messages": [
                {"role": "user", "content": "Create a checkbox for agreeing to terms"}
            ],
            "thread_id": "test-thread",
            "run_id": "test-run"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Should emit: surfaceUpdate, dataModelUpdate, beginRendering, AG-UI messages
        assert len(events) > 0
        
        # Check for A2UI events
        a2ui_events = [e for e in events if '"type":"surfaceUpdate"' in e or 
                       '"type":"dataModelUpdate"' in e or 
                       '"type":"beginRendering"' in e]
        assert len(a2ui_events) >= 3
```

---

## Phase 2: Frontend - No Changes Required

**Owner**: Frontend Agent (see [frontend.agent.md](../../.github/agents/frontend.agent.md))

**Good News**: The frontend A2UI client already supports dynamic components! No changes needed because:

1. **Frontend is data-driven**: It receives A2UI JSON and renders components
2. **Component mapping exists**: Frontend maps A2UI JSON to Shadcn UI components
3. **Protocol is stable**: surfaceUpdate, dataModelUpdate, beginRendering flow unchanged

The only difference is the *backend* now generates different components dynamically instead of static checkboxes.

### 2.1 Verify Frontend Handles Dynamic Components

**File**: `frontend/components/A2UIRenderer.tsx` (VERIFY ONLY)

Ensure the renderer handles any component type:

```typescript
// Existing code should handle dynamic components
const renderComponent = (component: A2UIComponent) => {
  switch (component.component.type) {
    case 'Checkbox':
      return <CheckboxComponent {...component.component.Checkbox} />;
    case 'Button':
      return <ButtonComponent {...component.component.Button} />;
    case 'Text':
      return <TextComponent {...component.component.Text} />;
    default:
      console.warn(`Unknown component type: ${component.component.type}`);
      return null;
  }
};
```

**Action**: No code changes needed, just verify existing renderer works.

---

## Phase 3: Testing & Validation

### 3.1 Unit Tests

**Backend**:
- [x] Test checkbox tool generation (`test_a2ui_dynamic.py`)
- [x] Test tool registry (`test_a2ui_dynamic.py`)
- [x] Test LLM tool calling integration
- [x] Test A2UI agent with different prompts

**Frontend**:
- [x] Verify existing A2UI renderer tests pass
- [x] Test dynamic component rendering

### 3.2 Integration Tests

#### Test Scenario 1: Checkbox Generation
```bash
# User prompt: "Create a checkbox to agree to terms"
# Expected:
# - LLM calls create_checkbox tool
# - Checkbox component generated
# - A2UI messages streamed
# - Frontend renders Shadcn Checkbox
```

#### Test Scenario 2: Multiple Components (Future)
```bash
# User prompt: "Create a form with name and email fields"
# Expected:
# - LLM calls multiple component tools
# - Form container + input fields generated
# - Frontend renders complete form
```

### 3.3 Manual Testing

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend
cd frontend
npm run dev

# Browser: http://localhost:3000
# 1. Select "A2UI Agent"
# 2. Send prompt: "Create a checkbox for agreeing to privacy policy"
# 3. Verify checkbox appears with correct label
# 4. Test checkbox interaction
# 5. Try different prompts to test LLM understanding
```

---

## Phase 4: Future Extensions

### 4.1 Add More Component Types

**Priority**: After checkbox works well

Component candidates:
- Button
- TextInput
- Select/Dropdown
- Radio buttons
- DatePicker
- Slider

Each requires:
1. Create tool class (e.g., `ButtonTool`)
2. Implement `generate_component()` method
3. Register in `ComponentToolRegistry`
4. Update frontend component mapping (if new type)

### 4.2 MCP Integration

**Priority**: Future enhancement

Replace custom tools with MCP (Model Context Protocol):
- MCP servers provide component tools
- Agents discover tools at runtime
- Better ecosystem compatibility

**Changes needed**:
- Add MCP client to backend
- Replace `ComponentToolRegistry` with MCP tool discovery
- Keep same tool interface for compatibility

### 4.3 Complex Layouts

**Priority**: Advanced feature

Support container components:
- VStack / HStack
- Grid layouts
- Tabs
- Cards

Requires:
- Nested component support in A2UI
- Layout tool classes
- Frontend container rendering

---

## Implementation Checklist

### Backend Tasks

- [ ] **1.1** Create `backend/tools/a2ui_tools.py`
  - [ ] Implement `BaseComponentTool` abstract class
  - [ ] Implement `CheckboxTool` 
  - [ ] Implement `ComponentToolRegistry`
  - [ ] Add tool schema generation

- [ ] **1.2** Update `backend/agents/a2ui_agent.py`
  - [ ] Add LLM provider initialization
  - [ ] Implement `_generate_component_with_llm()` method
  - [ ] Replace static checkbox with dynamic generation
  - [ ] Add error handling for tool calls

- [ ] **1.3** Update LLM provider clients
  - [ ] Add `generate_with_tools()` to `provider_client.py`
  - [ ] Implement in `ollama_client.py`
  - [ ] Implement in `azure_openai_client.py`
  - [ ] Implement in `gemini_client.py` (if needed)

- [ ] **1.4** Create tests
  - [ ] Create `backend/tests/test_a2ui_dynamic.py`
  - [ ] Test checkbox tool
  - [ ] Test tool registry
  - [ ] Test LLM integration (mock)

### Frontend Tasks

- [ ] **2.1** Verify existing A2UI renderer
  - [ ] Check component mapping works for dynamic components
  - [ ] Test with different component types
  - [ ] Ensure no regressions

### Integration Tasks

- [ ] **3.1** Integration testing
  - [ ] Test end-to-end flow with real LLM
  - [ ] Test different user prompts
  - [ ] Verify frontend rendering

- [ ] **3.2** Documentation
  - [ ] Update README with dynamic component examples
  - [ ] Document tool calling patterns
  - [ ] Add usage examples

---

## Success Criteria

✅ **Core Functionality**:
- A2UI agent uses LLM to understand user intent
- Agent calls appropriate component tool
- Checkbox component generates dynamically from any relevant prompt
- Frontend renders components correctly

✅ **Code Quality**:
- Unit tests pass (>80% coverage)
- Integration tests pass
- Type safety maintained (TypeScript + Python)
- Error handling implemented

✅ **User Experience**:
- User can request checkbox with natural language
- Component appears within 2-3 seconds
- Component is interactive and functional
- Error messages clear when generation fails

✅ **Extensibility**:
- Easy to add new component types
- Tool registry architecture clean
- Ready for MCP migration

---

## Migration Notes

### From Static to Dynamic

**Before (Static)**:
```python
# Hardcoded checkbox generation
checkbox = create_checkbox_component(
    component_id="terms-checkbox",
    label_text="I agree to the terms and conditions",
    value_path="/form/agreedToTerms"
)
```

**After (Dynamic)**:
```python
# LLM-powered generation
component_data = await self._generate_component_with_llm(
    "Create a checkbox for terms agreement"
)
# LLM calls create_checkbox tool with appropriate label
```

### Backward Compatibility

The changes are backward compatible:
- Existing A2UI protocol unchanged
- Frontend components work as before
- Static checkbox demo can coexist with dynamic agent

---

## Risk Mitigation

### Risk 1: LLM Doesn't Call Tools Correctly

**Mitigation**:
- Use models with good tool calling support (qwen2.5, gpt-4)
- Provide clear tool descriptions
- Add fallback to default checkbox if tool call fails
- Log tool calls for debugging

### Risk 2: Tool Arguments Invalid

**Mitigation**:
- Validate tool arguments in tool classes
- Use Pydantic for schema validation
- Return helpful error messages
- Add integration tests for edge cases

### Risk 3: Performance Issues

**Mitigation**:
- Cache LLM responses for common prompts
- Use streaming for tool calls
- Set reasonable timeouts
- Monitor LLM latency

---

## Timeline Estimate

**Total**: 2-3 days for full implementation

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 1.1 - Component Tools | Create tool classes | 4 hours |
| 1.2 - Agent Update | Add LLM integration | 4 hours |
| 1.3 - LLM Providers | Add tool calling | 3 hours |
| 1.4 - Backend Tests | Unit tests | 3 hours |
| 2.1 - Frontend Verify | Check compatibility | 1 hour |
| 3.1 - Integration | E2E testing | 3 hours |
| 3.2 - Documentation | Update docs | 2 hours |

**Note**: Timeline assumes LLM provider already supports tool calling (Ollama 0.5+, Azure OpenAI GPT-4).

---

## References

- [A2UI Protocol Spec](https://github.com/a2ui/a2ui-protocol)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Ollama Tool Calling](https://ollama.com/blog/tool-support)
- [LangGraph Tool Pattern](https://python.langchain.com/docs/langgraph/how-tos/tool-calling)
- [Previous Plan: 017-support-a2ui-protocol-plan.md](017-support-a2ui-protocol-plan.md)

---

**Plan Status**: Ready for Implementation  
**Next Step**: Begin Phase 1.1 - Create component tool classes  
**Review Required**: Before moving to Phase 2
