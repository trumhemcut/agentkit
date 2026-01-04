"""Thread service for managing conversation threads."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Thread
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ThreadService:
    """Service layer for thread operations."""
    
    @staticmethod
    async def create_thread(
        db: AsyncSession, 
        agent_id: str, 
        model: str, 
        provider: str, 
        title: str = None
    ) -> Thread:
        """
        Create a new thread.
        
        Args:
            db: Database session
            agent_id: Agent identifier (e.g., "chat", "canvas")
            model: LLM model name
            provider: LLM provider name
            title: Optional thread title
            
        Returns:
            Created thread instance
        """
        thread = Thread(
            agent_id=agent_id,
            model=model,
            provider=provider,
            title=title or f"New {agent_id} conversation"
        )
        db.add(thread)
        await db.commit()
        await db.refresh(thread)
        
        logger.info(f"Created thread {thread.id} with agent_id={agent_id}")
        return thread
    
    @staticmethod
    async def get_thread(db: AsyncSession, thread_id: str) -> Optional[Thread]:
        """
        Get thread by ID.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            
        Returns:
            Thread instance or None if not found
        """
        result = await db.execute(select(Thread).filter(Thread.id == thread_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_threads(
        db: AsyncSession, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Thread]:
        """
        List all threads ordered by updated_at DESC.
        
        Args:
            db: Database session
            limit: Maximum number of threads to return
            offset: Number of threads to skip
            
        Returns:
            List of thread instances
        """
        result = await db.execute(
            select(Thread)
            .order_by(Thread.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update_thread(
        db: AsyncSession, 
        thread_id: str, 
        title: str = None
    ) -> Optional[Thread]:
        """
        Update thread metadata.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            title: New thread title
            
        Returns:
            Updated thread instance or None if not found
        """
        result = await db.execute(select(Thread).filter(Thread.id == thread_id))
        thread = result.scalar_one_or_none()
        
        if thread:
            if title is not None:
                thread.title = title
            thread.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(thread)
            logger.info(f"Updated thread {thread_id}")
        
        return thread
    
    @staticmethod
    async def delete_thread(db: AsyncSession, thread_id: str) -> bool:
        """
        Delete thread and all associated messages.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            
        Returns:
            True if thread was deleted, False if not found
        """
        result = await db.execute(select(Thread).filter(Thread.id == thread_id))
        thread = result.scalar_one_or_none()
        
        if thread:
            await db.delete(thread)
            await db.commit()
            logger.info(f"Deleted thread {thread_id}")
            return True
        
        return False
