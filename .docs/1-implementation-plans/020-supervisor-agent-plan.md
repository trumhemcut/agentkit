# Implementation Plan: Supervisor Agent for Insurance Domain

**Requirement**: Tạo một agent mới và graph để thể hiện supervisor pattern với chủ đề về bảo hiểm (insurance). Supervisor agent sẽ điều phối các specialized agents để xử lý các yêu cầu về bảo hiểm.

**Related Files**:
- Backend: `backend/agents/`, `backend/graphs/`, `backend/api/routes.py`, `backend/agents/agent_registry.py`
- Frontend: `frontend/components/`, `frontend/services/api.ts`, `frontend/types/agent.ts`

**Architecture**: Supervisor pattern - một supervisor agent trung tâm điều phối các specialized agents (insurance policy agent, claims processing agent, quoting agent, customer support agent).

---

## 1. Backend Tasks (LangGraph + AG-UI)

**Delegate to Backend Agent** - See [.github/agents/backend.agent.md](../../.github/agents/backend.agent.md)

### Task 1.1: Create Specialized Insurance Agents

**Files**: 
- `backend/agents/insurance/__init__.py` (NEW)
- `backend/agents/insurance/policy_agent.py` (NEW)
- `backend/agents/insurance/claims_agent.py` (NEW)
- `backend/agents/insurance/quoting_agent.py` (NEW)
- `backend/agents/insurance/support_agent.py` (NEW)
- `backend/agents/insurance/supervisor_agent.py` (NEW)

Create four specialized agents inheriting from `BaseAgent`:

#### 1.1.0 Create Insurance Package
**File**: `backend/agents/insurance/__init__.py`

Create package initialization file:

```python
"""Insurance Domain Agents Package"""

from .supervisor_agent import InsuranceSupervisorAgent
from .policy_agent import InsurancePolicyAgent
from .claims_agent import ClaimsAgent
from .quoting_agent import QuotingAgent
from .support_agent import CustomerSupportAgent

__all__ = [
    "InsuranceSupervisorAgent",
    "InsurancePolicyAgent",
    "ClaimsAgent",
    "QuotingAgent",
    "CustomerSupportAgent",
]
```

#### 1.1.1 Insurance Policy Agent
**File**: `backend/agents/insurance/policy_agent.py`

```python
"""
Insurance Policy Agent

Handles questions about insurance policies, coverage details, premiums, and benefits.
"""

import logging
from typing import AsyncGenerator
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory
from protocols.event_types import (
    TextMessageStartEvent,
    TextMessageContentEvent, 
    TextMessageEndEvent,
    ThinkingStartEvent,
    ThinkingContentEvent,
    ThinkingEndEvent
)

logger = logging.getLogger(__name__)


class InsurancePolicyAgent(BaseAgent):
    """Agent specialized in insurance policy information"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Insurance Policy Agent
        
        Args:
            model: Optional model name (e.g., 'qwen:7b')
            provider: Optional provider name (e.g., 'ollama', 'gemini', 'azure-openai')
        """
        self.model = model
        self.provider = provider
        self.llm_client = LLMProviderFactory.get_provider(provider).get_client(model)
        self.name = "Insurance Policy Expert"
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute policy agent logic with streaming"""
        logger.info(f"Insurance Policy Agent processing with model={self.model}, provider={self.provider}")
        
        try:
            # Emit thinking event
            yield ThinkingStartEvent()
            yield ThinkingContentEvent(content="Analyzing insurance policy question...")
            yield ThinkingEndEvent()
            
            # Prepare system prompt for policy expertise
            system_prompt = """You are an insurance policy expert. You help customers understand:
            - Different types of insurance policies (life, health, auto, home, etc.)
            - Coverage details and benefits
            - Premium calculations and payment options
            - Policy terms and conditions
            - Eligibility requirements
            
            Provide clear, accurate information about insurance policies. Use Vietnamese if the question is in Vietnamese.
            """
            
            # Prepare messages with system prompt
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(state.get("messages", []))
            
            # Stream response
            yield TextMessageStartEvent()
            
            async for chunk in self.llm_client.stream(messages):
                yield TextMessageContentEvent(content=chunk)
            
            yield TextMessageEndEvent()
            
        except Exception as e:
            logger.error(f"Error in Insurance Policy Agent: {str(e)}")
            raise
```

