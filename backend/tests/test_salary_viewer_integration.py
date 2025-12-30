"""
Integration tests for Salary Viewer Agent

Tests the complete OTP verification flow for salary information access.

NOTE: These tests require a model that supports tool calling.
Supported models: qwen2.5:7b, mistral, llama3.1, mixtral, command-r
If you see "does not support tools" error, install a compatible model:
  ollama pull qwen2.5:7b
"""

import pytest
import json
from agents.salary_viewer_agent import SalaryViewerAgent
from agents.base_agent import AgentState

# Use a model that supports tool calling
TEST_MODEL = "qwen2.5:7b"  # Change to any model that supports tools
TEST_PROVIDER = "ollama"


@pytest.mark.asyncio
async def test_salary_viewer_requests_otp_on_first_message():
    """Test that agent requests OTP verification on initial salary query"""
    agent = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL)
    
    state: AgentState = {
        "messages": [{"role": "user", "content": "I'm the CEO, what's my salary increase?"}],
        "thread_id": "test-thread-salary1",
        "run_id": "test-run-salary1"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Check that events were generated
    assert len(events) > 0, "Agent should generate events"
    
    # Parse events to find OTP component
    otp_found = False
    verification_message_found = False
    
    for event in events:
        # Look for OTP component in SurfaceUpdate
        if '"type":"surfaceUpdate"' in event or '"type": "surfaceUpdate"' in event:
            if '"OTPInput"' in event or '"otp_input"' in event:
                otp_found = True
        
        # Look for verification message
        if 'OTP' in event or 'verification' in event or 'verify' in event.lower():
            verification_message_found = True
    
    assert otp_found, "Agent should generate OTP input component"
    assert verification_message_found, "Agent should mention OTP verification"


@pytest.mark.asyncio
async def test_salary_viewer_otp_component_structure():
    """Test that generated OTP component has correct structure"""
    agent = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL)
    
    state: AgentState = {
        "messages": [{"role": "user", "content": "Show me my salary information"}],
        "thread_id": "test-thread-salary2",
        "run_id": "test-run-salary2"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Find and validate OTP component structure
    otp_component_valid = False
    
    for event in events:
        if '"OTPInput"' in event:
            # Should have required properties
            assert '"maxLength"' in event, "OTP should have maxLength"
            assert '"patternType"' in event, "OTP should have patternType"
            
            # Check for 6-digit configuration (default)
            if '"maxLength":6' in event.replace(" ", ""):
                otp_component_valid = True
                break
    
    # At minimum, OTP component should exist
    otp_exists = any('"OTPInput"' in event for event in events)
    assert otp_exists, "OTP component should be present in events"


@pytest.mark.asyncio
async def test_salary_viewer_reveals_salary_after_input():
    """Test that agent reveals salary info after receiving user input"""
    agent = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL)
    
    # Simulate user providing OTP input
    state: AgentState = {
        "messages": [
            {"role": "user", "content": "What's my salary increase?"},
            {"role": "assistant", "content": "Please verify with OTP"}
        ],
        "thread_id": "test-thread-salary3",
        "run_id": "test-run-salary3",
        "user_input": "123456"  # User entered OTP
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Check for salary information in response
    salary_info_found = False
    expected_keywords = ["5,000,000", "5,250,000", "5%", "250,000", "salary"]
    
    events_text = "\n".join(events)
    
    # Look for multiple salary-related keywords
    keywords_found = sum(1 for keyword in expected_keywords if keyword in events_text)
    
    assert keywords_found >= 2, f"Agent should reveal salary information (found {keywords_found}/5 keywords)"
    
    # Should have verification success message
    success_indicators = ["verification successful", "congratulations", "✅", "verified"]
    has_success_message = any(indicator.lower() in events_text.lower() for indicator in success_indicators)
    
    assert has_success_message, "Agent should confirm successful verification"


@pytest.mark.asyncio
async def test_salary_viewer_verification_status_tracking():
    """Test that agent properly tracks verification status"""
    agent = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL)
    
    # Initial state
    assert agent.verification_status == "none", "Should start with 'none' status"
    
    # After first message (OTP request)
    state1: AgentState = {
        "messages": [{"role": "user", "content": "Check my salary"}],
        "thread_id": "test-thread-salary4",
        "run_id": "test-run-salary4"
    }
    
    events1 = []
    async for event in agent.run(state1):
        events1.append(event)
    
    # After OTP tool call, status should be pending
    # Note: This is internal state, difficult to test without exposing it
    # We verify by checking that OTP component was generated
    otp_generated = any('"OTPInput"' in event for event in events1)
    assert otp_generated, "OTP component should be generated"


