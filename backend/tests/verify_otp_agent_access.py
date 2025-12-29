"""
Quick verification that agents have access to OTP tool

This script verifies that both A2UI agents can access the OTP tool
and that it appears in their tool schemas.
"""

from agents.a2ui_agent import A2UIAgent
from agents.a2ui_agent_with_loop import A2UIAgentWithLoop


def verify_agent_has_otp_tool(agent_class, agent_name):
    """Verify agent has OTP tool in its tool registry"""
    print(f"\n{'=' * 60}")
    print(f"Verifying {agent_name}")
    print(f"{'=' * 60}")
    
    agent = agent_class(provider="ollama", model="qwen:7b")
    
    # Check tool registry
    otp_tool = agent.tool_registry.get_tool("create_otp_input")
    if otp_tool:
        print("✅ OTP tool found in registry")
    else:
        print("❌ OTP tool NOT found in registry")
        return False
    
    # Check tool schemas
    schemas = agent.tool_registry.get_tool_schemas()
    otp_schema = None
    for schema in schemas:
        if schema["function"]["name"] == "create_otp_input":
            otp_schema = schema
            break
    
    if otp_schema:
        print("✅ OTP tool in tool schemas")
        print(f"   Description: {otp_schema['function']['description'][:80]}...")
        
        # Check parameters
        params = otp_schema['function']['parameters']
        props = params['properties']
        print(f"   Parameters: {', '.join(props.keys())}")
    else:
        print("❌ OTP tool NOT in tool schemas")
        return False
    
    return True


if __name__ == "__main__":
    print("\n🔍 Verifying OTP Tool Access in A2UI Agents\n")
    
    # Verify both agents
    agent1_ok = verify_agent_has_otp_tool(A2UIAgent, "A2UIAgent")
    agent2_ok = verify_agent_has_otp_tool(A2UIAgentWithLoop, "A2UIAgentWithLoop")
    
    print(f"\n{'=' * 60}")
    if agent1_ok and agent2_ok:
        print("✅ SUCCESS: Both agents have access to OTP tool")
    else:
        print("❌ FAILURE: Some agents missing OTP tool")
    print(f"{'=' * 60}\n")