#### 1.1.2 Claims Processing Agent
**File**: `backend/agents/insurance/claims_agent.py`

```python
"""
Claims Processing Agent

Handles insurance claims questions, status checks, and claims procedures.
"""

import logging
from typing import AsyncGenerator
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory
from protocols.event_types import (
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ThinkingStartEvent,
    ThinkingContentEvent,
    ThinkingEndEvent
)

logger = logging.getLogger(__name__)


class ClaimsAgent(BaseAgent):
    """Agent specialized in insurance claims processing"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Claims Agent
        
        Args:
            model: Optional model name
            provider: Optional provider name
        """
        self.model = model
        self.provider = provider
        self.llm_client = LLMProviderFactory.get_provider(provider).get_client(model)
        self.name = "Claims Processing Expert"
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute claims agent logic with streaming"""
        logger.info(f"Claims Agent processing with model={self.model}, provider={self.provider}")
        
        try:
            # Emit thinking event
            yield ThinkingStartEvent()
            yield ThinkingContentEvent(content="Analyzing claims question...")
            yield ThinkingEndEvent()
            
            # Prepare system prompt for claims expertise
            system_prompt = """You are an insurance claims processing expert. You help customers with:
            - Filing insurance claims
            - Understanding claims procedures
            - Checking claims status
            - Required documentation for claims
            - Claims approval process
            - Claims rejection reasons and appeals
            
            Provide step-by-step guidance on claims processes. Use Vietnamese if the question is in Vietnamese.
            """
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(state.get("messages", []))
            
            # Stream response
            yield TextMessageStartEvent()
            
            async for chunk in self.llm_client.stream(messages):
                yield TextMessageContentEvent(content=chunk)
            
            yield TextMessageEndEvent()
            
        except Exception as e:
            logger.error(f"Error in Claims Agent: {str(e)}")
            raise
```

#### 1.1.3 Quoting Agent
**File**: `backend/agents/insurance/quoting_agent.py`

```python
"""
Quoting Agent

Handles insurance quotes, pricing calculations, and premium estimates.
"""

import logging
from typing import AsyncGenerator
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory
from protocols.event_types import (
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ThinkingStartEvent,
    ThinkingContentEvent,
    ThinkingEndEvent
)

logger = logging.getLogger(__name__)


class QuotingAgent(BaseAgent):
    """Agent specialized in insurance quotes and pricing"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Quoting Agent
        
        Args:
            model: Optional model name
            provider: Optional provider name
        """
        self.model = model
        self.provider = provider
        self.llm_client = LLMProviderFactory.get_provider(provider).get_client(model)
        self.name = "Insurance Quoting Expert"
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute quoting agent logic with streaming"""
        logger.info(f"Quoting Agent processing with model={self.model}, provider={self.provider}")
        
        try:
            # Emit thinking event
            yield ThinkingStartEvent()
            yield ThinkingContentEvent(content="Analyzing insurance quote request...")
            yield ThinkingEndEvent()
            
            # Prepare system prompt for quoting expertise
            system_prompt = """You are an insurance quoting expert. You help customers with:
            - Insurance premium calculations and estimates
            - Pricing based on customer information (age, occupation, coverage needs)
            - Comparing different insurance packages and their costs
            - Explaining factors that affect insurance premiums
            - Providing quote breakdowns and cost analysis
            - Recommending suitable insurance packages based on budget
            
            Ask relevant questions to provide accurate quotes. Use Vietnamese if the question is in Vietnamese.
            """
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(state.get("messages", []))
            
            # Stream response
            yield TextMessageStartEvent()
            
            async for chunk in self.llm_client.stream(messages):
                yield TextMessageContentEvent(content=chunk)
            
            yield TextMessageEndEvent()
            
        except Exception as e:
            logger.error(f"Error in Quoting Agent: {str(e)}")
            raise
```

#### 1.1.4 Customer Support Agent
**File**: `backend/agents/insurance/support_agent.py`

