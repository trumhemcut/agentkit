"""Service for handling message feedback operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import MessageFeedback, Message
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for managing message feedback."""
    
    @staticmethod
    async def add_feedback(
        db: AsyncSession,
        message_id: str,
        feedback_type: str
    ) -> MessageFeedback:
        """
        Add or update feedback for a message.
        
        If feedback already exists for this message, it will be updated.
        Otherwise, a new feedback entry is created.
        
        Args:
            db: Database session
            message_id: ID of the message to add feedback to
            feedback_type: Type of feedback ("like" or "dislike")
            
        Returns:
            MessageFeedback: The created or updated feedback object
            
        Raises:
            ValueError: If message is not found
        """
        # Check if message exists
        result = await db.execute(select(Message).filter(Message.id == message_id))
        message = result.scalar_one_or_none()
        
        if not message:
            logger.error(f"Message {message_id} not found")
            raise ValueError(f"Message {message_id} not found")
        
        # Check if feedback already exists
        result = await db.execute(
            select(MessageFeedback).filter(MessageFeedback.message_id == message_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing feedback
            logger.info(f"Updating feedback for message {message_id} to {feedback_type}")
            existing.feedback_type = feedback_type
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new feedback
            logger.info(f"Creating new feedback for message {message_id}: {feedback_type}")
            feedback = MessageFeedback(
                id=str(uuid.uuid4()),
                message_id=message_id,
                feedback_type=feedback_type
            )
            db.add(feedback)
            await db.commit()
            await db.refresh(feedback)
            return feedback
    
    @staticmethod
    async def remove_feedback(
        db: AsyncSession,
        message_id: str
    ) -> bool:
        """
        Remove feedback for a message.
        
        Args:
            db: Database session
            message_id: ID of the message to remove feedback from
            
        Returns:
            bool: True if feedback was removed, False if no feedback existed
        """
        result = await db.execute(
            select(MessageFeedback).filter(MessageFeedback.message_id == message_id)
        )
        feedback = result.scalar_one_or_none()
        
        if feedback:
            logger.info(f"Removing feedback for message {message_id}")
            await db.delete(feedback)
            await db.commit()
            return True
        
        logger.debug(f"No feedback found for message {message_id}")
        return False
    
    @staticmethod
    async def get_feedback(
        db: AsyncSession,
        message_id: str
    ) -> Optional[MessageFeedback]:
        """
        Get feedback for a message.
        
        Args:
            db: Database session
            message_id: ID of the message to get feedback for
            
        Returns:
            Optional[MessageFeedback]: The feedback object if it exists, None otherwise
        """
        result = await db.execute(
            select(MessageFeedback).filter(MessageFeedback.message_id == message_id)
        )
        feedback = result.scalar_one_or_none()
        
        if feedback:
            logger.debug(f"Found feedback for message {message_id}: {feedback.feedback_type}")
        else:
            logger.debug(f"No feedback found for message {message_id}")
        
        return feedback
