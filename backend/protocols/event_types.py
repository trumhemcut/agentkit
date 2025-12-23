# Re-export EventType from ag_ui.core for convenience
from ag_ui.core import EventType

# Canvas-specific custom event types (as strings for CustomEvent)
class CanvasEventType:
    """Canvas-specific event type constants"""
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_STREAMING = "artifact_streaming"
    ARTIFACT_STREAMING_START = "artifact_streaming_start"
    ARTIFACT_VERSION_CHANGED = "artifact_version_changed"
    SELECTION_CONTEXT = "selection_context"
    THINKING = "thinking"

__all__ = ["EventType", "CanvasEventType"]