```python
"""
Customer Support Agent

Handles general customer support, account management, and basic inquiries.
"""

import logging
from typing import AsyncGenerator
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory
from protocols.event_types import (
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ThinkingStartEvent,
    ThinkingContentEvent,
    ThinkingEndEvent
)

logger = logging.getLogger(__name__)


class CustomerSupportAgent(BaseAgent):
    """Agent specialized in customer support"""
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Customer Support Agent
        
        Args:
            model: Optional model name
            provider: Optional provider name
        """
        self.model = model
        self.provider = provider
        self.llm_client = LLMProviderFactory.get_provider(provider).get_client(model)
        self.name = "Customer Support Specialist"
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute customer support agent logic with streaming"""
        logger.info(f"Customer Support Agent processing with model={self.model}, provider={self.provider}")
        
        try:
            # Emit thinking event
            yield ThinkingStartEvent()
            yield ThinkingContentEvent(content="Processing customer support request...")
            yield ThinkingEndEvent()
            
            # Prepare system prompt for customer support
            system_prompt = """You are a customer support specialist for an insurance company. You help customers with:
            - General inquiries about insurance services
            - Account management and updates
            - Contact information and office locations
            - Appointment scheduling
            - Frequently asked questions
            - Directing customers to specialized agents when needed
            
            Be friendly, helpful, and professional. Use Vietnamese if the question is in Vietnamese.
            """
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(state.get("messages", []))
            
            # Stream response
            yield TextMessageStartEvent()
            
            async for chunk in self.llm_client.stream(messages):
                yield TextMessageContentEvent(content=chunk)
            
            yield TextMessageEndEvent()
            
        except Exception as e:
            logger.error(f"Error in Customer Support Agent: {str(e)}")
            raise
```

**Requirements**:
- All agents inherit from `BaseAgent`
- Support model and provider parameters
- Emit AG-UI events (THINKING, TEXT_MESSAGE_START/CONTENT/END)
- Specialized system prompts for each domain
- Support Vietnamese language
- Proper error handling and logging

---

### Task 1.2: Create Supervisor Agent

**File**: `backend/agents/insurance/supervisor_agent.py` (NEW)

Create supervisor agent that orchestrates the four specialized agents:

```python
"""
Insurance Supervisor Agent

Orchestrates specialized insurance agents (policy, claims, customer support).
Uses LLM to decide which specialized agent should handle each query.
"""

import logging
from typing import AsyncGenerator, Dict, Any
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory
from protocols.event_types import (
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ThinkingStartEvent,
    ThinkingContentEvent,
    ThinkingEndEvent
)

logger = logging.getLogger(__name__)


class InsuranceSupervisorAgent(BaseAgent):
    """Supervisor agent that routes queries to specialized insurance agents"""
    
    # Define routing keywords for each agent
    AGENT_ROUTING = {
        "policy": [
            "policy", "coverage", "benefit", "bảo hiểm", "quyền lợi", 
            "gói bảo hiểm", "loại bảo hiểm", "điều khoản", "terms"
        ],
        "claims": [
            "claim", "bồi thường", "yêu cầu bồi thường", "giải quyết", "hồ sơ",
            "đền bù", "thủ tục bồi thường"
        ],
        "quoting": [
            "quote", "price", "cost", "báo giá", "giá", "phí", "premium",
            "tính phí", "chi phí", "bao nhiêu tiền", "how much", "estimate"
        ],
        "support": [
            "account", "contact", "office", "appointment", "help", "general",
            "tài khoản", "liên hệ", "văn phòng", "hẹn", "giúp đỡ"
        ]
    }
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Insurance Supervisor Agent
        
        Args:
            model: Optional model name
            provider: Optional provider name
        """
        self.model = model
        self.provider = provider
        self.llm_client = LLMProviderFactory.get_provider(provider).get_client(model)
        self.name = "Insurance Supervisor"
    
    def _determine_agent(self, message: str) -> str:
        """
        Determine which specialized agent should handle the query
        
        Args:
            message: User's message
            
        Returns:
            Agent identifier: 'policy', 'claims', 'quoting', or 'support'
        """
        message_lower = message.lower()
        
        # Count keyword matches for each agent
        scores = {
            "policy": 0,
            "claims": 0,
            "quoting": 0,
            "support": 0
        }
        
        for agent_type, keywords in self.AGENT_ROUTING.items():
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    scores[agent_type] += 1
        
        # Return agent with highest score, default to support
        max_score = max(scores.values())
        if max_score == 0:
            return "support"  # Default to support for general queries
        
        return max(scores, key=scores.get)
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute supervisor logic - route to appropriate specialized agent"""
        logger.info(f"Insurance Supervisor processing with model={self.model}, provider={self.provider}")
        
        try:
            # Get the last user message
            messages = state.get("messages", [])
            if not messages:
                yield TextMessageStartEvent()
                yield TextMessageContentEvent(content="Xin chào! Tôi có thể giúp gì cho bạn về bảo hiểm?")
                yield TextMessageEndEvent()
                return
            
            last_message = messages[-1].get("content", "")
            
            # Emit thinking event - supervisor is analyzing
            yield ThinkingStartEvent()
            yield ThinkingContentEvent(content="Phân tích câu hỏi và chọn chuyên gia phù hợp...")
            
            # Determine which agent to use
            selected_agent = self._determine_agent(last_message)
            
            agent_names = {
                "policy": "Chuyên gia Chính sách Bảo hiểm",
                "claims": "Chuyên gia Giải quyết Bồi thường",
                "quoting": "Chuyên gia Báo giá",
                "support": "Chuyên viên Hỗ trợ Khách hàng"
            }
            
            yield ThinkingContentEvent(
                content=f"Đang chuyển câu hỏi đến {agent_names[selected_agent]}..."
            )
            yield ThinkingEndEvent()
            
            # Store routing decision in state for graph to use
            state["selected_specialist"] = selected_agent
            
            # Supervisor can optionally provide context
            yield TextMessageStartEvent()
            yield TextMessageContentEvent(
                content=f"Tôi đã chuyển câu hỏi của bạn đến {agent_names[selected_agent]}. "
            )
            yield TextMessageEndEvent()
            
        except Exception as e:
            logger.error(f"Error in Insurance Supervisor: {str(e)}")
            raise
```

