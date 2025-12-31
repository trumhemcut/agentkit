"""
Integration tests for A2UI User Action Endpoint

Tests the POST /agents/{agent_id}/action endpoint that handles
user actions from A2UI components.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_user_action_endpoint_exists():
    """Test that user action endpoint is registered"""
    # Send a basic user action
    response = client.post(
        "/api/agents/a2ui-loop/action",
        json={
            "userAction": {
                "name": "test_action",
                "surfaceId": "test_surface",
                "sourceComponentId": "test_component",
                "timestamp": "2025-12-30T10:00:00Z",
                "context": {}
            },
            "threadId": "test-thread",
            "runId": "test-run"
        }
    )
    
    # Should not be 404 (endpoint exists)
    assert response.status_code != 404


def test_user_action_invalid_agent():
    """Test error handling for invalid agent ID"""
    response = client.post(
        "/api/agents/nonexistent_agent/action",
        json={
            "userAction": {
                "name": "test",
                "surfaceId": "test",
                "sourceComponentId": "test",
                "timestamp": "2025-12-30T10:00:00Z",
                "context": {}
            },
            "threadId": "test",
            "runId": "test"
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_user_action_non_a2ui_agent():
    """Test error when agent doesn't support A2UI"""
    # Try to send action to chat agent (doesn't support A2UI)
    response = client.post(
        "/api/agents/chat/action",
        json={
            "userAction": {
                "name": "test",
                "surfaceId": "test",
                "sourceComponentId": "test",
                "timestamp": "2025-12-30T10:00:00Z",
                "context": {}
            },
            "threadId": "test",
            "runId": "test"
        }
    )
    
    # Should return 400 error
    assert response.status_code == 400
    assert "does not support A2UI" in response.json()["detail"]


def test_user_action_test_click():
    """Test simple test_click action"""
    response = client.post(
        "/api/agents/a2ui-loop/action",
        json={
            "userAction": {
                "name": "test_click",
                "surfaceId": "test_surface",
                "sourceComponentId": "test_button",
                "timestamp": "2025-12-30T10:00:00Z",
                "context": {}
            },
            "threadId": "thread-123",
            "runId": "run-456"
        }
    )
    
    assert response.status_code == 200
    
    # Check that response is SSE stream
    assert response.headers["content-type"].startswith("text/event-stream")


def test_user_action_with_context():
    """Test action with complex context data"""
    response = client.post(
        "/api/agents/a2ui-loop/action",
        json={
            "userAction": {
                "name": "submit_form",
                "surfaceId": "contact_form",
                "sourceComponentId": "submit_button",
                "timestamp": "2025-12-30T10:00:00Z",
                "context": {
                    "email": "test@example.com",
                    "name": "Test User",
                    "message": "Hello world"
                }
            },
            "threadId": "thread-789",
            "runId": "run-012"
        }
    )
    
    assert response.status_code == 200


def test_user_action_missing_required_fields():
    """Test validation of required fields"""
    # Missing timestamp
    response = client.post(
        "/api/agents/a2ui-loop/action",
        json={
            "userAction": {
                "name": "test",
                "surfaceId": "test",
                "sourceComponentId": "test",
                "context": {}
            },
            "threadId": "test",
            "runId": "test"
        }
    )
    
    # Should return 422 validation error
    assert response.status_code == 422


def test_user_action_invalid_json():
    """Test handling of invalid JSON"""
    response = client.post(
        "/api/agents/a2ui-loop/action",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    # Should return 422 validation error
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
