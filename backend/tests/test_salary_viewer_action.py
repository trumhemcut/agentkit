"""
Integration tests for Salary Viewer Agent with User Action handling
"""

import pytest
import uuid
from agents.salary_viewer_agent import SalaryViewerAgent


@pytest.mark.asyncio
async def test_salary_viewer_initial_request_generates_otp():
    """Test that initial request generates OTP component"""
    agent = SalaryViewerAgent(provider="azure-openai", model="gpt-5-mini")
    
    state = {
        "messages": [
            {"role": "user", "content": "I'm the CEO, what's my salary?"}
        ],
        "thread_id": "test-thread-1",
        "run_id": "test-run-1"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should generate OTP component
    has_otp = any("OTPInput" in event for event in events)
    assert has_otp, "OTP component should be generated"
    
    # Should send confirmation message
    has_confirmation = any(
        "verification" in event.lower() or "otp" in event.lower() 
        for event in events
    )
    assert has_confirmation, "Should send confirmation message"


@pytest.mark.asyncio
async def test_salary_viewer_handles_verify_action():
    """Test that agent handles verify_otp user action"""
    agent = SalaryViewerAgent(provider="azure-openai", model="gpt-5-mini")
    
    state = {
        "messages": [],
        "thread_id": "test-thread-2",
        "run_id": "test-run-2",
        "user_action": {
            "name": "verify_otp",
            "surfaceId": "otp_form",
            "sourceComponentId": "verify_button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {
                "code": "999888"
            }
        }
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should echo OTP back
    has_echo = any("999888" in event for event in events)
    assert has_echo, "Agent should echo the OTP code"
    
    # Should reveal salary info
    has_salary = any(
        "5,250,000" in event or "5.25" in event or "salary" in event.lower()
        for event in events
    )
    assert has_salary, "Agent should reveal salary information"


@pytest.mark.asyncio
async def test_salary_viewer_handles_invalid_action():
    """Test that agent handles invalid user actions gracefully"""
    agent = SalaryViewerAgent(provider="azure-openai", model="gpt-5-mini")
    
    state = {
        "messages": [],
        "thread_id": "test-thread-3",
        "run_id": "test-run-3",
        "user_action": {
            "name": "unknown_action",
            "surfaceId": "form",
            "sourceComponentId": "button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {}
        }
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should send error message
    has_error = any("error" in event.lower() or "invalid" in event.lower() for event in events)
    assert has_error, "Agent should handle invalid actions gracefully"


@pytest.mark.asyncio
async def test_salary_viewer_handles_missing_otp():
    """Test that agent handles verify action without OTP code"""
    agent = SalaryViewerAgent(provider="azure-openai", model="gpt-5-mini")
    
    state = {
        "messages": [],
        "thread_id": "test-thread-4",
        "run_id": "test-run-4",
        "user_action": {
            "name": "verify_otp",
            "surfaceId": "otp_form",
            "sourceComponentId": "verify_button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {}  # No code provided
        }
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should send error message
    has_error = any("error" in event.lower() or "invalid" in event.lower() for event in events)
    assert has_error, "Agent should handle missing OTP code"


@pytest.mark.asyncio
async def test_salary_viewer_echo_message_format():
    """Test that OTP echo message is properly formatted"""
    agent = SalaryViewerAgent(provider="azure-openai", model="gpt-5-mini")
    
    state = {
        "messages": [],
        "thread_id": f"test-thread-{uuid.uuid4().hex[:8]}",
        "run_id": f"test-run-{uuid.uuid4().hex[:8]}",
        "user_action": {
            "name": "verify_otp",
            "surfaceId": "otp_form",
            "sourceComponentId": "verify_button",
            "timestamp": "2026-01-01T10:00:00Z",
            "context": {
                "code": "654321"
            }
        }
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Should echo with markdown formatting
    has_bold_otp = any("**654321**" in event for event in events)
    assert has_bold_otp, "OTP should be in bold markdown format"
    
    # Should contain emoji
    has_emoji = any("📩" in event for event in events)
    assert has_emoji, "Echo message should contain emoji"
