import uuid
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from protocols.a2ui_types import UserAction
from datetime import datetime


class Message(BaseModel):
    role: str
    content: str
    message_type: Optional[str] = "text"  # "text" or "artifact"
    
    # Artifact-specific fields (only when message_type="artifact")
    language: Optional[str] = None  # for code artifacts
    title: Optional[str] = None


class RunAgentInput(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    model: Optional[str] = None  # Optional model selection
    provider: Optional[str] = None  # Optional provider selection
    agent: Optional[str] = "chat"  # Optional agent selection
    
    # Canvas-specific optional fields (for unified endpoint)
    artifact: Optional['Artifact'] = None  # Full artifact object from frontend
    artifact_id: Optional[str] = None  # Server-side cached artifact ID
    selectedText: Optional['SelectedText'] = None
    action: Optional[Literal["create", "update", "partial_update", "chat"]] = None


# Canvas-specific models

class Artifact(BaseModel):
    """Simplified artifact structure"""
    artifact_id: str
    title: str
    content: str
    language: Optional[str] = None


class SelectedText(BaseModel):
    """User selected text in artifact - supports both character and line-based selection"""
    start: int = Field(..., description="Character position start (0-indexed)")
    end: int = Field(..., description="Character position end (0-indexed)")
    text: str = Field(..., description="Selected text content")
    lineStart: Optional[int] = Field(None, description="Line number start (1-indexed) for code")
    lineEnd: Optional[int] = Field(None, description="Line number end (1-indexed) for code")


class CanvasMessageRequest(BaseModel):
    """Request model for canvas chat endpoint"""
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    artifact_id: Optional[str] = None  # Server-side cached artifact ID
    selectedText: Optional[SelectedText] = None
    action: Optional[Literal["create", "update", "partial_update", "chat"]] = None
    model: Optional[str] = None  # Optional model selection
    provider: Optional[str] = None  # Optional provider selection
    agent: Optional[str] = "canvas"  # Optional agent selection


class ArtifactUpdate(BaseModel):
    """Manual artifact update request"""
    content: str
    artifact_id: str


class UserActionRequest(BaseModel):
    """
    Request model for user action endpoint.
    
    Sent from frontend when user interacts with A2UI components
    (e.g., clicks a button, submits a form).
    """
    user_action: UserAction = Field(..., alias="userAction")
    thread_id: str = Field(..., alias="threadId")
    run_id: str = Field(..., alias="runId")
    model: Optional[str] = None  # Optional model selection
    provider: Optional[str] = None  # Optional provider selection

    class Config:
        populate_by_name = True


# ============================================================================
# Database Persistence Models
# ============================================================================

class ThreadCreate(BaseModel):
    """Request model for creating a thread"""
    agent_id: str = Field(..., description="Agent identifier (chat, canvas, salary_viewer)")
    model: str = Field(..., description="LLM model name")
    provider: str = Field(..., description="LLM provider name")
    title: Optional[str] = Field(None, description="Thread title")


class ThreadUpdate(BaseModel):
    """Request model for updating a thread"""
    title: Optional[str] = Field(None, description="New thread title")


class ThreadResponse(BaseModel):
    """Response model for thread data"""
    id: str
    title: str
    agent_id: str
    model: str
    provider: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ThreadListResponse(BaseModel):
    """Response model for listing threads"""
    threads: List[ThreadResponse]


class MessageCreate(BaseModel):
    """Request model for creating a message"""
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: Optional[str] = Field(None, description="Text content")
    message_type: Optional[Literal["text", "artifact"]] = Field("text", description="Message type")
    artifact_data: Optional[Dict[str, Any]] = Field(None, description="A2UI artifact data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class MessageResponse(BaseModel):
    """Response model for message data"""
    id: str
    thread_id: str
    agent_id: str
    role: str
    message_type: str
    content: Optional[str]
    artifact_data: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    is_interrupted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Response model for listing messages"""
    messages: List[MessageResponse]


class DeleteResponse(BaseModel):
    """Response model for delete operations"""
    message: str


# ============================================================================
# Message Feedback Models
# ============================================================================

class MessageFeedbackRequest(BaseModel):
    """Request model for submitting message feedback"""
    feedback_type: Literal["like", "dislike"] = Field(..., description="Type of feedback")


class MessageFeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    success: bool
    message_id: str
    feedback_type: str


class MessageFeedbackData(BaseModel):
    """Response model for feedback data"""
    feedback_type: Optional[Literal["like", "dislike"]] = None