**Requirements**:
- Inherit from `BaseAgent`
- Analyze user query to determine appropriate specialized agent
- Use keyword matching and scoring for routing decisions
- Emit supervisor routing events
- Store routing decision in state for graph conditional routing
- Support both English and Vietnamese

---

### Task 1.3: Create Supervisor Graph

**File**: `backend/graphs/insurance_supervisor_graph.py` (NEW)

Create LangGraph workflow implementing supervisor pattern:

```python
"""
Insurance Supervisor Graph

LangGraph workflow implementing supervisor pattern for insurance domain.
Supervisor routes queries to specialized agents (policy, claims, support).
"""

import logging
from langgraph.graph import StateGraph, START, END
from typing import Literal
from agents.base_agent import AgentState
from agents.insurance import (
    InsuranceSupervisorAgent,
    InsurancePolicyAgent,
    ClaimsAgent,
    QuotingAgent,
    CustomerSupportAgent
)

logger = logging.getLogger(__name__)


def create_insurance_supervisor_graph(model: str = None, provider: str = None):
    """
    Create LangGraph workflow for insurance supervisor pattern
    
    Architecture:
        START → supervisor → [policy_agent | claims_agent | quoting_agent | support_agent] → END
    
    Args:
        model: Optional model name (e.g., 'qwen:7b')
        provider: Optional provider name (e.g., 'ollama', 'gemini')
    
    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(AgentState)
    
    # Initialize all agents with same model/provider
    supervisor = InsuranceSupervisorAgent(model=model, provider=provider)
    policy_agent = InsurancePolicyAgent(model=model, provider=provider)
    claims_agent = ClaimsAgent(model=model, provider=provider)
    quoting_agent = QuotingAgent(model=model, provider=provider)
    support_agent = CustomerSupportAgent(model=model, provider=provider)
    
    # Supervisor node
    async def supervisor_node(state: AgentState, config=None):
        """Supervisor analyzes query and determines routing"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in supervisor.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Policy agent node
    async def policy_node(state: AgentState, config=None):
        """Policy expert handles policy-related queries"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in policy_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Claims agent node
    async def claims_node(state: AgentState, config=None):
        """Claims expert handles claims-related queries"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in claims_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Quoting agent node
    async def quoting_node(state: AgentState, config=None):
        """Quoting expert handles pricing and quote requests"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in quoting_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Support agent node
    async def support_node(state: AgentState, config=None):
        """Support specialist handles general queries"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        async for event in support_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        return state
    
    # Routing function
    def route_to_specialist(state: AgentState) -> Literal["policy", "claims", "quoting", "support"]:
        """Route to appropriate specialist based on supervisor's decision"""
        selected = state.get("selected_specialist", "support")
        logger.info(f"Routing to specialist: {selected}")
        return selected
    
    # Build graph structure
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("policy", policy_node)
    workflow.add_node("claims", claims_node)
    workflow.add_node("quoting", quoting_node)
    workflow.add_node("support", support_node)
    
    # Define flow: START → supervisor → conditional routing to specialists → END
    workflow.add_edge(START, "supervisor")
    
    workflow.add_conditional_edges(
        "supervisor",
        route_to_specialist,
        {
            "policy": "policy",
            "claims": "claims",
            "quoting": "quoting",
            "support": "support"
        }
    )
    
    # All specialists end the workflow
    workflow.add_edge("policy", END)
    workflow.add_edge("claims", END)
    workflow.add_edge("quoting", END)
    workflow.add_edge("support", END)
    
    return workflow.compile()
```

