"""Test cases for thread persistence endpoints."""

import pytest
from services.thread_service import ThreadService


@pytest.mark.asyncio
async def test_create_thread_via_api(client):
    """Test creating a thread via API endpoint"""
    response = await client.post("/api/threads", json={
        "agent_type": "chat",
        "model": "gpt-5-mini",
        "provider": "azure-openai"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "chat"
    assert data["model"] == "gpt-5-mini"
    assert data["provider"] == "azure-openai"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_thread_with_title(client):
    """Test creating a thread with custom title"""
    response = await client.post("/api/threads", json={
        "agent_type": "canvas",
        "model": "gemini-2.5-flash",
        "provider": "gemini",
        "title": "My Canvas Thread"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My Canvas Thread"
    assert data["agent_type"] == "canvas"


@pytest.mark.asyncio
async def test_create_thread_missing_fields(client):
    """Test creating thread with missing required fields"""
    response = await client.post("/api/threads", json={
        "agent_type": "chat"
        # Missing model and provider
    })
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_list_threads(client, db_session):
    """Test listing threads via API"""
    # Create test threads
    await ThreadService.create_thread(db_session, "chat", "gpt-5-mini", "azure-openai")
    await ThreadService.create_thread(db_session, "canvas", "gemini-2.5-flash", "gemini")
    
    response = await client.get("/api/threads")
    assert response.status_code == 200
    data = response.json()
    assert "threads" in data
    assert len(data["threads"]) >= 2


@pytest.mark.asyncio
async def test_list_threads_pagination(client, db_session):
    """Test thread list pagination"""
    # Create 5 test threads
    for i in range(5):
        await ThreadService.create_thread(
            db_session, "chat", "gpt-5-mini", "azure-openai", f"Thread {i}"
        )
    
    # Get first 3
    response = await client.get("/api/threads?limit=3&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["threads"]) == 3
    
    # Get next 2
    response = await client.get("/api/threads?limit=3&offset=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["threads"]) == 2


@pytest.mark.asyncio
async def test_get_thread(client, db_session):
    """Test getting a specific thread by ID"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai", "Test Thread"
    )
    
    response = await client.get(f"/api/threads/{thread.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thread.id
    assert data["title"] == "Test Thread"


@pytest.mark.asyncio
async def test_get_thread_not_found(client):
    """Test getting non-existent thread"""
    response = await client.get("/api/threads/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_thread(client, db_session):
    """Test updating thread metadata"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai", "Original Title"
    )
    
    response = await client.patch(f"/api/threads/{thread.id}", json={
        "title": "Updated Title"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_thread_not_found(client):
    """Test updating non-existent thread"""
    response = await client.patch("/api/threads/nonexistent-id", json={
        "title": "New Title"
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_thread(client, db_session):
    """Test deleting a thread"""
    thread = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai"
    )
    
    response = await client.delete(f"/api/threads/{thread.id}")
    assert response.status_code == 200
    
    # Verify thread is deleted
    deleted_thread = await ThreadService.get_thread(db_session, thread.id)
    assert deleted_thread is None


@pytest.mark.asyncio
async def test_delete_thread_not_found(client):
    """Test deleting non-existent thread"""
    response = await client.delete("/api/threads/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_thread_service_create(db_session):
    """Test ThreadService create method directly"""
    thread = await ThreadService.create_thread(
        db_session, "salary_viewer", "qwen:7b", "ollama", "Salary Analysis"
    )
    
    assert thread.id is not None
    assert thread.agent_type == "salary_viewer"
    assert thread.model == "qwen:7b"
    assert thread.provider == "ollama"
    assert thread.title == "Salary Analysis"
    assert thread.created_at is not None
    assert thread.updated_at is not None


@pytest.mark.asyncio
async def test_thread_service_list_order(db_session):
    """Test threads are listed in correct order (most recent first)"""
    thread1 = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai", "Thread 1"
    )
    thread2 = await ThreadService.create_thread(
        db_session, "chat", "gpt-5-mini", "azure-openai", "Thread 2"
    )
    
    threads = await ThreadService.list_threads(db_session)
    
    # Most recent should be first
    assert threads[0].id == thread2.id
    assert threads[1].id == thread1.id
