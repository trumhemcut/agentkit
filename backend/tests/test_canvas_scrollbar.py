"""
Automated test to verify canvas scrollbar functionality
Tests the height constraints and overflow behavior in canvas mode
"""
import requests
import json
import time
from typing import List, Dict

# Configuration
BASE_URL = "http://localhost:8000"
CANVAS_AGENT = "canvas"
TEST_MESSAGES_COUNT = 15  # Number of messages to generate scrollbar

def test_canvas_message_generation():
    """
    Test 1: Generate multiple messages to verify backend responds correctly
    This indirectly tests that the UI will have content to scroll
    """
    print("Test 1: Generating messages for canvas mode...")
    
    messages = []
    for i in range(TEST_MESSAGES_COUNT):
        message = {
            "content": f"Test message {i+1} to verify scrollbar functionality",
            "role": "user"
        }
        messages.append(message)
    
    # Send request to canvas agent
    payload = {
        "messages": messages,
        "agent": CANVAS_AGENT,
        "thread_id": "test_scrollbar_thread"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/agents/chat",
            json=payload,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Backend responds correctly to {TEST_MESSAGES_COUNT} messages")
            
            # Count response chunks
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
            
            print(f"   Received {chunk_count} event chunks from backend")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_frontend_css_classes():
    """
    Test 2: Verify CSS classes are correctly applied
    This checks that the implementation includes the overflow-hidden fix
    """
    print("\nTest 2: Checking frontend CSS implementation...")
    
    # Read CanvasLayout component
    try:
        with open("/home/phihuynh/projects/agenkit/frontend/components/Canvas/CanvasLayout.tsx", "r") as f:
            content = f.read()
            
        # Check for the critical overflow-hidden class in chat panel
        if 'overflow-hidden' in content and 'flex-[0_0_33.333%]' in content:
            # Verify it's in the chat panel div specifically
            if 'flex flex-col border-r overflow-hidden' in content or 'overflow-hidden' in content.split('flex-[0_0_33.333%]')[1].split('>')[0]:
                print("✅ CanvasLayout has overflow-hidden class in chat panel")
                
                # Also verify CanvasChatContainer structure
                with open("/home/phihuynh/projects/agenkit/frontend/components/Canvas/CanvasChatContainer.tsx", "r") as f2:
                    chat_content = f2.read()
                
                if 'flex-1 overflow-hidden' in chat_content:
                    print("✅ CanvasChatContainer has correct overflow structure")
                    return True
                else:
                    print("⚠️  CanvasChatContainer missing flex-1 overflow-hidden wrapper")
                    return False
            else:
                print("❌ overflow-hidden not found in correct location")
                return False
        else:
            print("❌ Required CSS classes not found")
            return False
            
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_message_history_structure():
    """
    Test 3: Verify MessageHistory component has correct overflow classes
    """
    print("\nTest 3: Checking MessageHistory overflow configuration...")
    
    try:
        with open("/home/phihuynh/projects/agenkit/frontend/components/MessageHistory.tsx", "r") as f:
            content = f.read()
        
        # Check for h-full and overflow-y-auto
        if 'overflow-y-auto' in content and ('h-full' in content or 'h-screen' in content):
            print("✅ MessageHistory has correct overflow-y-auto configuration")
            return True
        else:
            print("❌ MessageHistory missing required overflow classes")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def run_all_tests():
    """Execute all tests and report results"""
    print("=" * 60)
    print("CANVAS SCROLLBAR FIX - AUTOMATED TEST SUITE")
    print("=" * 60)
    
    results = {
        "Backend Message Generation": test_canvas_message_generation(),
        "Frontend CSS Classes": test_frontend_css_classes(),
        "MessageHistory Structure": test_message_history_structure()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Scrollbar fix is correctly implemented.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