**Requirements**:
- Implement supervisor pattern with conditional routing
- Create supervisor node and four specialist nodes (policy, claims, quoting, support)
- Use conditional edges for intelligent routing based on supervisor's decision
- Support streaming through event callbacks
- Pass model and provider to all agents
- Proper logging for debugging

---

### Task 1.4: Register Graph in Graph Factory

**File**: `backend/graphs/graph_factory.py`

Add the new insurance supervisor graph to the factory registry:

```python
# Add to imports
from graphs.insurance_supervisor_graph import create_insurance_supervisor_graph

class GraphFactory:
    """Factory for creating LangGraph workflows based on agent_id"""
    
    # Add to registry
    _graph_creators = {
        "chat": create_chat_graph,
        "canvas": create_canvas_graph,
        "a2ui": create_a2ui_graph,
        "insurance-supervisor": create_insurance_supervisor_graph,  # NEW
    }
```

**Requirements**:
- Import new graph creator function
- Register in `_graph_creators` dictionary with key `"insurance-supervisor"`

---

### Task 1.5: Register Agent in Agent Registry

**File**: `backend/agents/agent_registry.py`

Register the insurance supervisor agent in the agent registry:

```python
def _initialize_agents(self):
    # ... existing agents ...
    
    # Register Insurance Supervisor Agent
    self.register_agent(AgentMetadata(
        id="insurance-supervisor",
        name="Insurance Supervisor",
        description="Multi-agent system for insurance queries with specialized agents for policies, claims, quotes, and customer support",
        icon="shield",  # Insurance shield icon
        available=True,
        sub_agents=["policy_agent", "claims_agent", "quoting_agent", "support_agent"],
        features=["insurance", "supervisor-pattern", "multi-agent", "vietnamese", "quoting"]
    ))
```

**Requirements**:
- Use unique agent ID: `"insurance-supervisor"`
- Descriptive name and description
- List all sub-agents
- Mark as available
- Include relevant feature tags

---

### Task 1.6: Testing

**File**: `backend/tests/test_insurance_supervisor.py` (NEW)

Create comprehensive tests for the insurance supervisor system:

```python
"""
Tests for Insurance Supervisor Agent System
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
```

**Requirements**:
- Test supervisor routing logic for all agent types
- Test graph creation and compilation
- Test factory and registry registration
- Test full end-to-end graph execution
- Test Vietnamese language support
- Use pytest with async support

---

## 2. AG-UI Protocol (Communication Contract)

### Event Flow Specification

**Supervisor Flow**:
1. **RUN_STARTED** - Overall execution begins
2. **THINKING_START** - Supervisor analyzing query
3. **THINKING_CONTENT** - "Phân tích câu hỏi và chọn chuyên gia..."
4. **THINKING_CONTENT** - "Đang chuyển câu hỏi đến [Agent Name]..."
5. **THINKING_END** - Routing decision complete
6. **TEXT_MESSAGE_START** - Supervisor acknowledgment
7. **TEXT_MESSAGE_CONTENT** - Routing confirmation message
8. **TEXT_MESSAGE_END**
9. **THINKING_START** - Specialist agent begins processing
10. **THINKING_CONTENT** - Specialist analyzing specific domain
11. **THINKING_END**
12. **TEXT_MESSAGE_START** - Specialist response begins
13. **TEXT_MESSAGE_CONTENT** - Streamed specialist response
14. **TEXT_MESSAGE_END**
15. **RUN_FINISHED** - Overall execution complete

