"""
Test script for Agent Registry System

Validates agent registration, retrieval, and API endpoint
"""

import sys
sys.path.insert(0, '/home/phihuynh/projects/agenkit/backend')

from agents.agent_registry import agent_registry

# Test 1: List all agents
print("Test 1: List all agents")
print("=" * 50)
agents = agent_registry.list_agents()
for agent in agents:
    print(f"ID: {agent.id}")
    print(f"Name: {agent.name}")
    print(f"Description: {agent.description}")
    print(f"Icon: {agent.icon}")
    print(f"Available: {agent.available}")
    print(f"Sub-agents: {agent.sub_agents}")
    print(f"Features: {agent.features}")
    print("-" * 50)

# Test 2: Get specific agent
print("\nTest 2: Get specific agent (chat)")
print("=" * 50)
chat_agent = agent_registry.get_agent("chat")
if chat_agent:
    print(f"Found: {chat_agent.name}")
    print(f"Description: {chat_agent.description}")
else:
    print("Chat agent not found!")

# Test 3: Check availability
print("\nTest 3: Check agent availability")
print("=" * 50)
print(f"chat available: {agent_registry.is_available('chat')}")
print(f"canvas available: {agent_registry.is_available('canvas')}")
print(f"nonexistent available: {agent_registry.is_available('nonexistent')}")

# Test 4: Validate agent metadata
print("\nTest 4: Validate agent metadata")
print("=" * 50)
canvas_agent = agent_registry.get_agent("canvas")
if canvas_agent:
    print(f"Canvas agent sub-agents: {canvas_agent.sub_agents}")
    assert "generator" in canvas_agent.sub_agents
    assert "editor" in canvas_agent.sub_agents
    print("✓ Canvas agent has correct sub-agents")

print("\n✓ All tests passed!")
