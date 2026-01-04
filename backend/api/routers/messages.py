"""
Message Router

Handles message CRUD operations for conversation persistence.
"""
import logging
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.models import MessageCreate, MessageResponse, MessageListResponse, DeleteResponse
from database.config import get_db
from services.thread_service import ThreadService
from services.message_service import MessageService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def create_message(
    thread_id: str,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new message in a thread.
    
    Path params:
        thread_id: str - Thread identifier
    
    Request body:
        role: str - Message role ("user" or "assistant")
        content: str (optional) - Text content
        artifact_data: dict (optional) - A2UI artifact data
        metadata: dict (optional) - Additional metadata
    
    Returns:
        Created message object
    """
    try:
        # Verify thread exists
        thread = await ThreadService.get_thread(db, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Auto-detect message_type if not provided
        message_type = data.message_type
        if message_type == "text" and data.artifact_data:
            message_type = "artifact"
        
        message = await MessageService.create_message(
            db, thread_id, thread.agent_id, data.role, data.content, message_type, data.artifact_data, data.metadata
        )
        
        # Convert to response model
        return MessageResponse(
            id=message.id,
            thread_id=message.thread_id,
            agent_id=message.agent_id,
            role=message.role,
            message_type=message.message_type,
            content=message.content,
            artifact_data=json.loads(message.artifact_data) if message.artifact_data else None,
            metadata=json.loads(message.message_metadata) if message.message_metadata else None,
            is_interrupted=message.is_interrupted,
            created_at=message.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message in thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/{thread_id}/messages", response_model=MessageListResponse)
async def list_messages(
    thread_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    List all messages in a thread.
    
    Path params:
        thread_id: str - Thread identifier
    
    Returns:
        List of message objects ordered by created_at ASC
    """
    try:
        messages = await MessageService.list_messages(db, thread_id)
        return MessageListResponse(
            messages=[
                MessageResponse(
                    id=m.id,
                    thread_id=m.thread_id,
                    agent_id=m.agent_id,
                    role=m.role,
                    message_type=m.message_type,
                    content=m.content,
                    artifact_data=json.loads(m.artifact_data) if m.artifact_data else None,
                    metadata=json.loads(m.message_metadata) if m.message_metadata else None,
                    is_interrupted=m.is_interrupted,
                    created_at=m.created_at
                )
                for m in messages
            ]
        )
    except Exception as e:
        logger.error(f"Error listing messages for thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/messages/{message_id}/interrupted")
async def update_message_interrupted(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a message as interrupted by user.
    
    Path params:
        message_id: str - Message identifier
    
    Returns:
        Success message
    """
    try:
        success = await MessageService.update_message_interrupted(db, message_id)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return {"message": "Message marked as interrupted", "message_id": message_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message {message_id} interrupted status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{message_id}", response_model=DeleteResponse)
async def delete_message(
    message_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a message.
    
    Path params:
        message_id: str - Message identifier
    
    Returns:
        Success message
    """
    try:
        success = await MessageService.delete_message(db, message_id)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return DeleteResponse(message="Message deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
