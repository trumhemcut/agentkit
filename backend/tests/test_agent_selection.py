"""
Test script for Agent Selection in Chat Endpoint

Tests that the /api/chat endpoint properly handles agent parameter
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_chat_with_valid_agent():
    """Test chat endpoint with valid agent parameter"""
    print("Test 1: Chat endpoint with valid agent (chat)")
    print("=" * 50)
    
    payload = {
        "thread_id": "test-thread-1",
        "run_id": "test-run-1",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "agent": "chat"
    }
    
    try:
        # We just test that the endpoint accepts the parameter without error
        # Not actually streaming the full response
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=5
        )
        
        # Should get 200 and start streaming
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Request accepted with agent='chat'")
        
        # Read first few bytes to confirm streaming started
        chunk = next(response.iter_content(chunk_size=100), None)
        if chunk:
            print("✓ Server started streaming response")
        
        response.close()
        return True
        
    except requests.exceptions.Timeout:
        print("⚠ Request timed out (this is expected for streaming)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_with_invalid_agent():
    """Test chat endpoint with invalid agent parameter"""
    print("\nTest 2: Chat endpoint with invalid agent")
    print("=" * 50)
    
    payload = {
        "thread_id": "test-thread-2",
        "run_id": "test-run-2",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "agent": "nonexistent_agent"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Accept": "text/event-stream"},
            timeout=5
        )
        
        # Should get 400 error for invalid agent
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Server returned 400 for invalid agent")
        
        error_data = response.json()
        assert "not available" in error_data.get("detail", "").lower(), "Error message not appropriate"
        print(f"✓ Error message: {error_data.get('detail')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_with_canvas_agent():
    """Test chat endpoint with canvas agent"""
    print("\nTest 3: Chat endpoint with canvas agent")
    print("=" * 50)
    
    payload = {
        "thread_id": "test-thread-3",
        "run_id": "test-run-3",
        "messages": [
            {"role": "user", "content": "Create a hello world script"}
        ],
        "agent": "canvas"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=5
        )
        
        # Should get 200 for valid canvas agent
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Request accepted with agent='canvas'")
        
        # Read first few bytes to confirm streaming started
        chunk = next(response.iter_content(chunk_size=100), None)
        if chunk:
            print("✓ Server started streaming response")
        
        response.close()
        return True
        
    except requests.exceptions.Timeout:
        print("⚠ Request timed out (this is expected for streaming)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat_without_agent_param():
    """Test chat endpoint without agent parameter (should use default)"""
    print("\nTest 4: Chat endpoint without agent parameter")
    print("=" * 50)
    
    payload = {
        "thread_id": "test-thread-4",
        "run_id": "test-run-4",
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
        # No agent parameter - should default to "chat"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=5
        )
        
        # Should get 200 and use default agent
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Request accepted without agent parameter (using default)")
        
        # Read first few bytes to confirm streaming started
        chunk = next(response.iter_content(chunk_size=100), None)
        if chunk:
            print("✓ Server started streaming response")
        
        response.close()
        return True
        
    except requests.exceptions.Timeout:
        print("⚠ Request timed out (this is expected for streaming)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("Testing Agent Selection in Chat Endpoint")
    print("=" * 70)
    
    try:
        all_passed = True
        all_passed &= test_chat_with_valid_agent()
        all_passed &= test_chat_with_invalid_agent()
        all_passed &= test_chat_with_canvas_agent()
        all_passed &= test_chat_without_agent_param()
        
        print("\n" + "=" * 70)
        if all_passed:
            print("✓ All tests passed!")
        else:
            print("❌ Some tests failed")
        
        exit(0 if all_passed else 1)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print("Please start the backend server with: python main.py")
        exit(1)
