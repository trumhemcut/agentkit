"""Test cases for message persistence endpoints."""

import pytest
import json
from services.thread_service import ThreadService
from services.message_service import MessageService


@pytest.mark.asyncio
async def test_create_message_via_api(client, db_session):
    """Test creating a message via API endpoint"""
    # Create thread first
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    response = await client.post(f"/api/threads/{thread.id}/messages", json={
        "role": "user",
        "content": "Hello, world!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert data["content"] == "Hello, world!"
    assert data["thread_id"] == thread.id
    assert "id" in data


@pytest.mark.asyncio
async def test_create_message_with_artifact(client, db_session):
    """Test creating message with artifact data"""
    thread = await ThreadService.create_thread(
        db_session, "canvas", "gemini-2.5-flash", "gemini"
    )
    
    artifact_data = {
        "type": "code",
        "language": "python",
        "content": "print('hello')"
    }
    
    response = await client.post(f"/api/threads/{thread.id}/messages", json={
        "role": "assistant",
        "content": "Here's your code",
        "artifact_data": artifact_data
    })
    assert response.status_code == 200
    data = response.json()
    assert data["artifact_data"] == artifact_data


@pytest.mark.asyncio
async def test_create_message_with_metadata(client, db_session):
    """Test creating message with metadata"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    metadata = {
        "tokens": 100,
        "model_version": "5.0"
    }
    
    response = await client.post(f"/api/threads/{thread.id}/messages", json={
        "role": "assistant",
        "content": "Response",
        "metadata": metadata
    })
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"] == metadata


@pytest.mark.asyncio
async def test_create_message_thread_not_found(client):
    """Test creating message in non-existent thread"""
    response = await client.post("/api/threads/nonexistent-id/messages", json={
        "role": "user",
        "content": "Hello"
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_message_missing_role(client, db_session):
    """Test creating message without role"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    response = await client.post(f"/api/threads/{thread.id}/messages", json={
        "content": "Hello"
        # Missing role
    })
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_list_messages(client, db_session):
    """Test listing messages in a thread"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    # Create messages
    await MessageService.create_message(db_session, thread.id, "user", "Hello")
    await MessageService.create_message(db_session, thread.id, "assistant", "Hi there")
    await MessageService.create_message(db_session, thread.id, "user", "How are you?")
    
    response = await client.get(f"/api/threads/{thread.id}/messages")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 3
    
    # Verify order (oldest first)
    assert data["messages"][0]["content"] == "Hello"
    assert data["messages"][1]["content"] == "Hi there"
    assert data["messages"][2]["content"] == "How are you?"


@pytest.mark.asyncio
async def test_list_messages_empty_thread(client, db_session):
    """Test listing messages in thread with no messages"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    response = await client.get(f"/api/threads/{thread.id}/messages")
    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []


@pytest.mark.asyncio
async def test_delete_message(client, db_session):
    """Test deleting a message"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    message = await MessageService.create_message(
        db_session, thread.id, "user", "Delete me"
    )
    
    response = await client.delete(f"/api/messages/{message.id}")
    assert response.status_code == 200
    
    # Verify message is deleted
    deleted_message = await MessageService.get_message(db_session, message.id)
    assert deleted_message is None


@pytest.mark.asyncio
async def test_delete_message_not_found(client):
    """Test deleting non-existent message"""
    response = await client.delete("/api/messages/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_thread_cascades_messages(client, db_session):
    """Test deleting thread also deletes all messages"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    # Create messages
    msg1 = await MessageService.create_message(db_session, thread.id, "user", "Hello")
    msg2 = await MessageService.create_message(db_session, thread.id, "assistant", "Hi")
    
    # Delete thread
    response = await client.delete(f"/api/threads/{thread.id}")
    assert response.status_code == 200
    
    # Verify messages are also deleted
    deleted_msg1 = await MessageService.get_message(db_session, msg1.id)
    deleted_msg2 = await MessageService.get_message(db_session, msg2.id)
    assert deleted_msg1 is None
    assert deleted_msg2 is None


@pytest.mark.asyncio
async def test_message_service_create(db_session):
    """Test MessageService create method directly"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    message = await MessageService.create_message(
        db_session, 
        thread.id, 
        "user", 
        "Test message",
        artifact_data={"type": "test"},
        metadata={"key": "value"}
    )
    
    assert message.id is not None
    assert message.thread_id == thread.id
    assert message.role == "user"
    assert message.content == "Test message"
    assert json.loads(message.artifact_data) == {"type": "test"}
    assert json.loads(message.message_metadata) == {"key": "value"}


@pytest.mark.asyncio
async def test_message_service_list_order(db_session):
    """Test messages are listed in correct order (oldest first)"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    msg1 = await MessageService.create_message(db_session, thread.id, "user", "First")
    msg2 = await MessageService.create_message(db_session, thread.id, "assistant", "Second")
    msg3 = await MessageService.create_message(db_session, thread.id, "user", "Third")
    
    messages = await MessageService.list_messages(db_session, thread.id)
    
    # Oldest should be first
    assert messages[0].id == msg1.id
    assert messages[1].id == msg2.id
    assert messages[2].id == msg3.id
