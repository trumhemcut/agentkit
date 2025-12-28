"""
Tests for Insurance Supervisor Agent System

Tests the supervisor pattern with specialized agents for insurance domain.
"""

import pytest
from agents.insurance import (
    InsuranceSupervisorAgent,
    InsurancePolicyAgent,
    ClaimsAgent,
    QuotingAgent,
    CustomerSupportAgent
)
from graphs.insurance_supervisor_graph import create_insurance_supervisor_graph
from graphs.graph_factory import graph_factory
from agents.agent_registry import agent_registry


@pytest.mark.asyncio
async def test_supervisor_routing_policy_questions():
    """Test supervisor routes policy questions to policy agent"""
    supervisor = InsuranceSupervisorAgent()
    
    # Test English policy question
    result = supervisor._determine_agent("What are the benefits of life insurance?")
    assert result == "policy"
    
    # Test Vietnamese policy question
    result = supervisor._determine_agent("Quyền lợi bảo hiểm nhân thọ là gì?")
    assert result == "policy"
    
    # Test coverage question
    result = supervisor._determine_agent("What does the policy cover?")
    assert result == "policy"


@pytest.mark.asyncio
async def test_supervisor_routing_claims_questions():
    """Test supervisor routes claims questions to claims agent"""
    supervisor = InsuranceSupervisorAgent()
    
    # Test English claims question
    result = supervisor._determine_agent("How do I file a claim?")
    assert result == "claims"
    
    # Test Vietnamese claims question
    result = supervisor._determine_agent("Làm thế nào để yêu cầu bồi thường?")
    assert result == "claims"
    
    # Test claims status question
    result = supervisor._determine_agent("What is the status of my claim?")
    assert result == "claims"


@pytest.mark.asyncio
async def test_supervisor_routing_quoting_questions():
    """Test supervisor routes pricing/quote questions to quoting agent"""
    supervisor = InsuranceSupervisorAgent()
    
    # Test English quote question
    result = supervisor._determine_agent("How much does life insurance cost?")
    assert result == "quoting"
    
    # Test Vietnamese quote question
    result = supervisor._determine_agent("Bảo hiểm nhân thọ giá bao nhiêu?")
    assert result == "quoting"
    
    # Test price-related question
    result = supervisor._determine_agent("What is the premium for health insurance?")
    assert result == "quoting"
    
    # Test estimate question
    result = supervisor._determine_agent("Can you give me a quote?")
    assert result == "quoting"


@pytest.mark.asyncio
async def test_supervisor_routing_support_questions():
    """Test supervisor routes general questions to support agent"""
    supervisor = InsuranceSupervisorAgent()
    
    # Test general question
    result = supervisor._determine_agent("What is your office address?")
    assert result == "support"
    
    # Default to support for unclear questions
    result = supervisor._determine_agent("Hello")
    assert result == "support"
    
    # Test account-related question
    result = supervisor._determine_agent("I need to update my account information")
    assert result == "support"


@pytest.mark.asyncio
async def test_insurance_supervisor_graph_creation():
    """Test graph creation and structure"""
    graph = create_insurance_supervisor_graph(model="qwen:7b", provider="ollama")
    
    assert graph is not None
    # Graph should be compiled and ready to invoke


@pytest.mark.asyncio
async def test_graph_factory_registration():
    """Test insurance supervisor is registered in graph factory"""
    assert "insurance-supervisor" in graph_factory._graph_creators
    
    # Should be able to create graph via factory
    graph = graph_factory.create_graph("insurance-supervisor", model="qwen:7b")
    assert graph is not None


@pytest.mark.asyncio
async def test_agent_registry_registration():
    """Test insurance supervisor is registered in agent registry"""
    agent = agent_registry.get_agent("insurance-supervisor")
    
    assert agent is not None
    assert agent.id == "insurance-supervisor"
    assert agent.name == "Insurance Supervisor"
    assert agent.available is True
    assert len(agent.sub_agents) == 4
    assert "policy_agent" in agent.sub_agents
    assert "claims_agent" in agent.sub_agents
    assert "quoting_agent" in agent.sub_agents
    assert "support_agent" in agent.sub_agents


