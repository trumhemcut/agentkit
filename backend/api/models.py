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
    artifact: Optional['ArtifactV3'] = None
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
    """User selected text in artifact"""
    start: int
    end: int
    text: str


class CanvasMessageRequest(BaseModel):
    """Request model for canvas chat endpoint"""
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message]
    artifact: Optional[ArtifactV3] = None
    selectedText: Optional[SelectedText] = None
    action: Optional[Literal["create", "update", "rewrite", "chat"]] = None
    model: Optional[str] = None  # Optional model selection
    agent: Optional[str] = "canvas"  # Optional agent selection


class ArtifactUpdate(BaseModel):
    """Manual artifact update request"""
    content: str
    index: int

