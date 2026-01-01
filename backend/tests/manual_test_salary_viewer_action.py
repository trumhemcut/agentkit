"""
Manual test for Salary Viewer Agent with User Action handling

This test simulates the complete flow:
1. User asks about salary
2. Agent generates OTP component
3. User enters OTP and clicks Verify
4. Agent echoes OTP and reveals salary
"""

import asyncio
import uuid
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.salary_viewer_agent import SalaryViewerAgent


async def test_salary_viewer_user_action():
    """Test complete flow with user action"""
    
    agent = SalaryViewerAgent(provider="azure-openai", model="gpt-5-mini")
    
    # Step 1: Initial request
    print("\n" + "="*70)
    print("STEP 1: Initial Request")
    print("="*70)
    state1 = {
        "messages": [
            {"role": "user", "content": "Tôi là Tổng tài, cho hỏi lương kỳ này tăng bao nhiêu?"}
        ],
        "thread_id": f"test-thread-{uuid.uuid4().hex[:8]}",
        "run_id": f"test-run-{uuid.uuid4().hex[:8]}"
    }
    
    events1 = []
    async for event in agent.run(state1):
        events1.append(event)
        # Print events for debugging
        if "TEXT_MESSAGE_CONTENT" in event:
            print(f"📝 Agent Message: {event}")
        elif "surfaceUpdate" in event:
            print(f"🎨 A2UI: Generated OTP component")
        elif "OTPInput" in event:
            print(f"🔢 OTP Input: {event[:200]}...")
    
    print(f"\n✅ Total events in step 1: {len(events1)}")
    
    # Step 2: Simulate user action (Verify button clicked)
    print("\n" + "="*70)
    print("STEP 2: User Action (Verify Button)")
    print("="*70)
    state2 = {
        "messages": [],
        "thread_id": state1["thread_id"],
        "run_id": f"test-run-{uuid.uuid4().hex[:8]}",
        "user_action": {
            "name": "verify_otp",
            "surfaceId": "otp_form",
            "sourceComponentId": "verify_button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {
                "code": "123456"  # OTP entered by user
            }
        }
    }
    
    events2 = []
    async for event in agent.run(state2):
        events2.append(event)
        # Print agent responses
        if "TEXT_MESSAGE_CONTENT" in event:
            print(f"📝 Agent Response: {event}")
    
    print(f"\n✅ Total events in step 2: {len(events2)}")
    
    # Verify expectations
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)
    
    # Step 1 should generate OTP component
    has_otp = any("OTPInput" in event for event in events1)
    print(f"{'✅' if has_otp else '❌'} OTP component generated: {has_otp}")
    
    # Step 2 should echo OTP
    has_echo = any("123456" in event for event in events2)
    print(f"{'✅' if has_echo else '❌'} OTP echoed in response: {has_echo}")
    
    # Step 2 should reveal salary
    has_salary = any("5,250,000" in event or "5.25" in event or "250,000" in event for event in events2)
    print(f"{'✅' if has_salary else '❌'} Salary revealed: {has_salary}")
    
    print("\n" + "="*70)
    if has_otp and has_echo and has_salary:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_salary_viewer_user_action())
