"""
Test the unified /chat/{agent_id} endpoint
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_chat_agent_endpoint():
    """Test /chat/chat-agent endpoint for text-only conversations"""
    print("\n=== Testing /chat/chat-agent endpoint ===\n")
    
    payload = {
        "messages": [
            {"role": "user", "content": "What is 2+2?"}
        ],
        "model": "qwen:7b"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/chat-agent",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Status code: 200 OK")
        
        # Parse SSE events
        events = []
        text_message_start_found = False
        text_message_content_count = 0
        text_message_end_found = False
        is_text_message = False
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    event_data = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        event = json.loads(event_data)
                        events.append(event)
                        
                        print(f"Event: {event.get('type')}")
                        
                        # Check for TEXT_MESSAGE_START with text metadata
                        if event.get('type') == 'text_message_start':
                            text_message_start_found = True
                            metadata = event.get('metadata', {})
                            if metadata.get('message_type') == 'text':
                                is_text_message = True
                                print("  ✓ Text message detected (message_type='text')")
                        
                        # Count TEXT_MESSAGE_CONTENT chunks
                        elif event.get('type') == 'text_message_content':
                            text_message_content_count += 1
                        
                        # Check for TEXT_MESSAGE_END
                        elif event.get('type') == 'text_message_end':
                            text_message_end_found = True
                        
                    except json.JSONDecodeError:
                        pass
        
        print(f"\n✓ Total events: {len(events)}")
        print(f"✓ TEXT_MESSAGE_START found: {text_message_start_found}")
        print(f"✓ Is text message: {is_text_message}")
        print(f"✓ TEXT_MESSAGE_CONTENT chunks: {text_message_content_count}")
        print(f"✓ TEXT_MESSAGE_END found: {text_message_end_found}")
        
        # Validate
        assert text_message_start_found, "TEXT_MESSAGE_START not found"
        assert is_text_message, "message_type='text' not found in metadata"
        assert text_message_content_count > 0, "No TEXT_MESSAGE_CONTENT chunks"
        assert text_message_end_found, "TEXT_MESSAGE_END not found"
        
        print("\n✓ All checks passed for chat-agent!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_canvas_agent_endpoint():
    """Test /chat/canvas-agent endpoint for artifact generation"""
    print("\n=== Testing /chat/canvas-agent endpoint ===\n")
    
    payload = {
        "messages": [
            {"role": "user", "content": "Create a Python function to calculate fibonacci numbers"}
        ],
        "model": "qwen:7b"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/canvas-agent",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Status code: 200 OK")
        
        # Parse SSE events
        events = []
        text_message_start_found = False
        is_artifact_message = False
        artifact_metadata = {}
        text_message_content_count = 0
        text_message_end_found = False
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    event_data = line_str[6:]
                    try:
                        event = json.loads(event_data)
                        events.append(event)
                        
                        print(f"Event: {event.get('type')}")
                        
                        # Check for TEXT_MESSAGE_START with artifact metadata
                        if event.get('type') == 'text_message_start':
                            text_message_start_found = True
                            metadata = event.get('metadata', {})
                            if metadata.get('message_type') == 'artifact':
                                is_artifact_message = True
                                artifact_metadata = metadata
                                print("  ✓ Artifact message detected!")
                                print(f"    - artifact_type: {metadata.get('artifact_type')}")
                                print(f"    - language: {metadata.get('language')}")
                                print(f"    - title: {metadata.get('title')}")
                        
                        # Count TEXT_MESSAGE_CONTENT chunks
                        elif event.get('type') == 'text_message_content':
                            text_message_content_count += 1
                        
                        # Check for TEXT_MESSAGE_END
                        elif event.get('type') == 'text_message_end':
                            text_message_end_found = True
                        
                    except json.JSONDecodeError:
                        pass
        
        print(f"\n✓ Total events: {len(events)}")
        print(f"✓ TEXT_MESSAGE_START found: {text_message_start_found}")
        print(f"✓ Is artifact message: {is_artifact_message}")
        print(f"✓ TEXT_MESSAGE_CONTENT chunks: {text_message_content_count}")
        print(f"✓ TEXT_MESSAGE_END found: {text_message_end_found}")
        
        # Validate
        assert text_message_start_found, "TEXT_MESSAGE_START not found"
        assert is_artifact_message, "message_type='artifact' not found in metadata"
        assert artifact_metadata.get('artifact_type') in ['code', 'text'], "Invalid artifact_type"
        assert text_message_content_count > 0, "No TEXT_MESSAGE_CONTENT chunks"
        assert text_message_end_found, "TEXT_MESSAGE_END not found"
        
        print("\n✓ All checks passed for canvas-agent!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("Testing Unified /chat/{agent_id} Endpoint")
    print("=" * 60)
    
    results = []
    
    # Test chat agent
    results.append(("chat-agent", test_chat_agent_endpoint()))
    
    # Wait a bit between tests
    time.sleep(2)
    
    # Test canvas agent
    results.append(("canvas-agent", test_canvas_agent_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for agent, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{agent}: {status}")
    
    all_passed = all(success for _, success in results)
    print("=" * 60)
    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server")
        print("Please start the backend server with: cd backend && python main.py")
        exit(1)
