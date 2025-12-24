"""
Test script for Agent Discovery API Endpoint

Tests the /api/agents endpoint
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_agents_endpoint():
    """Test the /api/agents endpoint"""
    print("Testing GET /api/agents endpoint")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/api/agents")
        
        # Check status code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Status code: 200 OK")
        
        # Parse response
        data = response.json()
        print(f"\n✓ Response received:")
        print(json.dumps(data, indent=2))
        
        # Validate response structure
        assert "agents" in data, "Response missing 'agents' field"
        assert "default" in data, "Response missing 'default' field"
        print("\n✓ Response has correct structure")
        
        # Validate agents list
        agents = data["agents"]
        assert len(agents) > 0, "No agents returned"
        print(f"\n✓ Found {len(agents)} agents")
        
        # Validate each agent has required fields
        required_fields = ["id", "name", "description", "icon", "sub_agents", "features"]
        for agent in agents:
            for field in required_fields:
                assert field in agent, f"Agent missing required field: {field}"
        print("✓ All agents have required fields")
        
        # Check for expected agents
        agent_ids = [agent["id"] for agent in agents]
        assert "chat" in agent_ids, "Chat agent not found"
        assert "canvas" in agent_ids, "Canvas agent not found"
        print("✓ Expected agents (chat, canvas) present")
        
        # Validate default agent
        assert data["default"] == "chat", f"Expected default 'chat', got {data['default']}"
        print("✓ Default agent is 'chat'")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print("Please start the backend server with: python main.py")
        return False
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_agents_endpoint()
    exit(0 if success else 1)
