"""Database models for AgentKit persistence layer."""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
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
        agent_type: Type of agent (e.g., "chat", "canvas", "salary_viewer")
        model: LLM model name (e.g., "gpt-5-mini", "gemini-2.5-flash")
        provider: LLM provider (e.g., "azure-openai", "gemini", "ollama")
        created_at: Timestamp when thread was created
        updated_at: Timestamp when thread was last updated
        messages: Relationship to associated messages
    """
    __tablename__ = "threads"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    agent_type = Column(String(50), nullable=False)  # "chat", "canvas", "salary_viewer"
    model = Column(String(100), nullable=False)  # "gpt-5-mini", "gemini-2.5-flash"
    provider = Column(String(50), nullable=False)  # "azure-openai", "gemini", "ollama"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Thread(id={self.id}, title={self.title}, agent_type={self.agent_type})>"


class Message(Base):
    """
    Message model representing a message in a conversation thread.
    
    Attributes:
        id: Unique message identifier (UUID)
        thread_id: Foreign key to parent thread
        role: Message role ("user" or "assistant")
        content: Text content of the message
        artifact_data: JSON string for A2UI artifacts
        metadata: JSON string for additional metadata
        created_at: Timestamp when message was created
        thread: Relationship to parent thread
    """
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(36), ForeignKey("threads.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user", "assistant"
    content = Column(Text, nullable=True)  # Text content
    artifact_data = Column(Text, nullable=True)  # JSON string for A2UI artifacts
    message_metadata = Column(Text, nullable=True)  # JSON string for additional metadata (renamed from 'metadata')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    thread = relationship("Thread", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, thread_id={self.thread_id}, role={self.role})>"
