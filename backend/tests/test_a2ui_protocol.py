"""
Tests for A2UI Protocol Message Types and Encoder

Tests the A2UI protocol implementation including:
- Pydantic model validation
- Message encoding (SSE and JSONL)
- Component creation helpers
- Message type detection
"""

import pytest
import json
from protocols.a2ui_types import (
    Component,
    SurfaceUpdate,
    DataModelUpdate,
    DataContent,
    BeginRendering,
    DeleteSurface,
    create_checkbox_component,
    create_text_component,
    create_button_component
)
from protocols.a2ui_encoder import A2UIEncoder, is_a2ui_message


class TestA2UITypes:
    """Test A2UI message type models"""
    
    def test_component_creation(self):
        """Test basic component creation"""
        component = Component(
            id="test-component",
            component={
                "Checkbox": {
                    "label": {"literalString": "Test"},
                    "value": {"path": "/test"}
                }
            }
        )
        
        assert component.id == "test-component"
        assert "Checkbox" in component.component
    
    def test_surface_update_with_alias(self):
        """Test SurfaceUpdate with field aliases (camelCase)"""
        component = Component(id="comp-1", component={"Text": {}})
        
        surface_update = SurfaceUpdate(
            surface_id="surface-123",
            components=[component]
        )
        
        # Check field alias in dict export
        data = surface_update.model_dump(by_alias=True)
        assert data["surfaceId"] == "surface-123"
        assert data["type"] == "surfaceUpdate"
        assert len(data["components"]) == 1
    
    def test_data_model_update_with_boolean(self):
        """Test DataModelUpdate with boolean value"""
        data_update = DataModelUpdate(
            surface_id="surface-123",
            path="/form",
            contents=[
                DataContent(key="accepted", value_boolean=True)
            ]
        )
        
        assert data_update.surface_id == "surface-123"
        assert data_update.path == "/form"
        assert data_update.contents[0].value_boolean is True
    
    def test_data_model_update_with_multiple_types(self):
        """Test DataModelUpdate with multiple value types"""
        data_update = DataModelUpdate(
            surface_id="surface-123",
            contents=[
                DataContent(key="name", value_string="Alice"),
                DataContent(key="age", value_number=30),
                DataContent(key="active", value_boolean=True),
                DataContent(key="settings", value_map={"theme": "dark"})
            ]
        )
        
        contents = data_update.contents
        assert contents[0].value_string == "Alice"
        assert contents[1].value_number == 30
        assert contents[2].value_boolean is True
        assert contents[3].value_map == {"theme": "dark"}
    
    def test_begin_rendering(self):
        """Test BeginRendering message"""
        begin = BeginRendering(
            surface_id="surface-123",
            root_component_id="root-comp"
        )
        
        assert begin.type == "beginRendering"
        assert begin.surface_id == "surface-123"
        assert begin.root_component_id == "root-comp"
    
    def test_delete_surface(self):
        """Test DeleteSurface message"""
        delete = DeleteSurface(surface_id="surface-123")
        
        assert delete.type == "deleteSurface"
        assert delete.surface_id == "surface-123"


class TestA2UIHelpers:
    """Test helper functions for creating A2UI components"""
    
    def test_create_checkbox_component(self):
        """Test checkbox component helper"""
        checkbox = create_checkbox_component(
            component_id="cb-1",
            label_text="Accept terms",
            value_path="/form/accepted"
        )
        
        assert checkbox.id == "cb-1"
        assert "Checkbox" in checkbox.component
        assert checkbox.component["Checkbox"]["label"]["literalString"] == "Accept terms"
        assert checkbox.component["Checkbox"]["value"]["path"] == "/form/accepted"
    
    def test_create_text_component(self):
        """Test text component helper"""
        text = create_text_component(
            component_id="text-1",
            content="Hello world"
        )
        
        assert text.id == "text-1"
        assert "Text" in text.component
        assert text.component["Text"]["content"]["literalString"] == "Hello world"
    
    def test_create_button_component(self):
        """Test button component helper"""
        button = create_button_component(
            component_id="btn-1",
            label_text="Submit",
            action_name="form_submit"
        )
        
        assert button.id == "btn-1"
        assert "Button" in button.component
        assert button.component["Button"]["label"]["literalString"] == "Submit"
        assert button.component["Button"]["action"]["name"] == "form_submit"
        assert button.component["Button"]["action"]["context"] == {}


