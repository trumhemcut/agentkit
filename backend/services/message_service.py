"""Message service for managing conversation messages."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Message
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class MessageService:
    """Service layer for message operations."""
    
    @staticmethod
    async def create_message(
        db: AsyncSession,
        thread_id: str,
        agent_id: str,
        role: str,
        content: str = None,
        message_type: str = "text",
        artifact_data: dict = None,
        metadata: dict = None,
        is_interrupted: bool = False
    ) -> Message:
        """
        Create a new message in a thread.
        
        Args:
            db: Database session
            thread_id: Parent thread identifier
            agent_id: Agent identifier (e.g., "chat", "canvas", "salary_viewer")
            role: Message role ("user" or "assistant")
            content: Text content of the message
            message_type: Message type ("text" or "artifact"), defaults to "text"
            artifact_data: A2UI artifact data (will be JSON-encoded)
            metadata: Additional metadata (will be JSON-encoded)
            is_interrupted: Whether message was interrupted by user
            
        Returns:
            Created message instance
        """
        message = Message(
            thread_id=thread_id,
            agent_id=agent_id,
            role=role,
            message_type=message_type,
            content=content,
            artifact_data=json.dumps(artifact_data) if artifact_data else None,
            message_metadata=json.dumps(metadata) if metadata else None,
            is_interrupted=is_interrupted
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        logger.info(f"Created message {message.id} in thread {thread_id} with role={role}, agent_id={agent_id}, type={message_type}, interrupted={is_interrupted}")
        return message
    
    @staticmethod
    async def get_message(db: AsyncSession, message_id: str) -> Optional[Message]:
        """
        Get message by ID.
        
        Args:
            db: Database session
            message_id: Message identifier
            
        Returns:
            Message instance or None if not found
        """
        result = await db.execute(select(Message).filter(Message.id == message_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_messages(db: AsyncSession, thread_id: str) -> List[Message]:
        """
        List all messages in a thread ordered by created_at ASC.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            
        Returns:
            List of message instances
        """
        result = await db.execute(
            select(Message)
            .filter(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update_message_interrupted(db: AsyncSession, message_id: str, is_interrupted: bool = True) -> bool:
        """
        Update message interrupted status.
        
        Args:
            db: Database session
            message_id: Message identifier
            is_interrupted: Interrupted status
            
        Returns:
            True if message was updated, False if not found
        """
        result = await db.execute(select(Message).filter(Message.id == message_id))
        message = result.scalar_one_or_none()
        
        if message:
            message.is_interrupted = is_interrupted
            await db.commit()
            logger.info(f"Updated message {message_id} interrupted status to {is_interrupted}")
            return True
        
        return False
    
    @staticmethod
    async def delete_message(db: AsyncSession, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            db: Database session
            message_id: Message identifier
            
        Returns:
            True if message was deleted, False if not found
        """
        result = await db.execute(select(Message).filter(Message.id == message_id))
        message = result.scalar_one_or_none()
        
        if message:
            await db.delete(message)
            await db.commit()
            logger.info(f"Deleted message {message_id}")
            return True
        
        return False
