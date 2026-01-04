"""
Thread Router

Handles thread CRUD operations for conversation persistence.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.models import ThreadCreate, ThreadUpdate, ThreadResponse, ThreadListResponse, DeleteResponse
from database.config import get_db
from services.thread_service import ThreadService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/threads", response_model=ThreadResponse)
async def create_thread(
    data: ThreadCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new conversation thread.
    
    Request body:
        agent_id: str - Agent identifier ("chat", "canvas", "salary_viewer")
        model: str - LLM model name
        provider: str - LLM provider name
        title: str (optional) - Thread title
    
    Returns:
        Thread object with id, title, agent_id, model, provider, timestamps
    """
    try:
        thread = await ThreadService.create_thread(
            db, data.agent_id, data.model, data.provider, data.title
        )
        return ThreadResponse.model_validate(thread)
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all conversation threads.
    
    Query params:
        limit: int - Maximum number of threads to return (default: 50)
        offset: int - Number of threads to skip (default: 0)
    
    Returns:
        List of thread objects ordered by updated_at DESC
    """
    try:
        threads = await ThreadService.list_threads(db, limit, offset)
        return ThreadListResponse(
            threads=[ThreadResponse.model_validate(t) for t in threads]
        )
    except Exception as e:
        logger.error(f"Error listing threads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific thread by ID.
    
    Path params:
        thread_id: str - Thread identifier
    
    Returns:
        Thread object with full details
    """
    try:
        thread = await ThreadService.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return ThreadResponse.model_validate(thread)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    data: ThreadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update thread metadata.
    
    Path params:
        thread_id: str - Thread identifier
    
    Request body:
        title: str (optional) - New thread title
    
    Returns:
        Updated thread details
    """
    try:
        thread = await ThreadService.update_thread(db, thread_id, data.title)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return ThreadResponse.model_validate(thread)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/threads/{thread_id}", response_model=DeleteResponse)
async def delete_thread(
    thread_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a thread and all associated messages.
    
    Path params:
        thread_id: str - Thread identifier
    
    Returns:
        Success message
    """
    try:
        success = await ThreadService.delete_thread(db, thread_id)
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return DeleteResponse(message="Thread deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
