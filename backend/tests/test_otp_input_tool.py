"""
Unit tests for OTP Input Tool

Tests the OTPInputTool class that generates OTP input components.
"""

import pytest
from tools.a2ui_tools import OTPInputTool, ComponentToolRegistry
from protocols.a2ui_types import Component, DataContent


class TestOTPInputTool:
    """Test suite for OTPInputTool"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.tool = OTPInputTool()
    
    def test_tool_name(self):
        """Test tool has correct name"""
        assert self.tool.name == "create_otp_input"
    
    def test_tool_description(self):
        """Test tool has description"""
        assert len(self.tool.description) > 0
        assert "OTP" in self.tool.description
        assert "verification" in self.tool.description.lower()
    
    def test_tool_parameters(self):
        """Test tool parameters schema"""
        params = self.tool.parameters
        assert params["type"] == "object"
        assert "properties" in params
        
        # Check required properties exist
        props = params["properties"]
        assert "title" in props
        assert "description" in props
        assert "max_length" in props
        assert "pattern_type" in props
        assert "button_text" in props
    
    def test_generate_basic_6digit_otp(self):
        """Test generating basic 6-digit OTP input"""
        result = self.tool.generate_component(
            title="Verify Email",
            description="Enter the 6-digit code",
            max_length=6
        )
        
        # Check result structure
        assert "component" in result
        assert "data_model" in result
        assert "component_id" in result
        
        # Check component
        component = result["component"]
        assert isinstance(component, Component)
        assert component.id.startswith("otp-input-")
        
        # Check component properties
        comp_data = component.component
        assert "OTPInput" in comp_data
        otp_props = comp_data["OTPInput"]
        
        assert otp_props["title"]["literalString"] == "Verify Email"
        assert otp_props["description"]["literalString"] == "Enter the 6-digit code"
        assert otp_props["maxLength"] == 6
        assert otp_props["patternType"] == "digits"
        assert otp_props["buttonText"]["literalString"] == "Verify"
        assert otp_props["disabled"] == False
    
    def test_generate_4digit_otp_with_separator(self):
        """Test generating 4-digit OTP with separator at position 2 (12-34)"""
        result = self.tool.generate_component(
            title="Phone Verification",
            max_length=4,
            separator_positions=[2]
        )
        
        component = result["component"]
        otp_props = component.component["OTPInput"]
        
        # Check groups
        assert len(otp_props["groups"]) == 2
        assert otp_props["groups"][0] == {"start": 0, "end": 2}
        assert otp_props["groups"][1] == {"start": 2, "end": 4}
    
    def test_generate_6digit_otp_with_separator(self):
        """Test generating 6-digit OTP with separator at position 3 (123-456)"""
        result = self.tool.generate_component(
            max_length=6,
            separator_positions=[3]
        )
        
        component = result["component"]
        otp_props = component.component["OTPInput"]
        
        # Check groups
        assert len(otp_props["groups"]) == 2
        assert otp_props["groups"][0] == {"start": 0, "end": 3}
        assert otp_props["groups"][1] == {"start": 3, "end": 6}
    
    def test_generate_otp_with_multiple_separators(self):
        """Test generating OTP with multiple separators (12-34-56)"""
        result = self.tool.generate_component(
            max_length=6,
            separator_positions=[2, 4]
        )
        
        component = result["component"]
        otp_props = component.component["OTPInput"]
        
        # Check groups
        assert len(otp_props["groups"]) == 3
        assert otp_props["groups"][0] == {"start": 0, "end": 2}
        assert otp_props["groups"][1] == {"start": 2, "end": 4}
        assert otp_props["groups"][2] == {"start": 4, "end": 6}
    
    def test_generate_alphanumeric_otp(self):
        """Test generating alphanumeric OTP"""
        result = self.tool.generate_component(
            pattern_type="alphanumeric"
        )
        
        component = result["component"]
        otp_props = component.component["OTPInput"]
        
        assert otp_props["patternType"] == "alphanumeric"
    
    def test_generate_disabled_otp(self):
        """Test generating disabled OTP input"""
        result = self.tool.generate_component(
            disabled=True
        )
        
        component = result["component"]
        otp_props = component.component["OTPInput"]
        
        assert otp_props["disabled"] == True
    
    def test_custom_button_text(self):
        """Test custom button text"""
        result = self.tool.generate_component(
            button_text="Confirm Code"
        )
        
        component = result["component"]
        otp_props = component.component["OTPInput"]
        
        assert otp_props["buttonText"]["literalString"] == "Confirm Code"
    
    def test_data_model_initialization(self):
        """Test data model is correctly initialized"""
        result = self.tool.generate_component()
        
        data_model = result["data_model"]
        assert "path" in data_model
        assert "contents" in data_model
        
        # Check initial value is empty string
        contents = data_model["contents"]
        assert len(contents) == 1
        assert isinstance(contents[0], DataContent)
        assert contents[0].key == "value"
        assert contents[0].value_string == ""
    
    def test_custom_data_path(self):
        """Test custom data path"""
        custom_path = "/auth/otp/code"
        result = self.tool.generate_component(
            data_path=custom_path
        )
        
        component = result["component"]
        otp_props = component.component["OTPInput"]
        
        assert otp_props["valuePath"] == custom_path
        
        # Check data model uses custom path
        data_model = result["data_model"]
        assert data_model["path"] == "/auth/otp"
        assert data_model["contents"][0].key == "code"
    
    def test_unique_component_ids(self):
        """Test that each generated component has unique ID"""
        result1 = self.tool.generate_component()
        result2 = self.tool.generate_component()
        
        assert result1["component_id"] != result2["component_id"]
        assert result1["component"].id != result2["component"].id


class TestOTPInputToolRegistry:
    """Test OTP tool registration"""
    
    def test_otp_tool_registered(self):
        """Test OTP tool is registered in ComponentToolRegistry"""
        registry = ComponentToolRegistry()
        
        # Check OTP tool exists
        otp_tool = registry.get_tool("create_otp_input")
        assert otp_tool is not None
        assert isinstance(otp_tool, OTPInputTool)
    
    def test_otp_tool_in_schemas(self):
        """Test OTP tool appears in tool schemas"""
        registry = ComponentToolRegistry()
        schemas = registry.get_tool_schemas()
        
        # Find OTP schema
        otp_schema = None
        for schema in schemas:
            if schema["function"]["name"] == "create_otp_input":
                otp_schema = schema
                break
        
        assert otp_schema is not None
        assert otp_schema["type"] == "function"
        assert "parameters" in otp_schema["function"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
