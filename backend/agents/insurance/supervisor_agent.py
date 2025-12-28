"""
Insurance Supervisor Agent

Orchestrates specialized insurance agents (policy, claims, quoting, customer support).
Uses keyword matching to decide which specialized agent should handle each query.
"""

import uuid
import logging
from typing import AsyncGenerator, Dict, Any
from ag_ui.core import (
    EventType,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ThinkingStartEvent,
    ThinkingTextMessageContentEvent as ThinkingContentEvent,
    ThinkingEndEvent
)
from agents.base_agent import BaseAgent, AgentState
from llm.provider_factory import LLMProviderFactory

logger = logging.getLogger(__name__)


class InsuranceSupervisorAgent(BaseAgent):
    """Supervisor agent that routes queries to specialized insurance agents"""
    
    # Define routing keywords for each agent with priority weights
    AGENT_ROUTING = {
        "policy": [
            "policy", "policies", "coverage", "benefit", "benefits", "quyền lợi", 
            "gói bảo hiểm", "loại bảo hiểm", "điều khoản", "terms", "types", "offer",
            "plan", "plans"
        ],
        "claims": [
            "claim", "claims", "bồi thường", "yêu cầu bồi thường", "giải quyết", "hồ sơ",
            "đền bù", "thủ tục bồi thường", "file a claim", "file", "filing"
        ],
        "quoting": [
            "quote", "quotes", "price", "prices", "cost", "costs", "báo giá", "giá", "phí", "premium",
            "tính phí", "chi phí", "bao nhiêu tiền", "how much", "estimate",
            "bao nhiêu", "pricing"
        ],
        "support": [
            "account", "contact", "office", "appointment", "help", "general",
            "tài khoản", "liên hệ", "văn phòng", "hẹn", "giúp đỡ", "hello", "hi"
        ]
    }
    
    def __init__(self, model: str = None, provider: str = None):
        """
        Initialize Insurance Supervisor Agent
        
        Args:
            model: Optional model name
            provider: Optional provider name
        """
        self.provider = provider or "ollama"
        self.model = model or "qwen:7b"
        provider_instance = LLMProviderFactory.get_provider(self.provider, self.model)
        self.llm = provider_instance.get_model()
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
        
        # If there's a tie, prioritize in order: quoting > claims > policy > support
        priority_order = ["quoting", "claims", "policy", "support"]
        candidates = [agent for agent in priority_order if scores[agent] == max_score]
        
        return candidates[0]
    
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute supervisor logic - route to appropriate specialized agent"""
        logger.info(f"Insurance Supervisor processing with model={self.model}, provider={self.provider}")
        
        try:
            message_id = str(uuid.uuid4())
            
            # Get the last user message
            messages = state.get("messages", [])
            if not messages:
                yield TextMessageStartEvent(
                    type=EventType.TEXT_MESSAGE_START,
                    message_id=message_id,
                    role="assistant"
                )
                yield TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    message_id=message_id,
                    delta="Xin chào! Tôi có thể giúp gì cho bạn về bảo hiểm?"
                )
                yield TextMessageEndEvent(
                    type=EventType.TEXT_MESSAGE_END,
                    message_id=message_id
                )
                return
            
            last_message = messages[-1].get("content", "")
            
            # Emit thinking event - supervisor is analyzing
            yield ThinkingStartEvent(
                type=EventType.THINKING_START,
                message_id=message_id
            )
            yield ThinkingContentEvent(
                type=EventType.THINKING_TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta="Phân tích câu hỏi và chọn chuyên gia phù hợp..."
            )
            
            # Determine which agent to use
            selected_agent = self._determine_agent(last_message)
            
            agent_names = {
                "policy": "Chuyên gia Chính sách Bảo hiểm",
                "claims": "Chuyên gia Giải quyết Bồi thường",
                "quoting": "Chuyên gia Báo giá",
                "support": "Chuyên viên Hỗ trợ Khách hàng"
            }
            
            yield ThinkingContentEvent(
                type=EventType.THINKING_TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=f"Đang chuyển câu hỏi đến {agent_names[selected_agent]}..."
            )
            yield ThinkingEndEvent(
                type=EventType.THINKING_END,
                message_id=message_id
            )
            
            # Store routing decision in state for graph to use
            state["selected_specialist"] = selected_agent
            
            # Supervisor can optionally provide context
            yield TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message_id,
                role="assistant"
            )
            yield TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=message_id,
                delta=f"Tôi đã chuyển câu hỏi của bạn đến {agent_names[selected_agent]}. "
            )
            yield TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END,
                message_id=message_id
            )
            
        except Exception as e:
            logger.error(f"Error in Insurance Supervisor: {str(e)}")
            raise
