import logging
from typing import TypedDict, Optional, List, Dict
from langgraph.graph import StateGraph, START, END

logger = logging.getLogger(__name__)


def prepare_canvas_state(state: "CanvasGraphState") -> "CanvasGraphState":
    """
    Prepare canvas state by handling artifact retrieval from cache
    
    This node resolves artifact_id to full artifact object if needed.
    """
    from cache.artifact_cache import artifact_cache
    
    artifact_id = state.get("artifact_id")
    artifact = state.get("artifact")
    
    # If artifact_id is provided but no artifact, try to retrieve from cache
    if artifact_id and not artifact:
        cached_artifact = artifact_cache.get(artifact_id)
        if cached_artifact:
            logger.info(f"Retrieved artifact from cache: {artifact_id}")
            state["artifact"] = cached_artifact
        else:
            logger.warning(f"Artifact ID provided but not found in cache: {artifact_id}")
    elif artifact:
        logger.info("Client sent full artifact object")
    
    return state


class Artifact(TypedDict):
    """Simplified artifact structure"""
    artifact_id: str        # Unique identifier
    title: str              # Artifact title
    content: str            # The actual content (code, text, markdown, etc.)
    language: Optional[str] # Optional language hint for syntax highlighting


class SelectedText(TypedDict):
    """User selected text in artifact - supports both character and line-based selection"""
    start: int                      # Character position start (0-indexed)
    end: int                        # Character position end (0-indexed)
    text: str                       # The actual selected text content
    lineStart: Optional[int]        # Line number start (1-indexed) for code
    lineEnd: Optional[int]          # Line number end (1-indexed) for code


class CanvasGraphState(TypedDict):
    """Extended state for canvas feature"""
    messages: List[Dict[str, str]]
    thread_id: str
    run_id: str
    artifact: Optional[Artifact]
    selectedText: Optional[SelectedText]
    artifactAction: Optional[str]  # "create", "update", "partial_update"
    artifact_id: Optional[str]     # Current artifact ID being worked on


def detect_intent_node(state: CanvasGraphState) -> CanvasGraphState:
    """Classify if message requires artifact manipulation"""
    # For now, simple heuristic: if artifact exists, assume update
    # Otherwise, check for keywords suggesting artifact creation
    
    if not state["messages"]:
        return state
    
    # Check if there's a text selection - this takes priority for partial updates
    selected_text = state.get("selectedText")
    artifact = state.get("artifact")
    
    if selected_text and artifact:
        # User has selected text AND there's an existing artifact
        # Default to "partial_update" action
        state["artifactAction"] = "partial_update"
        logger.info(f"Detected partial_update intent with selection: {selected_text.get('start')}-{selected_text.get('end')}")
        return state
    
    last_message = state["messages"][-1]["content"].lower()
    
    # Keywords suggesting artifact creation/manipulation
    create_keywords = ["create", "write", "generate", "make", "build"]
    update_keywords = ["update", "modify", "change", "edit", "fix"]
    
    if artifact:
        # Artifact exists, default to update
        if any(keyword in last_message for keyword in update_keywords):
            state["artifactAction"] = "update"
        else:
            # Default to update if artifact exists
            state["artifactAction"] = "update"
    else:
        # No artifact, check for creation
        if any(keyword in last_message for keyword in create_keywords):
            state["artifactAction"] = "create"
        else:
            state["artifactAction"] = None
    
    return state


def route_to_handler(state: CanvasGraphState) -> str:
    """Route based on detected intent"""
    action = state.get("artifactAction")
    route = "artifact_action" if action else "chat_only"
    logger.info(f"Routing to: {route} (artifactAction={action})")
    return route


def update_artifact_node(state: CanvasGraphState) -> CanvasGraphState:
    """Finalize artifact updates"""
    # This node is a placeholder for any post-processing
    return state


async def chat_response_node(state: CanvasGraphState, config=None) -> CanvasGraphState:
    """Handle non-artifact chat messages using regular chat agent with streaming"""
    from agents.chat_agent import ChatAgent
    
    event_callback = config.get("configurable", {}).get("event_callback") if config else None
    
    # Use chat agent for non-artifact conversations
    chat_agent = ChatAgent(model=None, provider=None)  # Uses defaults from state/config
    
    async for event in chat_agent.run(state):
        if event_callback:
            await event_callback(event)
    
    return state


def create_canvas_graph(model: str = None, provider: str = None):
    """Build canvas workflow graph with streaming support
    
    Args:
        model: Optional model name (e.g., 'qwen:7b', 'gemini-pro')
        provider: Optional provider name (e.g., 'ollama', 'gemini', 'azure-openai')
    """
    from agents.canvas_agent import CanvasAgent
    
    canvas_agent = CanvasAgent(model=model, provider=provider)
    
    graph = StateGraph(CanvasGraphState)
    
    # Async canvas node with streaming callback support
    async def canvas_agent_node(state: CanvasGraphState, config=None):
        """Wrapper node that dispatches agent events with streaming"""
        event_callback = config.get("configurable", {}).get("event_callback") if config else None
        
        logger.info(f"Canvas agent node executing with action: {state.get('artifactAction')}")
        
        async for event in canvas_agent.run(state):
            if event_callback:
                await event_callback(event)
        
        logger.info(f"Canvas agent node completed")
        return state
    
    # Nodes
    graph.add_node("prepare_state", prepare_canvas_state)
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("canvas_agent", canvas_agent_node)  # Use async version with callback
    graph.add_node("update_artifact", update_artifact_node)
    graph.add_node("chat_response", chat_response_node)
    
    # Edges
    graph.add_edge(START, "prepare_state")
    graph.add_edge("prepare_state", "detect_intent")
    
    graph.add_conditional_edges(
        "detect_intent",
        route_to_handler,
        {
            "artifact_action": "canvas_agent",
            "chat_only": "chat_response",
        }
    )
    
    graph.add_edge("canvas_agent", "update_artifact")
    graph.add_edge("update_artifact", END)
    graph.add_edge("chat_response", END)
    
    return graph.compile()
