"""Database models for AgentKit persistence layer."""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.config import Base
from datetime import datetime
import uuid


class Thread(Base):
    """
    Thread model representing a conversation thread.
    
    Attributes:
        id: Unique thread identifier (UUID)
        title: Optional thread title
        agent_id: Agent identifier (e.g., "chat", "canvas", "salary_viewer")
        model: LLM model name (e.g., "gpt-5-mini", "gemini-2.5-flash")
        provider: LLM provider (e.g., "azure-openai", "gemini", "ollama")
        created_at: Timestamp when thread was created
        updated_at: Timestamp when thread was last updated
        messages: Relationship to associated messages
    """
    __tablename__ = "threads"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    agent_id = Column(String(50), nullable=False)  # "chat", "canvas", "salary_viewer"
    model = Column(String(100), nullable=False)  # "gpt-5-mini", "gemini-2.5-flash"
    provider = Column(String(50), nullable=False)  # "azure-openai", "gemini", "ollama"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Thread(id={self.id}, title={self.title}, agent_id={self.agent_id})>"


class Message(Base):
    """
    Message model representing a message in a conversation thread.
    
    Attributes:
        id: Unique message identifier (UUID)
        thread_id: Foreign key to parent thread
        agent_id: Agent identifier (e.g., "chat", "canvas", "salary_viewer") - denormalized for easier querying
        role: Message role ("user" or "assistant")
        message_type: Message type ("text" or "artifact")
        content: Text content of the message
        artifact_data: JSON string for A2UI artifacts
        metadata: JSON string for additional metadata
        is_interrupted: Whether message was interrupted by user (Stop button)
        created_at: Timestamp when message was created
        thread: Relationship to parent thread
    """
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(36), ForeignKey("threads.id"), nullable=False)
    agent_id = Column(String(50), nullable=False)  # "chat", "canvas", "salary_viewer" - denormalized from thread
    role = Column(String(20), nullable=False)  # "user", "assistant"
    message_type = Column(String(20), nullable=False, default="text")  # "text", "artifact"
    content = Column(Text, nullable=True)  # Text content
    artifact_data = Column(Text, nullable=True)  # JSON string for A2UI artifacts
    message_metadata = Column(Text, nullable=True)  # JSON string for additional metadata (renamed from 'metadata')
    is_interrupted = Column(Boolean, default=False, nullable=False)  # True if user clicked Stop button
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    thread = relationship("Thread", back_populates="messages")
    feedbacks = relationship("MessageFeedback", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(id={self.id}, thread_id={self.thread_id}, role={self.role})>"


class MessageFeedback(Base):
    """
    Message feedback model for tracking user reactions (like/dislike).
    
    Attributes:
        id: Unique feedback identifier (UUID)
        message_id: Foreign key to the message
        feedback_type: Type of feedback ("like" or "dislike")
        created_at: Timestamp when feedback was given
        message: Relationship to the message
    """
    __tablename__ = "message_feedbacks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False)
    feedback_type = Column(String(20), nullable=False)  # "like", "dislike"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    message = relationship("Message", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<MessageFeedback(id={self.id}, message_id={self.message_id}, feedback_type={self.feedback_type})>"