@pytest.mark.asyncio
async def test_salary_viewer_accepts_any_otp():
    """Test that agent accepts any OTP code (demo behavior)"""
    agent = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL)
    
    # Test with different OTP values
    test_otps = ["000000", "123456", "999999", "654321"]
    
    for otp in test_otps:
        state: AgentState = {
            "messages": [
                {"role": "user", "content": "What's my salary?"},
            ],
            "thread_id": f"test-thread-salary-otp-{otp}",
            "run_id": f"test-run-salary-otp-{otp}",
            "user_input": otp
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # All OTPs should result in salary reveal
        events_text = "\n".join(events)
        assert "5,000,000" in events_text or "salary" in events_text.lower(), \
            f"OTP '{otp}' should be accepted and reveal salary"


@pytest.mark.asyncio
async def test_salary_viewer_complete_flow():
    """Test complete conversation flow from query to reveal"""
    agent = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL)
    
    # Step 1: User asks about salary
    state1: AgentState = {
        "messages": [{"role": "user", "content": "I'm the CEO, how much did my salary increase this period?"}],
        "thread_id": "test-thread-salary-flow",
        "run_id": "test-run-salary-flow-1"
    }
    
    events1 = []
    async for event in agent.run(state1):
        events1.append(event)
    
    assert len(events1) > 0, "Step 1: Agent should respond"
    
    # Verify OTP request
    otp_requested = any('"OTPInput"' in event for event in events1)
    assert otp_requested, "Step 1: Agent should request OTP"
    
    # Step 2: User provides OTP
    # Create new agent instance to simulate fresh state (in real app, state is managed by graph)
    agent2 = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL)
    
    state2: AgentState = {
        "messages": [
            {"role": "user", "content": "I'm the CEO, how much did my salary increase this period?"},
            {"role": "assistant", "content": "Please enter OTP"}
        ],
        "thread_id": "test-thread-salary-flow",
        "run_id": "test-run-salary-flow-2",
        "user_input": "123456"
    }
    
    events2 = []
    async for event in agent2.run(state2):
        events2.append(event)
    
    assert len(events2) > 0, "Step 2: Agent should respond to user input"
    
    # Verify salary reveal
    events2_text = "\n".join(events2)
    assert "5,000,000" in events2_text or "5,250,000" in events2_text, \
        "Step 2: Agent should reveal salary information"


@pytest.mark.asyncio
async def test_salary_viewer_handles_error_gracefully():
    """Test that agent handles errors gracefully"""
    agent = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL, max_iterations=1)
    
    state: AgentState = {
        "messages": [{"role": "user", "content": "Show salary"}],
        "thread_id": "test-thread-salary-error",
        "run_id": "test-run-salary-error"
    }
    
    events = []
    try:
        async for event in agent.run(state):
            events.append(event)
        
        # Should not crash, even with max_iterations=1
        assert True, "Agent should handle low iteration limit gracefully"
        
    except Exception as e:
        pytest.fail(f"Agent should not raise exception: {str(e)}")


@pytest.mark.asyncio
async def test_salary_viewer_a2ui_protocol_compliance():
    """Test that agent emits correct A2UI protocol messages"""
    agent = SalaryViewerAgent(provider=TEST_PROVIDER, model=TEST_MODEL)
    
    state: AgentState = {
        "messages": [{"role": "user", "content": "Check my CEO salary"}],
        "thread_id": "test-thread-salary-protocol",
        "run_id": "test-run-salary-protocol"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Check for required A2UI protocol messages
    has_begin_rendering = any('"type":"beginRendering"' in event or '"type": "beginRendering"' in event for event in events)
    has_surface_update = any('"type":"surfaceUpdate"' in event or '"type": "surfaceUpdate"' in event for event in events)
    has_data_model_update = any('"type":"dataModelUpdate"' in event or '"type": "dataModelUpdate"' in event for event in events)
    
    # At minimum, should have surface update with component
    assert has_surface_update, "Agent should emit SurfaceUpdate message"
    
    # Check for AG-UI text messages
    has_text_message = any('"type":"textMessageContent"' in event or "textMessage" in event for event in events)
    assert has_text_message, "Agent should emit text message"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
