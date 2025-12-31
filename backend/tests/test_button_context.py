"""
Test button component with context paths
"""

import pytest
from tools.a2ui_tools import ButtonTool


class TestButtonContext:
    """Test button context path functionality"""
    
    def test_button_without_context(self):
        """Test button without context paths (empty context)"""
        tool = ButtonTool()
        result = tool.generate_component(
            label="Click Me",
            action_name="test_click"
        )
        
        assert "component" in result
        assert "Button" in result["component"].component
        
        button_config = result["component"].component["Button"]
        assert button_config["action"]["name"] == "test_click"
        assert button_config["action"]["context"] == {}  # Empty context
    
    def test_button_with_context_paths(self):
        """Test button with context paths for form data collection"""
        tool = ButtonTool()
        result = tool.generate_component(
            label="Submit",
            action_name="submit_form",
            context_paths={
                "email": "/user/email",
                "name": "/user/name"
            }
        )
        
        assert "component" in result
        assert "Button" in result["component"].component
        
        button_config = result["component"].component["Button"]
        assert button_config["action"]["name"] == "submit_form"
        assert button_config["action"]["context"] == {
            "email": {"path": "/user/email"},
            "name": {"path": "/user/name"}
        }
    
    def test_button_with_single_context_path(self):
        """Test button with single context path"""
        tool = ButtonTool()
        result = tool.generate_component(
            label="Send",
            action_name="send_message",
            context_paths={"message": "/chat/input"}
        )
        
        button_config = result["component"].component["Button"]
        assert button_config["action"]["context"] == {
            "message": {"path": "/chat/input"}
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
