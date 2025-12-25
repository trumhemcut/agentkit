# Re-export EventType from ag_ui.core for convenience
from ag_ui.core import EventType

# Canvas-specific custom event types (as strings for CustomEvent)
class CanvasEventType:
    """Canvas-specific event type constants"""
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_STREAMING = "artifact_streaming"
    ARTIFACT_STREAMING_START = "artifact_streaming_start"
    SELECTION_CONTEXT = "selection_context"
    THINKING = "thinking"
    
    # Partial update events
    ARTIFACT_PARTIAL_UPDATE_START = "artifact_partial_update_start"
    ARTIFACT_PARTIAL_UPDATE_CHUNK = "artifact_partial_update_chunk"
    ARTIFACT_PARTIAL_UPDATE_COMPLETE = "artifact_partial_update_complete"

__all__ = ["EventType", "CanvasEventType"]