@pytest.mark.asyncio
async def test_insurance_supervisor_graph_execution():
    """Test full graph execution with policy question"""
    graph = create_insurance_supervisor_graph(model="qwen:7b", provider="ollama")
    
    state = {
        "messages": [
            {"role": "user", "content": "What types of life insurance do you offer?"}
        ],
        "thread_id": "test-thread",
        "run_id": "test-run"
    }
    
    events = []
    
    async def event_callback(event):
        events.append(event)
    
    config = {"configurable": {"event_callback": event_callback}}
    
    result = await graph.ainvoke(state, config)
    
    # Should have routed to policy agent
    assert result.get("selected_specialist") == "policy"
    
    # Should have collected events
    assert len(events) > 0


@pytest.mark.asyncio
async def test_specialized_agents_initialization():
    """Test all specialized agents can be initialized"""
    policy_agent = InsurancePolicyAgent(model="qwen:7b", provider="ollama")
    claims_agent = ClaimsAgent(model="qwen:7b", provider="ollama")
    quoting_agent = QuotingAgent(model="qwen:7b", provider="ollama")
    support_agent = CustomerSupportAgent(model="qwen:7b", provider="ollama")
    
    assert policy_agent.name == "Insurance Policy Expert"
    assert claims_agent.name == "Claims Processing Expert"
    assert quoting_agent.name == "Insurance Quoting Expert"
    assert support_agent.name == "Customer Support Specialist"


@pytest.mark.asyncio
async def test_supervisor_empty_message():
    """Test supervisor handles empty messages gracefully"""
    supervisor = InsuranceSupervisorAgent()
    
    state = {
        "messages": [],
        "thread_id": "test-thread",
        "run_id": "test-run"
    }
    
    events = []
    async for event in supervisor.run(state):
        events.append(event)
    
    # Should emit TEXT_MESSAGE events with greeting
    assert len(events) > 0


@pytest.mark.asyncio
async def test_supervisor_routing_with_multiple_keywords():
    """Test supervisor handles messages with multiple keywords"""
    supervisor = InsuranceSupervisorAgent()
    
    # Message with both policy and price keywords should route to quoting
    # since "price" appears more prominently for quoting
    result = supervisor._determine_agent("What is the price of health insurance policy?")
    assert result in ["quoting", "policy"]  # Both are valid routing decisions
    
    # Message with claims and policy keywords should route based on score
    result = supervisor._determine_agent("I need to file a claim for my policy coverage")
    assert result == "claims"  # Claims keywords should win


@pytest.mark.asyncio  
async def test_graph_execution_claims_routing():
    """Test full graph execution with claims question"""
    graph = create_insurance_supervisor_graph(model="qwen:7b", provider="ollama")
    
    state = {
        "messages": [
            {"role": "user", "content": "Tôi muốn yêu cầu bồi thường"}
        ],
        "thread_id": "test-thread-2",
        "run_id": "test-run-2"
    }
    
    events = []
    
    async def event_callback(event):
        events.append(event)
    
    config = {"configurable": {"event_callback": event_callback}}
    
    result = await graph.ainvoke(state, config)
    
    # Should have routed to claims agent
    assert result.get("selected_specialist") == "claims"
    
    # Should have collected events
    assert len(events) > 0


@pytest.mark.asyncio
async def test_graph_execution_quoting_routing():
    """Test full graph execution with quoting question"""
    graph = create_insurance_supervisor_graph(model="qwen:7b", provider="ollama")
    
    state = {
        "messages": [
            {"role": "user", "content": "How much does car insurance cost?"}
        ],
        "thread_id": "test-thread-3",
        "run_id": "test-run-3"
    }
    
    events = []
    
    async def event_callback(event):
        events.append(event)
    
    config = {"configurable": {"event_callback": event_callback}}
    
    result = await graph.ainvoke(state, config)
    
    # Should have routed to quoting agent
    assert result.get("selected_specialist") == "quoting"
    
    # Should have collected events
    assert len(events) > 0
