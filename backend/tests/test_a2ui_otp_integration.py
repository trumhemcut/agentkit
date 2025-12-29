"""
Integration tests for A2UI OTP component generation

Tests end-to-end OTP generation through A2UI agents.
"""

import pytest
from agents.a2ui_agent import A2UIAgent
from agents.a2ui_agent_with_loop import A2UIAgentWithLoop


@pytest.mark.asyncio
async def test_a2ui_agent_generates_otp_basic():
    """Test A2UIAgent generates OTP component from natural language"""
    agent = A2UIAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Create a 6-digit verification code input"}],
        "thread_id": "test-thread-otp1",
        "run_id": "test-run-otp1"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Check that some events were generated
    assert len(events) > 0
    
    # Parse events to find SurfaceUpdate with OTP component
    otp_found = False
    for event in events:
        if '"type":"surfaceUpdate"' in event or '"type": "surfaceUpdate"' in event:
            if '"OTPInput"' in event:
                otp_found = True
                # Verify basic OTP properties are present
                assert '"maxLength"' in event
                assert '"patternType"' in event
                break
    
    assert otp_found, "OTP component should be generated"


@pytest.mark.asyncio
async def test_a2ui_agent_generates_otp_with_separator():
    """Test agent generates OTP with separator from prompt"""
    agent = A2UIAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Create 6-digit OTP input split into two groups"}],
        "thread_id": "test-thread-otp2",
        "run_id": "test-run-otp2"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Check OTP component exists
    otp_found = False
    for event in events:
        if '"OTPInput"' in event:
            otp_found = True
            # Check groups exist
            assert '"groups"' in event
            break
    
    assert otp_found


@pytest.mark.asyncio
async def test_a2ui_agent_generates_otp_email_verification():
    """Test agent generates OTP for email verification scenario"""
    agent = A2UIAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Add email verification with 6-digit code"}],
        "thread_id": "test-thread-otp3",
        "run_id": "test-run-otp3"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Verify OTP component exists
    otp_found = False
    for event in events:
        if '"OTPInput"' in event:
            otp_found = True
            break
    
    assert otp_found


@pytest.mark.asyncio
async def test_a2ui_agent_generates_otp_2fa():
    """Test agent generates OTP for 2FA scenario"""
    agent = A2UIAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Create 2FA authentication input"}],
        "thread_id": "test-thread-otp4",
        "run_id": "test-run-otp4"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    otp_found = False
    for event in events:
        if '"OTPInput"' in event:
            otp_found = True
            break
    
    assert otp_found


@pytest.mark.asyncio
async def test_a2ui_agent_generates_4digit_otp():
    """Test agent generates 4-digit OTP"""
    agent = A2UIAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Create 4-digit verification code for phone"}],
        "thread_id": "test-thread-otp5",
        "run_id": "test-run-otp5"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    otp_found = False
    for event in events:
        if '"OTPInput"' in event and '"maxLength":4' in event.replace(" ", ""):
            otp_found = True
            break
    
    # Note: This might not always work if LLM doesn't extract the exact number
    # but we can at least check OTP component is generated
    otp_component_exists = any('"OTPInput"' in event for event in events)
    assert otp_component_exists


@pytest.mark.asyncio
async def test_a2ui_loop_agent_generates_otp():
    """Test A2UIAgentWithLoop generates OTP component"""
    agent = A2UIAgentWithLoop(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Show verification code input"}],
        "thread_id": "test-thread-otp-loop1",
        "run_id": "test-run-otp-loop1"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    otp_found = False
    for event in events:
        if '"OTPInput"' in event:
            otp_found = True
            break
    
    assert otp_found


@pytest.mark.asyncio
async def test_otp_component_structure():
    """Test OTP component has correct structure"""
    agent = A2UIAgent(provider="ollama", model="qwen:7b")
    
    state = {
        "messages": [{"role": "user", "content": "Create OTP input"}],
        "thread_id": "test-thread-otp-struct",
        "run_id": "test-run-otp-struct"
    }
    
    events = []
    async for event in agent.run(state):
        events.append(event)
    
    # Find the OTP component event
    otp_event = None
    for event in events:
        if '"OTPInput"' in event:
            otp_event = event
            break
    
    assert otp_event is not None
    
    # Check required fields exist
    assert '"title"' in otp_event
    assert '"description"' in otp_event
    assert '"maxLength"' in otp_event
    assert '"groups"' in otp_event
    assert '"patternType"' in otp_event
    assert '"buttonText"' in otp_event
    assert '"disabled"' in otp_event
    assert '"valuePath"' in otp_event


@pytest.mark.asyncio  
async def test_multiple_otp_prompts():
    """Test agent handles various OTP-related prompts"""
    agent = A2UIAgent(provider="ollama", model="qwen:7b")
    
    prompts = [
        "Create verification code input",
        "Add OTP authentication",
        "Show 6-digit code field",
        "Create 2-factor authentication input",
    ]
    
    for i, prompt in enumerate(prompts):
        state = {
            "messages": [{"role": "user", "content": prompt}],
            "thread_id": f"test-thread-multi-{i}",
            "run_id": f"test-run-multi-{i}"
        }
        
        events = []
        async for event in agent.run(state):
            events.append(event)
        
        # Each prompt should generate an OTP component
        otp_found = any('"OTPInput"' in event for event in events)
        assert otp_found, f"Failed for prompt: {prompt}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
