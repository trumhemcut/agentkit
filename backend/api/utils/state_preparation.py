"""
State Preparation Utilities

Functions for preparing initial state for different agent types.
"""
import logging
from api.models import RunAgentInput

logger = logging.getLogger(__name__)


def prepare_state_for_agent(agent_id: str, input_data: RunAgentInput) -> dict:
    """
    Prepare initial state dictionary for graph execution
    
    Args:
        agent_id: Agent identifier ("chat", "canvas", etc.)
        input_data: Request data with messages, thread_id, run_id
        
    Returns:
        State dict matching the agent's StateGraph schema
    """
    # Base state for all agents
    state = {
        "messages": [
            {"role": msg.role, "content": msg.content} 
            for msg in input_data.messages
        ],
        "thread_id": input_data.thread_id,
        "run_id": input_data.run_id
    }
    
    # Agent-specific state extensions
    if agent_id == "canvas":
        # Canvas agent needs additional artifact state
        selected_text_data = input_data.selectedText.model_dump() if input_data.selectedText else None
        
        # Diagnostic logging for selection tracking
        if selected_text_data:
            logger.info(f"[STATE_PREP] Received selectedText in request: start={selected_text_data.get('start')}, end={selected_text_data.get('end')}")
            logger.info(f"[STATE_PREP] Selected text preview: '{selected_text_data.get('text', '')[:100]}...'")
        else:
            logger.debug(f"[STATE_PREP] No selectedText in request")
        
        state.update({
            "artifact": input_data.artifact.model_dump() if input_data.artifact else None,
            "selectedText": selected_text_data,
            "artifact_id": input_data.artifact_id,
            "artifactAction": input_data.action  # Will be detected by canvas graph if None
        })
        
        logger.debug(f"[STATE_PREP] Canvas state prepared with artifact_id={input_data.artifact_id}, action={input_data.action}")
    
    return state
