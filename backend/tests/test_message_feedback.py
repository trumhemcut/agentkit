"""
Tests for message feedback functionality.

Tests the feedback service, API endpoints, and database operations.
"""
import pytest
from uuid import uuid4
from database.models import Thread, Message, MessageFeedback
from services.feedback_service import FeedbackService
from services.thread_service import ThreadService
from services.message_service import MessageService


class TestFeedbackService:
    """Test FeedbackService class"""
    
    @pytest.mark.asyncio
    async def test_add_feedback_creates_new(self, db_session):
        """Test adding feedback creates new entry"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Add feedback
        feedback = await FeedbackService.add_feedback(
            db_session, message.id, "like"
        )
        
        assert feedback is not None
        assert feedback.message_id == message.id
        assert feedback.feedback_type == "like"
    
    @pytest.mark.asyncio
    async def test_add_feedback_updates_existing(self, db_session):
        """Test adding feedback updates existing entry"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Add initial feedback
        feedback1 = await FeedbackService.add_feedback(
            db_session, message.id, "like"
        )
        feedback1_id = feedback1.id
        
        # Update feedback
        feedback2 = await FeedbackService.add_feedback(
            db_session, message.id, "dislike"
        )
        
        # Should update the same entry, not create new one
        assert feedback2.id == feedback1_id
        assert feedback2.feedback_type == "dislike"
        
        # Verify only one feedback exists
        from sqlalchemy import select
        result = await db_session.execute(
            select(MessageFeedback).filter(MessageFeedback.message_id == message.id)
        )
        all_feedback = result.scalars().all()
        assert len(all_feedback) == 1
    
    @pytest.mark.asyncio
    async def test_add_feedback_invalid_message(self, db_session):
        """Test adding feedback to non-existent message raises error"""
        fake_message_id = str(uuid4())
        
        with pytest.raises(ValueError, match="not found"):
            await FeedbackService.add_feedback(
                db_session, fake_message_id, "like"
            )
    
    @pytest.mark.asyncio
    async def test_get_feedback_exists(self, db_session):
        """Test getting existing feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Add feedback
        await FeedbackService.add_feedback(db_session, message.id, "like")
        
        # Get feedback
        feedback = await FeedbackService.get_feedback(db_session, message.id)
        
        assert feedback is not None
        assert feedback.feedback_type == "like"
    
    @pytest.mark.asyncio
    async def test_get_feedback_not_exists(self, db_session):
        """Test getting non-existent feedback returns None"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Get feedback (should be None)
        feedback = await FeedbackService.get_feedback(db_session, message.id)
        
        assert feedback is None
    
    @pytest.mark.asyncio
    async def test_remove_feedback_exists(self, db_session):
        """Test removing existing feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Add feedback
        await FeedbackService.add_feedback(db_session, message.id, "like")
        
        # Remove feedback
        result = await FeedbackService.remove_feedback(db_session, message.id)
        
        assert result is True
        
        # Verify feedback is removed
        feedback = await FeedbackService.get_feedback(db_session, message.id)
        assert feedback is None
    
    @pytest.mark.asyncio
    async def test_remove_feedback_not_exists(self, db_session):
        """Test removing non-existent feedback returns False"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Remove feedback (should return False)
        result = await FeedbackService.remove_feedback(db_session, message.id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_feedback_cascade_delete(self, db_session):
        """Test feedback is deleted when message is deleted"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Add feedback
        feedback = await FeedbackService.add_feedback(
            db_session, message.id, "like"
        )
        feedback_id = feedback.id
        
        # Delete message
        await MessageService.delete_message(db_session, message.id)
        
        # Verify feedback is also deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(MessageFeedback).filter(MessageFeedback.id == feedback_id)
        )
        deleted_feedback = result.scalar_one_or_none()
        assert deleted_feedback is None


class TestFeedbackAPI:
    """Test feedback API endpoints"""
    
    @pytest.mark.asyncio
    async def test_submit_feedback_like(self, client, db_session):
        """Test submitting like feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Submit feedback
        response = await client.post(
            f"/api/messages/{message.id}/feedback",
            json={"feedback_type": "like"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message_id"] == message.id
        assert data["feedback_type"] == "like"
    
    @pytest.mark.asyncio
    async def test_submit_feedback_dislike(self, client, db_session):
        """Test submitting dislike feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Submit feedback
        response = await client.post(
            f"/api/messages/{message.id}/feedback",
            json={"feedback_type": "dislike"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["feedback_type"] == "dislike"
    
    @pytest.mark.asyncio
    async def test_submit_feedback_update(self, client, db_session):
        """Test updating existing feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Submit initial feedback
        response1 = await client.post(
            f"/api/messages/{message.id}/feedback",
            json={"feedback_type": "like"}
        )
        assert response1.status_code == 200
        
        # Update feedback
        response2 = await client.post(
            f"/api/messages/{message.id}/feedback",
            json={"feedback_type": "dislike"}
        )
        
        assert response2.status_code == 200
        data = response2.json()
        assert data["feedback_type"] == "dislike"
    
    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_message(self, client):
        """Test submitting feedback for non-existent message"""
        fake_message_id = str(uuid4())
        
        response = await client.post(
            f"/api/messages/{fake_message_id}/feedback",
            json={"feedback_type": "like"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_feedback_exists(self, client, db_session):
        """Test getting existing feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Submit feedback
        await client.post(
            f"/api/messages/{message.id}/feedback",
            json={"feedback_type": "like"}
        )
        
        # Get feedback
        response = await client.get(f"/api/messages/{message.id}/feedback")
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback_type"] == "like"
    
    @pytest.mark.asyncio
    async def test_get_feedback_not_exists(self, client, db_session):
        """Test getting non-existent feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Get feedback (should be None)
        response = await client.get(f"/api/messages/{message.id}/feedback")
        
        assert response.status_code == 200
        data = response.json()
        assert data["feedback_type"] is None
    
    @pytest.mark.asyncio
    async def test_remove_feedback(self, client, db_session):
        """Test removing feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Submit feedback
        await client.post(
            f"/api/messages/{message.id}/feedback",
            json={"feedback_type": "like"}
        )
        
        # Remove feedback
        response = await client.delete(f"/api/messages/{message.id}/feedback")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify feedback is removed
        get_response = await client.get(f"/api/messages/{message.id}/feedback")
        get_data = get_response.json()
        assert get_data["feedback_type"] is None
    
    @pytest.mark.asyncio
    async def test_remove_feedback_not_exists(self, client, db_session):
        """Test removing non-existent feedback"""
        # Create test thread and message
        thread = await ThreadService.create_thread(
            db_session, "chat", "gpt-4o-mini", "azure-openai", "Test Thread"
        )
        message = await MessageService.create_message(
            db_session, thread.id, "chat", "assistant", "Test response"
        )
        
        # Remove feedback (should return 404)
        response = await client.delete(f"/api/messages/{message.id}/feedback")
        
        assert response.status_code == 404