**State Contract**:
```typescript
interface InsuranceSupervisorState {
  messages: Message[];
  thread_id: string;
  run_id: string;
  selected_specialist?: "policy" | "claims" | "quoting" | "support";
}
```

**Metadata Fields**:
- `agent_name`: Current agent name (supervisor or specialist)
- `routing_decision`: Which specialist was selected
- `specialist_type`: Type of specialist handling the query

---

## 3. Frontend Tasks (AG-UI + React)

**Delegate to Frontend Agent** - See [.github/agents/frontend.agent.md](../../.github/agents/frontend.agent.md)

### Task 3.1: Add Insurance Supervisor to Agent List

**File**: `frontend/types/agent.ts`

Update TypeScript types for insurance supervisor:

```typescript
export interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
  available: boolean;
  sub_agents?: string[];
  features?: string[];
}

// Add insurance supervisor type
export type AgentId = "chat" | "canvas" | "a2ui" | "insurance-supervisor";

export interface InsuranceSupervisorMetadata {
  selected_specialist?: "policy" | "claims" | "quoting" | "support";
  specialist_name?: string;
}
```

---

### Task 3.2: Update Agent Selector Component

**File**: `frontend/components/AgentSelector.tsx`

Ensure insurance supervisor appears in agent selector with appropriate icon and description:

```tsx
// Component should automatically load from /agents endpoint
// Verify icon mapping includes "shield" icon for insurance
const iconMap = {
  "message-circle": MessageCircle,
  "layout": Layout,
  "component": Component,
  "shield": Shield,  // Add shield icon for insurance
};
```

---

### Task 3.3: Create Insurance Supervisor Indicator Component

**File**: `frontend/components/InsuranceSupervisorIndicator.tsx` (NEW)

Create component to show which specialist is handling the query:

```tsx
import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Shield, FileText, ClipboardList, DollarSign, Headphones } from 'lucide-react';

interface InsuranceSupervisorIndicatorProps {
  specialist?: 'policy' | 'claims' | 'quoting' | 'support';
  isActive?: boolean;
}

const specialistConfig = {
  policy: {
    name: 'Policy Expert',
    nameVi: 'Chuyên gia Chính sách',
    icon: FileText,
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  },
  claims: {
    name: 'Claims Expert',
    nameVi: 'Chuyên gia Bồi thường',
    icon: ClipboardList,
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  },
  quoting: {
    name: 'Quoting Expert',
    nameVi: 'Chuyên gia Báo giá',
    icon: DollarSign,
    color: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
  },
  support: {
    name: 'Customer Support',
    nameVi: 'Hỗ trợ Khách hàng',
    icon: Headphones,
    color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
  }
};

export function InsuranceSupervisorIndicator({ 
  specialist, 
  isActive = false 
}: InsuranceSupervisorIndicatorProps) {
  if (!specialist) {
    return (
      <Badge variant="outline" className="gap-1">
        <Shield className="h-3 w-3" />
        Insurance Supervisor
      </Badge>
    );
  }

  const config = specialistConfig[specialist];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className="gap-1">
        <Shield className="h-3 w-3" />
        Supervisor
      </Badge>
      <span className="text-xs text-muted-foreground">→</span>
      <Badge className={`gap-1 ${config.color}`}>
        <Icon className="h-3 w-3" />
        {config.nameVi}
      </Badge>
      {isActive && (
        <span className="inline-flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
      )}
    </div>
  );
}
```

---

### Task 3.4: Update Chat Interface to Show Specialist Routing

**File**: `frontend/components/AgentMessageBubble.tsx`

Update message bubble to show which specialist is responding:

```tsx
import { InsuranceSupervisorIndicator } from './InsuranceSupervisorIndicator';

// In the message rendering:
{message.agent_id === 'insurance-supervisor' && (
  <InsuranceSupervisorIndicator 
    specialist={message.metadata?.selected_specialist}
    isActive={message.is_streaming}
  />
)}
```

---

### Task 3.5: Update API Service

**File**: `frontend/services/api.ts`

Ensure API service supports insurance-supervisor agent:

```typescript
// Should already support any agent_id dynamically
// Verify no hardcoded agent checks that would block insurance-supervisor

export async function* streamAgentChat(
  agentId: string,  // Now includes "insurance-supervisor"
  threadId: string,
  runId: string,
  messages: Message[],
  model?: string,
  provider?: string
): AsyncGenerator<AgentEvent> {
  // Existing implementation should work
  // ...
}
```

