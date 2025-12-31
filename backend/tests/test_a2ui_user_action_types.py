"""
Unit tests for A2UI User Action Types

Tests the Pydantic models for client-to-server messages:
- UserAction
- ErrorMessage
- ClientToServerMessage union type
"""

import pytest
from datetime import datetime
from protocols.a2ui_types import UserAction, ErrorMessage


def test_user_action_basic():
    """Test basic UserAction model"""
    action = UserAction(
        name="test_action",
        surfaceId="test_surface",
        sourceComponentId="test_button",
        timestamp="2025-12-30T10:00:00Z",
        context={"key": "value"}
    )
    
    assert action.name == "test_action"
    assert action.surface_id == "test_surface"
    assert action.source_component_id == "test_button"
    assert action.timestamp == "2025-12-30T10:00:00Z"
    assert action.context == {"key": "value"}


def test_user_action_with_alias():
    """Test UserAction with camelCase aliases"""
    action = UserAction(
        name="submit_form",
        surfaceId="form_surface",  # Using camelCase
        sourceComponentId="submit_btn",  # Using camelCase
        timestamp="2025-12-30T10:00:00Z",
        context={"email": "test@example.com"}
    )
    
    # Should map to snake_case internally
    assert action.surface_id == "form_surface"
    assert action.source_component_id == "submit_btn"


def test_user_action_empty_context():
    """Test UserAction with empty context"""
    action = UserAction(
        name="click",
        surfaceId="main",
        sourceComponentId="btn1",
        timestamp="2025-12-30T10:00:00Z"
    )
    
    assert action.context == {}


def test_user_action_complex_context():
    """Test UserAction with complex nested context"""
    action = UserAction(
        name="book_restaurant",
        surfaceId="booking_form",
        sourceComponentId="submit_button",
        timestamp="2025-12-30T10:00:00Z",
        context={
            "restaurantName": "The Gourmet",
            "partySize": 4,
            "reservationTime": "2025-12-30T19:00:00Z",
            "preferences": {
                "seating": "outdoor",
                "dietary": ["vegetarian", "gluten-free"]
            }
        }
    )
    
    assert action.context["restaurantName"] == "The Gourmet"
    assert action.context["partySize"] == 4
    assert action.context["preferences"]["seating"] == "outdoor"


def test_error_message_basic():
    """Test basic ErrorMessage model"""
    error = ErrorMessage(
        code="VALIDATION_FAILED",
        surfaceId="form_surface",
        path="/user/email",
        message="Invalid email format"
    )
    
    assert error.code == "VALIDATION_FAILED"
    assert error.surface_id == "form_surface"
    assert error.path == "/user/email"
    assert error.message == "Invalid email format"


def test_user_action_serialization():
    """Test UserAction serialization to dict"""
    action = UserAction(
        name="test",
        surfaceId="surface1",
        sourceComponentId="comp1",
        timestamp="2025-12-30T10:00:00Z",
        context={"data": "value"}
    )
    
    # Serialize with aliases (camelCase)
    data = action.model_dump(by_alias=True)
    
    assert data["name"] == "test"
    assert data["surfaceId"] == "surface1"
    assert data["sourceComponentId"] == "comp1"
    assert "surface_id" not in data  # Should use alias
    assert "source_component_id" not in data


def test_user_action_from_json():
    """Test UserAction deserialization from JSON-like dict"""
    data = {
        "name": "submit",
        "surfaceId": "form",
        "sourceComponentId": "btn",
        "timestamp": "2025-12-30T10:00:00Z",
        "context": {"field": "value"}
    }
    
    action = UserAction(**data)
    
    assert action.name == "submit"
    assert action.surface_id == "form"
    assert action.source_component_id == "btn"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
