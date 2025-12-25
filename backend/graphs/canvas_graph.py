import logging
from typing import TypedDict, Optional, List, Dict
from langgraph.graph import StateGraph, START, END

logger = logging.getLogger(__name__)


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
    if state.get("artifactAction"):
        return "artifact_action"
    return "chat_only"


def update_artifact_node(state: CanvasGraphState) -> CanvasGraphState:
    """Finalize artifact updates"""
    # This node is a placeholder for any post-processing
    return state


def chat_response_node(state: CanvasGraphState) -> CanvasGraphState:
    """Handle non-artifact chat messages using regular chat agent"""
    # This will be handled by the chat agent in the streaming response
    # We just return the state as-is since streaming is handled at the route level
    return state


def create_canvas_graph(model: str = None):
    """Build canvas workflow graph"""
    from agents.canvas_agent import CanvasAgent
    
    canvas_agent = CanvasAgent(model=model)
    
    graph = StateGraph(CanvasGraphState)
    
    # Nodes
    graph.add_node("detect_intent", detect_intent_node)
    graph.add_node("canvas_agent", canvas_agent.process_sync)  # Use sync version
    graph.add_node("update_artifact", update_artifact_node)
    graph.add_node("chat_response", chat_response_node)
    
    # Edges
    graph.add_edge(START, "detect_intent")
    
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
