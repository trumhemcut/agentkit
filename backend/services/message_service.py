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
        role: str,
        content: str = None,
        artifact_data: dict = None,
        metadata: dict = None
    ) -> Message:
        """
        Create a new message in a thread.
        
        Args:
            db: Database session
            thread_id: Parent thread identifier
            role: Message role ("user" or "assistant")
            content: Text content of the message
            artifact_data: A2UI artifact data (will be JSON-encoded)
            metadata: Additional metadata (will be JSON-encoded)
            
        Returns:
            Created message instance
        """
        message = Message(
            thread_id=thread_id,
            role=role,
            content=content,
            artifact_data=json.dumps(artifact_data) if artifact_data else None,
            message_metadata=json.dumps(metadata) if metadata else None
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        logger.info(f"Created message {message.id} in thread {thread_id} with role={role}")
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