---

### Task 3.6: Add Insurance Supervisor UI Tests

**File**: `frontend/tests/insurance-supervisor.test.tsx` (NEW)

Create tests for insurance supervisor UI components:

```typescript
import { render, screen } from '@testing-library/react';
import { InsuranceSupervisorIndicator } from '@/components/InsuranceSupervisorIndicator';

describe('InsuranceSupervisorIndicator', () => {
  it('renders supervisor badge when no specialist selected', () => {
    render(<InsuranceSupervisorIndicator />);
    expect(screen.getByText('Insurance Supervisor')).toBeInTheDocument();
  });

  it('renders policy specialist badge', () => {
    render(<InsuranceSupervisorIndicator specialist="policy" />);
    expect(screen.getByText('Chuyên gia Chính sách')).toBeInTheDocument();
  });

  it('renders claims specialist badge', () => {
    render(<InsuranceSupervisorIndicator specialist="claims" />);
    expect(screen.getByText('Chuyên gia Bồi thường')).toBeInTheDocument();
  });

  it('renders quoting specialist badge', () => {
    render(<InsuranceSupervisorIndicator specialist="quoting" />);
    expect(screen.getByText('Chuyên gia Báo giá')).toBeInTheDocument();
  });

  it('renders support specialist badge', () => {
    render(<InsuranceSupervisorIndicator specialist="support" />);
    expect(screen.getByText('Hỗ trợ Khách hàng')).toBeInTheDocument();
  });

  it('shows active indicator when isActive is true', () => {
    render(<InsuranceSupervisorIndicator specialist="policy" isActive={true} />);
    const indicator = screen.getByRole('status', { hidden: true });
    expect(indicator).toHaveClass('animate-pulse');
  });
});
```

---

## 4. Integration & Testing Flow

### 4.1 Backend Integration Testing

**Test Sequence**:
1. Start FastAPI server
2. Test graph factory can create insurance-supervisor graph
3. Test agent registry lists insurance-supervisor agent
4. Test `/agents` endpoint returns insurance-supervisor
5. Test `/chat/insurance-supervisor` endpoint with various queries:
   - Policy questions (English & Vietnamese)
   - Claims questions (English & Vietnamese)
   - Support questions (English & Vietnamese)
6. Verify correct routing to specialists
7. Verify streaming events are emitted correctly

**Manual Test Commands**:
```bash
# Test agent discovery
curl http://localhost:8000/agents

# Test policy routing
curl -X POST http://localhost:8000/chat/insurance-supervisor \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"test","run_id":"test","messages":[{"role":"user","content":"What life insurance policies do you offer?"}],"model":"qwen:7b"}'

# Test claims routing (Vietnamese)
curl -X POST http://localhost:8000/chat/insurance-supervisor \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"test","run_id":"test","messages":[{"role":"user","content":"Làm thế nào để yêu cầu bồi thường?"}],"model":"qwen:7b"}'

# Test quoting routing (Vietnamese)
curl -X POST http://localhost:8000/chat/insurance-supervisor \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"test","run_id":"test","messages":[{"role":"user","content":"Bảo hiểm nhân thọ giá bao nhiêu?"}],"model":"qwen:7b"}'
```

---

### 4.2 Frontend Integration Testing

**Test Sequence**:
1. Start frontend dev server
2. Verify insurance-supervisor appears in agent selector
3. Select insurance-supervisor agent
4. Test various queries:
   - Ask about insurance policies
   - Ask about claims
   - Ask about quotes/pricing
   - Ask general support questions
5. Verify specialist routing indicator appears
6. Verify correct specialist badge is shown
7. Verify streaming works correctly
8. Test both English and Vietnamese

---

### 4.3 End-to-End Testing

**User Scenarios**:

**Scenario 1: Policy Question**
1. User selects "Insurance Supervisor" agent
2. User asks: "What are the benefits of life insurance?"
3. UI shows: Supervisor → Policy Expert
4. Response explains life insurance benefits

**Scenario 2: Claims Question (Vietnamese)**
1. User asks: "Tôi muốn yêu cầu bồi thường tai nạn"
2. UI shows: Supervisor → Chuyên gia Bồi thường
3. Response explains claims process in Vietnamese

