"""
Test Canvas agent selection in chat endpoint

Verifies that the Canvas agent works correctly when selected in the chat endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_canvas_agent_in_chat_endpoint():
    """Test that Canvas agent works in /api/chat endpoint"""
    print("Testing Canvas Agent in Chat Endpoint")
    print("=" * 70)
    
    payload = {
        "thread_id": "test-canvas-chat",
        "run_id": "test-canvas-run",
        "messages": [
            {"role": "user", "content": "Create a simple hello world Python script"}
        ],
        "agent": "canvas"
    }
    
    try:
        print(f"\nSending request with agent='canvas'...")
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=30
        )
        
        # Check status code
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        print("✅ Request accepted (200 OK)")
        print("\nReceiving events:")
        print("-" * 70)
        
        # Read and parse events
        events_received = []
        error_occurred = False
        error_message = None
        
        for line in response.iter_lines(decode_unicode=True):
            if line:
                print(line)
                
                # Parse event type and data
                if line.startswith("event:"):
                    event_type = line.split(":", 1)[1].strip()
                    events_received.append(event_type)
                    
                    if event_type == "run_error":
                        error_occurred = True
                
                if line.startswith("data:") and error_occurred:
                    try:
                        data = json.loads(line.split(":", 1)[1].strip())
                        error_message = data.get("message", "Unknown error")
                    except:
                        pass
        
        print("-" * 70)
        
        # Validate results
        print(f"\nEvents received: {events_received}")
        
        if error_occurred:
            print(f"\n❌ RUN_ERROR occurred: {error_message}")
            return False
        
        # Check for expected events
        if "run_started" not in events_received:
            print("❌ Missing RUN_STARTED event")
            return False
        
        if "run_finished" not in events_received and "run_error" not in events_received:
            print("❌ Missing completion event (RUN_FINISHED or RUN_ERROR)")
            return False
        
        if "run_finished" in events_received:
            print("\n✅ Canvas agent executed successfully!")
            print("✅ No errors occurred")
            return True
        
    except requests.exceptions.Timeout:
        print("⚠ Request timed out (may indicate long processing)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        print("Please start the backend server with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Canvas Agent in Chat Endpoint Test")
    print("=" * 70)
    print("This test verifies that the Canvas agent works correctly")
    print("when selected in the /api/chat endpoint")
    print("=" * 70)
    
    success = test_canvas_agent_in_chat_endpoint()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ TEST PASSED - Canvas agent works in chat endpoint")
    else:
        print("❌ TEST FAILED - Canvas agent has issues")
    print("=" * 70)
    
    exit(0 if success else 1)
