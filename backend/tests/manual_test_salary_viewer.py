"""
Manual Test for Salary Viewer Agent

This script demonstrates the salary viewer agent functionality.
It shows how the agent works without needing actual LLM tool calling support.

To test with actual LLM tool calling:
1. Install a model that supports tools: ollama pull qwen2.5:7b
2. Update TEST_MODEL in test_salary_viewer_integration.py
3. Run: pytest tests/test_salary_viewer_integration.py -v
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.salary_viewer_agent import SalaryViewerAgent
from agents.base_agent import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_manual_salary_viewer():
    """
    Manual test demonstrating salary viewer agent structure.
    
    This doesn't require a tool-capable model since we're just
    verifying the agent can be instantiated and has the correct structure.
    """
    print("\n" + "=" * 60)
    print("SALARY VIEWER AGENT - MANUAL TEST")
    print("=" * 60 + "\n")
    
    # Create agent
    print("1. Creating Salary Viewer Agent...")
    agent = SalaryViewerAgent(provider="ollama", model="qwen:7b")
    print(f"   ✓ Agent created")
    print(f"   - Provider: {agent.provider_name}")
    print(f"   - Model: {agent.model}")
    print(f"   - Max iterations: {agent.max_iterations}")
    print(f"   - Verification status: {agent.verification_status}")
    
    # Check tool registry
    print("\n2. Checking Tool Registry...")
    tools = agent.tool_registry.get_all_tools()
    print(f"   ✓ Available tools: {len(tools)}")
    for tool in tools:
        print(f"     - {tool.name}")
        if tool.name == "create_otp_input":
            print(f"       (This is the OTP tool used for verification)")
    
    # Check system prompt
    print("\n3. Verifying System Prompt...")
    from agents.salary_viewer_agent import SYSTEM_PROMPT
    print(f"   ✓ System prompt configured")
    print(f"   - Length: {len(SYSTEM_PROMPT)} characters")
    print(f"   - Contains 'OTP': {'OTP' in SYSTEM_PROMPT}")
    print(f"   - Contains 'salary': {'salary' in SYSTEM_PROMPT}")
    print(f"   - Contains '5,000,000': {'5,000,000' in SYSTEM_PROMPT}")
    
    # Show expected flow
    print("\n4. Expected User Flow:")
    print("   a) User: 'I'm the CEO, what's my salary increase?'")
    print("   b) Agent: Requests OTP verification")
    print("   c) Agent: Generates OTP input component")
    print("   d) User: Enters 6-digit code (any code accepted)")
    print("   e) Agent: Reveals salary information:")
    print("      - Original: 5,000,000 VND")
    print("      - Increase: 5%")
    print("      - New: 5,250,000 VND")
    
    # Test user input handling
    print("\n5. Testing User Input Handling...")
    state_with_input: AgentState = {
        "messages": [
            {"role": "user", "content": "What's my salary?"},
        ],
        "thread_id": "test-thread",
        "run_id": "test-run",
        "user_input": "123456"  # Simulated OTP input
    }
    
    print("   Simulating OTP input: 123456")
    
    try:
        events = []
        async for event in agent.run(state_with_input):
            events.append(event)
        
        print(f"   ✓ Agent processed input and generated {len(events)} events")
        
        # Check for salary info in events
        events_text = "\n".join(events)
        has_salary_info = "5,000,000" in events_text or "5,250,000" in events_text
        
        if has_salary_info:
            print("   ✓ Salary information revealed in response")
        else:
            print("   ℹ Salary info not found (model may not support tools)")
            
    except Exception as e:
        print(f"   ℹ Expected error (model doesn't support tools): {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("MANUAL TEST COMPLETE")
    print("=" * 60)
    print("\nNote: To test with actual LLM tool calling:")
    print("1. Install tool-capable model: ollama pull qwen2.5:7b")
    print("2. Run: pytest tests/test_salary_viewer_integration.py -v")
    print("")


if __name__ == "__main__":
    asyncio.run(test_manual_salary_viewer())
