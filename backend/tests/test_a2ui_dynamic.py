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
        assert schema["function"]["parameters"]["required"] == ["label"]
    
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
        # Check component structure instead of type attribute
        assert "Checkbox" in result["component"].component
    
    def test_checkbox_with_custom_path(self):
        """Test checkbox with custom data path"""
        tool = CheckboxTool()
        result = tool.generate_component(
            label="Accept terms",
            checked=True,
            data_path="/form/terms/accepted"
        )
        
        assert result["data_model"]["path"] == "/form/terms"
        assert result["data_model"]["contents"][0].key == "accepted"
        assert result["data_model"]["contents"][0].value_boolean == True


class TestComponentToolRegistry:
    """Test tool registry"""
    
    def test_registry_initialization(self):
        """Test registry has default tools"""
        registry = ComponentToolRegistry()
        assert len(registry.get_all_tools()) == 2  # CheckboxTool + MultipleCheckboxesTool
        assert registry.get_tool("create_checkbox") is not None
        assert registry.get_tool("create_checkboxes") is not None
    
    def test_get_tool_schemas(self):
        """Test tool schema generation"""
        registry = ComponentToolRegistry()
        schemas = registry.get_tool_schemas()
        
        assert len(schemas) == 2  # Two default tools
        assert schemas[0]["type"] == "function"
        assert "name" in schemas[0]["function"]
        assert "description" in schemas[0]["function"]
        assert "parameters" in schemas[0]["function"]
    
    def test_register_custom_tool(self):
        """Test registering custom tool"""
        from tools.a2ui_tools import BaseComponentTool
        
        class CustomTool(BaseComponentTool):
            @property
            def name(self) -> str:
                return "create_custom"
            
            @property
            def description(self) -> str:
                return "Custom tool"
            
            @property
            def parameters(self) -> dict:
                return {"type": "object", "properties": {}}
            
            def generate_component(self, **kwargs):
                return {"component": None, "data_model": None, "component_id": "test"}
        
        registry = ComponentToolRegistry()
        custom_tool = CustomTool()
        registry.register_tool(custom_tool)
        
        assert registry.get_tool("create_custom") is not None
        assert len(registry.get_all_tools()) == 3  # 2 default + custom


class TestMultipleCheckboxesTool:
    """Test multiple checkboxes tool"""
    
    def test_multiple_checkboxes_generation(self):
        """Test generating multiple checkboxes"""
        from tools.a2ui_tools import MultipleCheckboxesTool
        
        tool = MultipleCheckboxesTool()
        result = tool.generate_component(
            labels=["Chuyến bay HN → SG", "Chuyến bay SG → DN", "Chuyến bay DN → HN"],
            group_name="flight_plan"
        )
        
        assert "components" in result  # Multiple components
        assert "data_model" in result
        assert "component_ids" in result
        assert "root_component_id" in result
        
        # Should have 4 components: 3 checkboxes + 1 Column container
        assert len(result["components"]) == 4
        assert len(result["component_ids"]) == 3  # Only checkbox IDs
        
        # Root should be the Column container (last component)
        container = result["components"][-1]
        assert "Column" in container.component
        assert result["root_component_id"] == container.id
        
        # Check data model has 3 entries
        assert len(result["data_model"]["contents"]) == 3
        assert result["data_model"]["path"] == "/ui/flight_plan"
    
    def test_multiple_checkboxes_with_states(self):
        """Test generating checkboxes with initial states"""
        from tools.a2ui_tools import MultipleCheckboxesTool
        
        tool = MultipleCheckboxesTool()
        result = tool.generate_component(
            labels=["Task 1", "Task 2", "Task 3"],
            checked_states=[True, False, True],
            group_name="tasks"
        )
        
        # Check states are correct
        contents = result["data_model"]["contents"]
        assert contents[0].value_boolean == True
        assert contents[1].value_boolean == False
        assert contents[2].value_boolean == True


@pytest.mark.asyncio
class TestA2UIAgentDynamic:
    """Test dynamic A2UI agent with LLM"""
    
    async def test_agent_initialization(self):
        """Test agent initializes with LLM provider"""
        agent = A2UIAgent(provider="ollama", model="qwen:7b")
        
        assert agent.llm_provider is not None
        assert agent.tool_registry is not None
        assert len(agent.tool_registry.get_all_tools()) > 0
        assert agent.provider_name == "ollama"
        assert agent.model == "qwen:7b"
    
    async def test_component_generation_flow(self):
        """Test end-to-end component generation"""
        agent = A2UIAgent(provider="ollama", model="qwen:7b")
        
        state = {
            "messages": [
                {"role": "user", "content": "Create a checkbox for agreeing to terms"}
            ],
            "thread_id": "test-thread",
            "run_id": "test-run"
        }
        
        events = []
        has_tool_support = True
        async for event in agent.run(state):
            events.append(event)
            # Check if we got an error about tool support
            if "does not support tools" in event.lower() or "couldn't generate" in event.lower():
                has_tool_support = False
        
        # Should emit some events
        assert len(events) > 0
        
        if not has_tool_support:
            pytest.skip("Model doesn't support tool calling - this is expected for some models")
        
        # Check for A2UI events (only if tool support is available)
        a2ui_events = [e for e in events if '"type":"surfaceUpdate"' in e or 
                       '"type":"dataModelUpdate"' in e or 
                       '"type":"beginRendering"' in e]
        assert len(a2ui_events) >= 3  # At least surface, data, and begin
        
        # Check for AG-UI events
        agui_events = [e for e in events if 'event:' in e]
        assert len(agui_events) > 0  # At least one AG-UI event
    
    async def test_error_handling(self):
        """Test error handling when LLM fails"""
        agent = A2UIAgent(provider="ollama", model="qwen:7b")
        
        state = {
            "messages": [
                {"role": "user", "content": ""}  # Empty message
            ],
            "thread_id": "test-thread",
            "run_id": "test-run"
        }
        
        events = []
        try:
            async for event in agent.run(state):
                events.append(event)
        except Exception as e:
            # If Ollama is not available or model doesn't support tools, skip this test
            error_str = str(e).lower()
            if "connect" in error_str or "ollama" in error_str or "404" in error_str or "not found" in error_str or "does not support tools" in error_str or "400" in error_str:
                pytest.skip(f"Ollama not available or model doesn't support tools: {e}")
            raise
        
        # Should have some events (at least error message)
        assert len(events) > 0


@pytest.mark.asyncio
class TestLLMToolCalling:
    """Test LLM tool calling integration"""
    
    async def test_tool_schemas_format(self):
        """Test that tool schemas are in correct format for LLM"""
        registry = ComponentToolRegistry()
        schemas = registry.get_tool_schemas()
        
        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]
            
            # Check parameters structure
            params = schema["function"]["parameters"]
            assert params["type"] == "object"
            assert "properties" in params
    
    async def test_provider_has_tool_support(self):
        """Test that providers support tool calling"""
        from llm.provider_factory import LLMProviderFactory
        
        provider = LLMProviderFactory.get_provider("ollama", "qwen:7b")
        assert hasattr(provider, "get_model_with_tools")
        
        # Test binding tools
        dummy_tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "Test tool",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
        
        model_with_tools = provider.get_model_with_tools(dummy_tools)
        assert model_with_tools is not None
