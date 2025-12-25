import uuid
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal, Dict


class Message(BaseModel):
    role: str
    content: str
    message_type: Optional[str] = "text"  # "text" or "artifact"
    
    # Artifact-specific fields (only when message_type="artifact")
    artifact_type: Optional[str] = None  # "code", "text", "document"
    language: Optional[str] = None  # for code artifacts
    title: Optional[str] = None


class RunAgentInput(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    model: Optional[str] = None  # Optional model selection
    agent: Optional[str] = "chat"  # Optional agent selection
    
    # Canvas-specific optional fields (for unified endpoint)
    artifact: Optional['ArtifactV3'] = None  # DEPRECATED: Use artifact_id instead
    artifact_id: Optional[str] = None  # Server-side cached artifact ID
    selectedText: Optional['SelectedText'] = None
    action: Optional[Literal["create", "update", "rewrite", "chat"]] = None


# Canvas-specific models

class ArtifactContentCode(BaseModel):
    """Code artifact content"""
    index: int
    type: Literal["code"]
    title: str
    code: str
    language: str


class ArtifactContentText(BaseModel):
    """Text/Markdown artifact content"""
    index: int
    type: Literal["text"]
    title: str
    fullMarkdown: str


class ArtifactV3(BaseModel):
    """Canvas artifact with versioning"""
    currentIndex: int
    contents: List[Union[ArtifactContentCode, ArtifactContentText]]


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
    artifact: Optional[ArtifactV3] = None  # DEPRECATED: Use artifact_id instead
    artifact_id: Optional[str] = None  # Server-side cached artifact ID
    selectedText: Optional[SelectedText] = None
    action: Optional[Literal["create", "update", "rewrite", "chat"]] = None
    model: Optional[str] = None  # Optional model selection
    agent: Optional[str] = "canvas"  # Optional agent selection


class ArtifactUpdate(BaseModel):
    """Manual artifact update request"""
    content: str
    index: int