**Scenario 3: Quoting Question**
1. User asks: "How much does health insurance cost for a 30-year-old?"
2. UI shows: Supervisor → Quoting Expert
3. Response asks follow-up questions and provides pricing estimate

**Scenario 4: General Support**
1. User asks: "Where is your office?"
2. UI shows: Supervisor → Customer Support
3. Response provides office information

---

## 5. Dependencies & Prerequisites

### Backend Dependencies
- All dependencies already exist in `requirements.txt`
- LangGraph for workflow orchestration
- FastAPI for API endpoints
- Ollama/Gemini/Azure OpenAI for LLM providers

### Frontend Dependencies
- All dependencies already exist in `package.json`
- React for UI components
- Shadcn UI for component library
- TypeScript for type safety

### No New Dependencies Required
All required libraries and frameworks are already in the project.

---

## 6. Documentation Updates

### 6.1 Update Knowledge Base

**File**: `.docs/2-knowledge-base/agents/insurance-supervisor.md` (NEW)

Create documentation for insurance supervisor pattern:
- Architecture overview
- Supervisor pattern explanation
- Routing logic
- Specialized agent descriptions
- Usage examples
- Vietnamese language support

### 6.2 Update Backend README

**File**: `backend/README.md`

Add section about insurance supervisor agent:
- Multi-agent architecture
- Supervisor pattern implementation
- Specialized agents overview

### 6.3 Update Frontend README

**File**: `frontend/README.md`

Add section about supervisor UI components:
- InsuranceSupervisorIndicator component
- Specialist routing visualization

---

## 7. Timeline & Priorities

### Phase 1: Core Backend (High Priority)
- **Task 1.1**: Create specialized agents (2-3 hours)
- **Task 1.2**: Create supervisor agent (1-2 hours)
- **Task 1.3**: Create supervisor graph (1-2 hours)
- **Task 1.4-1.5**: Register in factory and registry (30 min)

### Phase 2: Testing & Validation (High Priority)
- **Task 1.6**: Backend testing (1-2 hours)
- Integration testing (1 hour)

### Phase 3: Frontend UI (Medium Priority)
- **Task 3.1-3.2**: Type updates and agent selector (30 min)
- **Task 3.3**: Create supervisor indicator (1 hour)
- **Task 3.4**: Update message bubble (30 min)
- **Task 3.6**: Frontend testing (1 hour)

### Phase 4: Documentation (Low Priority)
- **Task 6.1-6.3**: Documentation updates (1-2 hours)

**Total Estimated Time**: 10-15 hours

---

## 8. Success Criteria

✅ **Backend**:
- [ ] Three specialized agents created and functional
- [ ] Supervisor agent routes queries correctly
- [ ] Graph implements proper conditional routing
- [ ] All agents registered in factory and registry
- [ ] All backend tests pass
- [ ] Vietnamese language support works

✅ **Frontend**:
- [ ] Insurance supervisor appears in agent selector
- [ ] Specialist routing indicator displays correctly
- [ ] Message bubbles show which specialist is responding
- [ ] Streaming works properly
- [ ] All frontend tests pass

✅ **Integration**:
- [ ] End-to-end scenarios work correctly
- [ ] Both English and Vietnamese supported
- [ ] Proper event streaming throughout the flow
- [ ] Documentation is complete

---

## 9. Future Enhancements

### Potential Improvements:
1. **Advanced LLM-Based Routing**: Replace keyword matching with LLM-based routing decisions
2. **Sub-Agent Communication**: Allow specialists to consult with each other
3. **Multi-Level Hierarchy**: Add more specialized agents (health insurance, auto insurance, etc.)
4. **Tools Integration**: Add real tools for policy lookup, claims status checking
5. **Memory**: Add conversation memory across sessions
6. **Analytics**: Track which specialists handle most queries
7. **A/B Testing**: Compare routing algorithms

---

## References

- [LangGraph Supervisor Documentation](https://github.com/langchain-ai/langgraph-supervisor-py)
- [LangGraph Multi-Agent Patterns](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
- [Backend Agent Guide](../../.github/agents/backend.agent.md)
- [Frontend Agent Guide](../../.github/agents/frontend.agent.md)
- [Graph Factory Pattern](../../.docs/2-knowledge-base/langgraph-architecture.md)