class TestA2UIEncoder:
    """Test A2UI message encoder"""
    
    def test_encode_surface_update_sse(self):
        """Test SSE encoding of SurfaceUpdate"""
        encoder = A2UIEncoder()
        
        component = Component(id="comp-1", component={"Text": {}})
        surface_update = SurfaceUpdate(
            surface_id="surface-123",
            components=[component]
        )
        
        encoded = encoder.encode(surface_update)
        
        # Should have SSE format
        assert encoded.startswith("data: ")
        assert encoded.endswith("\n\n")
        
        # Extract JSON
        json_str = encoded.replace("data: ", "").replace("\n\n", "")
        data = json.loads(json_str)
        
        assert data["type"] == "surfaceUpdate"
        assert data["surfaceId"] == "surface-123"
    
    def test_encode_jsonl(self):
        """Test JSONL encoding"""
        encoder = A2UIEncoder()
        
        begin = BeginRendering(
            surface_id="surface-123",
            root_component_id="root"
        )
        
        encoded = encoder.encode_jsonl(begin)
        
        # Should have JSONL format (single line + newline)
        assert encoded.endswith("\n")
        assert encoded.count("\n") == 1
        
        # Parse JSON
        data = json.loads(encoded.strip())
        assert data["type"] == "beginRendering"
    
    def test_encode_batch_sse(self):
        """Test batch encoding in SSE format"""
        encoder = A2UIEncoder()
        
        messages = [
            SurfaceUpdate(surface_id="s1", components=[]),
            BeginRendering(surface_id="s1", root_component_id="r1")
        ]
        
        encoded = encoder.encode_batch(messages, format="sse")
        
        # Should contain both messages
        assert encoded.count("data: ") == 2
        assert "surfaceUpdate" in encoded
        assert "beginRendering" in encoded
    
    def test_encode_batch_jsonl(self):
        """Test batch encoding in JSONL format"""
        encoder = A2UIEncoder()
        
        messages = [
            SurfaceUpdate(surface_id="s1", components=[]),
            DeleteSurface(surface_id="s1")
        ]
        
        encoded = encoder.encode_batch(messages, format="jsonl")
        
        # Should have 2 lines
        lines = encoded.strip().split("\n")
        assert len(lines) == 2
        
        # Each line should be valid JSON
        data1 = json.loads(lines[0])
        data2 = json.loads(lines[1])
        
        assert data1["type"] == "surfaceUpdate"
        assert data2["type"] == "deleteSurface"
    
    def test_encode_dict(self):
        """Test dictionary encoding"""
        encoder = A2UIEncoder()
        
        surface_update = SurfaceUpdate(
            surface_id="surface-123",
            components=[]
        )
        
        data = encoder.encode_dict(surface_update)
        
        assert isinstance(data, dict)
        assert data["type"] == "surfaceUpdate"
        assert data["surfaceId"] == "surface-123"
    
    def test_encode_batch_invalid_format(self):
        """Test batch encoding with invalid format"""
        encoder = A2UIEncoder()
        
        with pytest.raises(ValueError, match="Unknown format"):
            encoder.encode_batch([], format="xml")


class TestA2UIMessageDetection:
    """Test A2UI message type detection"""
    
    def test_is_a2ui_message_surface_update(self):
        """Test detection of surfaceUpdate"""
        data = {"type": "surfaceUpdate", "surfaceId": "s1"}
        assert is_a2ui_message(data) is True
    
    def test_is_a2ui_message_data_model_update(self):
        """Test detection of dataModelUpdate"""
        data = {"type": "dataModelUpdate", "surfaceId": "s1"}
        assert is_a2ui_message(data) is True
    
    def test_is_a2ui_message_begin_rendering(self):
        """Test detection of beginRendering"""
        data = {"type": "beginRendering", "surfaceId": "s1"}
        assert is_a2ui_message(data) is True
    
    def test_is_a2ui_message_delete_surface(self):
        """Test detection of deleteSurface"""
        data = {"type": "deleteSurface", "surfaceId": "s1"}
        assert is_a2ui_message(data) is True
    
    def test_is_not_a2ui_message_agui_event(self):
        """Test that AG-UI events are not detected as A2UI"""
        data = {"type": "TEXT_MESSAGE_CONTENT", "delta": "hello"}
        assert is_a2ui_message(data) is False
    
    def test_is_not_a2ui_message_empty(self):
        """Test empty dict"""
        assert is_a2ui_message({}) is False
    
    def test_is_not_a2ui_message_no_type(self):
        """Test dict without type field"""
        assert is_a2ui_message({"data": "test"}) is False
