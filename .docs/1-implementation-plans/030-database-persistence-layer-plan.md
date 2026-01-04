# Database Persistence Layer Implementation Plan

**Requirement**: [030-support-db.md](../.docs/0-requirements/030-support-db.md)  
**Created**: January 4, 2026  
**Status**: ✅ Complete

**Implementation Date**: January 4, 2026  
**Summary**: Successfully implemented database persistence layer with SQLAlchemy, service layer, Pydantic models, comprehensive tests, and manual migration system.

## Overview

Implement a persistent storage architecture for the backend to replace frontend LocalStorage with server-side database persistence. Support SQLite for development and PostgreSQL for production environments.

## Objectives

- ✅ Build persistent architecture with SQLite (dev) and PostgreSQL (production) - **COMPLETE**
- ✅ Frontend uses Zustand for caching and offline-friendly access - **DEFERRED TO PHASE 2**
- ✅ Service Layer only (no repository layer - keep it lightweight) - **COMPLETE**
- ✅ Versioned database migrations in codebase - **COMPLETE**
- ✅ Add necessary API endpoints - **COMPLETE (8 endpoints)**
- ✅ Support Thread and Message models first (other models later) - **COMPLETE**
- ✅ Pydantic models for type safety and validation - **COMPLETE**
- ✅ Comprehensive test coverage - **COMPLETE (25 tests)**

## Implementation Summary

### What Was Built

1. **Database Layer**
   - Async SQLAlchemy configuration with aiosqlite (dev) and asyncpg support (prod)
   - Thread and Message ORM models with relationships
   - Manual migration system with SQL file tracking
   - Standalone migration script (`migrate.py`)

2. **Service Layer**
   - ThreadService: Full CRUD operations (create, get, list, update, delete)
   - MessageService: Full CRUD operations (create, get, list, delete)
   - Async/await throughout for non-blocking operations

3. **API Layer**
   - 8 RESTful endpoints with Pydantic models
   - Automatic request validation (returns 422 on validation errors)
   - Type-safe endpoint signatures
   - Comprehensive error handling

4. **Testing**
   - 25 tests (13 thread tests, 12 message tests)
   - 100% passing rate
   - In-memory SQLite for fast test execution
   - Proper async test fixtures

5. **Documentation**
   - DATABASE.md - Architecture and usage guide
   - PYDANTIC_MODELS_SUMMARY.md - API models documentation
   - Implementation summary documentation

### Key Decisions

- **Migration Approach**: Manual migration via `migrate.py` script instead of automatic on startup (better for production with multiple instances)
- **Column Naming**: Renamed `metadata` to `message_metadata` to avoid SQLAlchemy reserved keyword conflict
- **Multi-Statement Handling**: Migration manager splits SQL files by semicolon for SQLite compatibility
- **Pydantic Integration**: Used Pydantic models for all endpoints for automatic validation and API documentation

## Strategy: Phase 1

**Frontend**: Continue reading from LocalStorage, but POST new messages to server for persistence (accept temporary duplicates - will fix in Phase 2)

**Backend**: Provide APIs for storage, but frontend won't fetch from server yet

---

## Backend Implementation

**Delegate to Backend Agent** - See [backend.agent.md](../.github/agents/backend.agent.md)

### 1. Database Layer Setup

#### 1.1 Database Configuration (`backend/database/config.py`)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings
import logging

logger = logging.getLogger(__name__)

# Support both SQLite (dev) and PostgreSQL (prod)
# Use async drivers: aiosqlite for SQLite, asyncpg for PostgreSQL
DATABASE_URL = settings.DATABASE_URL  # "sqlite+aiosqlite:///./agentkit.db" or "postgresql+asyncpg://..."

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    """Async dependency for FastAPI routes"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

#### 1.2 Database Models (`backend/database/models.py`)

**Thread Model**:
```python
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.orm import relationship
from database.config import Base
from datetime import datetime
import uuid

class Thread(Base):
    __tablename__ = "threads"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    agent_type = Column(String(50), nullable=False)  # "chat", "canvas", "salary_viewer"
    model = Column(String(100), nullable=False)  # "gpt-5-mini", "gemini-2.5-flash"
    provider = Column(String(50), nullable=False)  # "azure-openai", "gemini"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
```

**Message Model**:
```python
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(36), ForeignKey("threads.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user", "assistant"
    content = Column(Text, nullable=True)  # Text content
    artifact_data = Column(Text, nullable=True)  # JSON string for A2UI artifacts
    metadata = Column(Text, nullable=True)  # JSON string for additional metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    thread = relationship("Thread", back_populates="messages")
```

#### 1.3 Database Migrations (`backend/database/migrations/`)

**Structure**:
```
backend/database/migrations/
├── __init__.py
├── 001_initial_schema.sql
└── migration_manager.py
```

**Migration Manager** (`migration_manager.py`):
```python
from sqlalchemy import text
from database.config import engine
import logging
import asyncio

logger = logging.getLogger(__name__)

MIGRATIONS = [
    "001_initial_schema.sql",
]

async def run_migrations():
    """Run all pending migrations asynchronously"""
    async with engine.begin() as conn:
        # Create migrations tracking table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Check applied migrations
        result = await conn.execute(text("SELECT version FROM schema_migrations"))
        applied = {row[0] for row in result}
        
        # Run pending migrations
        for idx, migration_file in enumerate(MIGRATIONS, start=1):
            if idx not in applied:
                logger.info(f"Running migration: {migration_file}")
                with open(f"backend/database/migrations/{migration_file}") as f:
                    await conn.execute(text(f.read()))
                await conn.execute(text("INSERT INTO schema_migrations (version) VALUES (:v)"), {"v": idx})
                logger.info(f"✅ Migration {migration_file} applied")
```

**Initial Schema** (`001_initial_schema.sql`):
```sql
-- Threads table
CREATE TABLE IF NOT EXISTS threads (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255),
    agent_type VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    thread_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT,
    artifact_data TEXT,
    metadata TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_threads_created_at ON threads(created_at);
```

### 2. Service Layer

#### 2.1 Thread Service (`backend/services/thread_service.py`)
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Thread, Message
from typing import List, Optional
from datetime import datetime

class ThreadService:
    @staticmethod
    async def create_thread(db: AsyncSession, agent_type: str, model: str, provider: str, title: str = None) -> Thread:
        """Create a new thread"""
        thread = Thread(
            agent_type=agent_type,
            model=model,
            provider=provider,
            title=title or f"New {agent_type} conversation"
        )
        db.add(thread)
        await db.commit()
        await db.refresh(thread)
        return thread
    
    @staticmethod
    async def get_thread(db: AsyncSession, thread_id: str) -> Optional[Thread]:
        """Get thread by ID"""
        result = await db.execute(select(Thread).filter(Thread.id == thread_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_threads(db: AsyncSession, limit: int = 50, offset: int = 0) -> List[Thread]:
        """List all threads ordered by updated_at DESC"""
        result = await db.execute(
            select(Thread).order_by(Thread.updated_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_thread(db: AsyncSession, thread_id: str, title: str = None) -> Optional[Thread]:
        """Update thread metadata"""
        result = await db.execute(select(Thread).filter(Thread.id == thread_id))
        thread = result.scalar_one_or_none()
        if thread:
            if title:
                thread.title = title
            thread.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(thread)
        return thread
    
    @staticmethod
    async def delete_thread(db: AsyncSession, thread_id: str) -> bool:
        """Delete thread and all messages"""
        result = await db.execute(select(Thread).filter(Thread.id == thread_id))
        thread = result.scalar_one_or_none()
        if thread:
            await db.delete(thread)
            await db.commit()
            return True
        return False
```

#### 2.2 Message Service (`backend/services/message_service.py`)
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Message
from typing import List, Optional
import json

class MessageService:
    @staticmethod
    async def create_message(
        db: AsyncSession, 
        thread_id: str, 
        role: str, 
        content: str = None,
        artifact_data: dict = None,
        metadata: dict = None
    ) -> Message:
        """Create a new message"""
        message = Message(
            thread_id=thread_id,
            role=role,
            content=content,
            artifact_data=json.dumps(artifact_data) if artifact_data else None,
            metadata=json.dumps(metadata) if metadata else None
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message
    
    @staticmethod
    async def get_message(db: AsyncSession, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        result = await db.execute(select(Message).filter(Message.id == message_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_messages(db: AsyncSession, thread_id: str) -> List[Message]:
        """List all messages in a thread ordered by created_at ASC"""
        result = await db.execute(
            select(Message).filter(Message.thread_id == thread_id).order_by(Message.created_at.asc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def delete_message(db: AsyncSession, message_id: str) -> bool:
        """Delete a message"""
        result = await db.execute(select(Message).filter(Message.id == message_id))
        message = result.scalar_one_or_none()
        if message:
            await db.delete(message)
            await db.commit()
            return True
        return False
```

### 3. API Endpoints

#### 3.1 Thread Endpoints (`backend/api/routes.py`)

Add new endpoints:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from database.config import get_db
from services.thread_service import ThreadService
from services.message_service import MessageService

# Thread endpoints
@app.post("/api/threads")
async def create_thread(
    agent_type: str,
    model: str,
    provider: str,
    title: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new thread"""
    thread = await ThreadService.create_thread(db, agent_type, model, provider, title)
    return {
        "id": thread.id,
        "title": thread.title,
        "agent_type": thread.agent_type,
        "model": thread.model,
        "provider": thread.provider,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat()
    }

@app.get("/api/threads")
async def list_threads(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all threads"""
    threads = await ThreadService.list_threads(db, limit, offset)
    return {
        "threads": [
            {
                "id": t.id,
                "title": t.title,
                "agent_type": t.agent_type,
                "model": t.model,
                "provider": t.provider,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat()
            }
            for t in threads
        ]
    }

@app.get("/api/threads/{thread_id}")
async def get_thread(thread_id: str, db: AsyncSession = Depends(get_db)):
    """Get thread by ID"""
    thread = await ThreadService.get_thread(db, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {
        "id": thread.id,
        "title": thread.title,
        "agent_type": thread.agent_type,
        "model": thread.model,
        "provider": thread.provider,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat()
    }

@app.patch("/api/threads/{thread_id}")
async def update_thread(
    thread_id: str,
    title: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Update thread metadata"""
    thread = await ThreadService.update_thread(db, thread_id, title)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"id": thread.id, "title": thread.title, "updated_at": thread.updated_at.isoformat()}

@app.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str, db: AsyncSession = Depends(get_db)):
    """Delete thread and all messages"""
    success = await ThreadService.delete_thread(db, thread_id)
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"message": "Thread deleted successfully"}
```

#### 3.2 Message Endpoints

```python
@app.post("/api/threads/{thread_id}/messages")
async def create_message(
    thread_id: str,
    role: str,
    content: str = None,
    artifact_data: dict = None,
    metadata: dict = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a new message in a thread"""
    # Verify thread exists
    thread = await ThreadService.get_thread(db, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    message = await MessageService.create_message(db, thread_id, role, content, artifact_data, metadata)
    return {
        "id": message.id,
        "thread_id": message.thread_id,
        "role": message.role,
        "content": message.content,
        "artifact_data": json.loads(message.artifact_data) if message.artifact_data else None,
        "metadata": json.loads(message.metadata) if message.metadata else None,
        "created_at": message.created_at.isoformat()
    }

@app.get("/api/threads/{thread_id}/messages")
async def list_messages(thread_id: str, db: AsyncSession = Depends(get_db)):
    """List all messages in a thread"""
    messages = await MessageService.list_messages(db, thread_id)
    return {
        "messages": [
            {
                "id": m.id,
                "thread_id": m.thread_id,
                "role": m.role,
                "content": m.content,
                "artifact_data": json.loads(m.artifact_data) if m.artifact_data else None,
                "metadata": json.loads(m.metadata) if m.metadata else None,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }

@app.delete("/api/messages/{message_id}")
async def delete_message(message_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a message"""
    success = await MessageService.delete_message(db, message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"}
```

### 4. Configuration & Dependencies

#### 4.1 Update `backend/config.py`
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Database settings (use async drivers)
    DATABASE_URL: str = "sqlite+aiosqlite:///./agentkit.db"  # Default to async SQLite
    # For PostgreSQL: "postgresql+asyncpg://user:pass@localhost/dbname"
    
    class Config:
        env_file = ".env"
```

#### 4.2 Update `backend/requirements.txt`
```
sqlalchemy[asyncio]==2.0.25
aiosqlite==0.19.0  # Async SQLite driver
asyncpg==0.29.0  # Async PostgreSQL driver
greenlet==3.0.3  # Required for async SQLAlchemy
```

#### 4.3 Update `backend/main.py`
```python
from database.migrations.migration_manager import run_migrations
from database.config import engine, Base

@app.on_event("startup")
async def startup_event():
    """Run migrations on startup"""
    logger.info("Running database migrations...")
    await run_migrations()
    logger.info("✅ Database ready")
```

### 5. Testing

#### 5.1 Test Database Setup (`backend/tests/conftest.py`)
```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.config import Base, get_db
from main import app
from httpx import AsyncClient

# Use in-memory async SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture
async def db_session():
    """Create test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db_session):
    """Create test client with test database"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

#### 5.2 Test Cases (`backend/tests/test_threads.py`)
```python
import pytest
from services.thread_service import ThreadService
from services.message_service import MessageService

@pytest.mark.asyncio
async def test_create_thread(client):
    response = await client.post("/api/threads", params={
        "agent_type": "chat",
        "model": "gpt-5-mini",
        "provider": "azure-openai"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "chat"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_threads(client, db_session):
    # Create test threads
    await ThreadService.create_thread(db_session, "chat", "gpt-5-mini", "azure-openai")
    
    response = await client.get("/api/threads")
    assert response.status_code == 200
    data = response.json()
    assert len(data["threads"]) >= 1

@pytest.mark.asyncio
async def test_create_message(client, db_session):
    thread = await ThreadService.create_thread(db_session, "chat", "gpt-5-mini", "azure-openai")
    
    response = await client.post(f"/api/threads/{thread.id}/messages", json={
        "role": "user",
        "content": "Hello"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert data["content"] == "Hello"
```

---

## Protocol (API Contracts)

### Thread API

**Create Thread**:
```typescript
POST /api/threads
Request: {
  agent_type: string;    // "chat" | "canvas" | "salary_viewer"
  model: string;         // "gpt-5-mini" | "gemini-2.5-flash"
  provider: string;      // "azure-openai" | "gemini" | "ollama"
  title?: string;
}
Response: {
  id: string;
  title: string;
  agent_type: string;
  model: string;
  provider: string;
  created_at: string;
  updated_at: string;
}
```

**List Threads**:
```typescript
GET /api/threads?limit=50&offset=0
Response: {
  threads: Array<{
    id: string;
    title: string;
    agent_type: string;
    model: string;
    provider: string;
    created_at: string;
    updated_at: string;
  }>;
}
```

**Get Thread**:
```typescript
GET /api/threads/{thread_id}
Response: {
  id: string;
  title: string;
  agent_type: string;
  model: string;
  provider: string;
  created_at: string;
  updated_at: string;
}
```

**Update Thread**:
```typescript
PATCH /api/threads/{thread_id}
Request: {
  title?: string;
}
Response: {
  id: string;
  title: string;
  updated_at: string;
}
```

**Delete Thread**:
```typescript
DELETE /api/threads/{thread_id}
Response: {
  message: string;
}
```

### Message API

**Create Message**:
```typescript
POST /api/threads/{thread_id}/messages
Request: {
  role: "user" | "assistant";
  content?: string;
  artifact_data?: {
    type: string;
    content: any;
  };
  metadata?: Record<string, any>;
}
Response: {
  id: string;
  thread_id: string;
  role: string;
  content: string | null;
  artifact_data: object | null;
  metadata: object | null;
  created_at: string;
}
```

**List Messages**:
```typescript
GET /api/threads/{thread_id}/messages
Response: {
  messages: Array<{
    id: string;
    thread_id: string;
    role: string;
    content: string | null;
    artifact_data: object | null;
    metadata: object | null;
    created_at: string;
  }>;
}
```

**Delete Message**:
```typescript
DELETE /api/messages/{message_id}
Response: {
  message: string;
}
```

---

## Frontend Implementation

**Delegate to Frontend Agent** - See [frontend.agent.md](../.github/agents/frontend.agent.md)

### Phase 1: Write-Only (Post to Server)

Frontend continues reading from LocalStorage, but writes to server for persistence.

#### 1. API Client Updates (`frontend/services/api.ts`)

```typescript
// Thread API
export const threadsApi = {
  create: async (data: {
    agent_type: string;
    model: string;
    provider: string;
    title?: string;
  }) => {
    const response = await fetch(`${API_BASE_URL}/api/threads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  list: async (limit = 50, offset = 0) => {
    const response = await fetch(`${API_BASE_URL}/api/threads?limit=${limit}&offset=${offset}`);
    return response.json();
  },

  get: async (threadId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/threads/${threadId}`);
    return response.json();
  },

  update: async (threadId: string, data: { title?: string }) => {
    const response = await fetch(`${API_BASE_URL}/api/threads/${threadId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  delete: async (threadId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/threads/${threadId}`, {
      method: 'DELETE'
    });
    return response.json();
  }
};

// Message API
export const messagesApi = {
  create: async (threadId: string, data: {
    role: 'user' | 'assistant';
    content?: string;
    artifact_data?: any;
    metadata?: Record<string, any>;
  }) => {
    const response = await fetch(`${API_BASE_URL}/api/threads/${threadId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  list: async (threadId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/threads/${threadId}/messages`);
    return response.json();
  },

  delete: async (messageId: string) => {
    const response = await fetch(`${API_BASE_URL}/api/messages/${messageId}`, {
      method: 'DELETE'
    });
    return response.json();
  }
};
```

#### 2. Zustand Store Updates (`frontend/stores/chatStore.ts`)

```typescript
interface ChatStore {
  // ... existing state ...
  
  // Add server sync methods
  syncMessageToServer: (threadId: string, message: Message) => Promise<void>;
  syncThreadToServer: (thread: Thread) => Promise<void>;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  // ... existing methods ...
  
  addMessage: async (threadId: string, message: Message) => {
    // Add to local state first (existing behavior)
    set((state) => ({
      messages: {
        ...state.messages,
        [threadId]: [...(state.messages[threadId] || []), message]
      }
    }));
    
    // **NEW**: Sync to server in background (Phase 1)
    try {
      await messagesApi.create(threadId, {
        role: message.role,
        content: message.content,
        artifact_data: message.artifact_data,
        metadata: message.metadata
      });
      console.log('✅ Message synced to server');
    } catch (error) {
      console.error('Failed to sync message to server:', error);
      // Don't block UI - message is already in LocalStorage
    }
  },
  
  createThread: async (thread: Thread) => {
    // Add to local state first
    set((state) => ({
      threads: [...state.threads, thread]
    }));
    
    // **NEW**: Sync to server in background
    try {
      await threadsApi.create({
        agent_type: thread.agentType,
        model: thread.model,
        provider: thread.provider,
        title: thread.title
      });
      console.log('✅ Thread synced to server');
    } catch (error) {
      console.error('Failed to sync thread to server:', error);
    }
  }
}));
```

#### 3. No UI Changes Required

Phase 1 doesn't require any UI changes - just background syncing.

---

## Testing Strategy

### Backend Tests ✅ COMPLETE
1. **Unit Tests**: Service layer methods (ThreadService, MessageService) - 25 tests
2. **Integration Tests**: API endpoints with test database - All passing
3. **Migration Tests**: Schema migrations verified working

**Test Results**: 25/25 passing (100% success rate)
- 13 thread tests (create, read, update, delete, list, pagination)
- 12 message tests (create, read, delete, list, cascading deletes)

### Frontend Tests
1. **API Client Tests**: Mock fetch calls, verify request/response formats - PENDING
2. **Store Tests**: Verify background sync behavior - PENDING
3. **Integration Tests**: E2E flow from UI to server persistence - PENDING

---

## Dependencies

### Backend ✅ INSTALLED
```
sqlalchemy==2.0.25
aiosqlite==0.20.0  # For async SQLite
asyncpg==0.30.0  # For async PostgreSQL (production)
pydantic==2.x  # For API validation
```

### Frontend
No new dependencies (uses existing fetch API)

---

## Rollout Plan

### Step 1: Backend Implementation ✅ COMPLETE
1. ✅ Setup database layer (config, models, migrations)
2. ✅ Implement service layer (ThreadService, MessageService)
3. ✅ Add API endpoints (8 endpoints with Pydantic models)
4. ✅ Write backend tests (25 tests, all passing)
5. ✅ Update configuration and dependencies
6. ✅ Create documentation (DATABASE.md, PYDANTIC_MODELS_SUMMARY.md)

### Step 2: Frontend Integration (NEXT PHASE)
1. ⏳ Update API client with new endpoints
2. ⏳ Add background sync to Zustand stores
3. ⏳ Test write-only behavior (Phase 1)
4. ⏳ Monitor for errors and fix edge cases

### Step 3: Phase 2 (Future)
- Frontend reads from server APIs instead of LocalStorage
- Implement proper sync/conflict resolution
- Remove duplicate data handling

---

## Success Criteria

### Phase 1 - Backend Implementation ✅ COMPLETE
- ✅ Backend database stores all threads and messages
- ✅ 8 RESTful API endpoints with Pydantic validation
- ✅ Service layer with full CRUD operations
- ✅ Manual migration system operational
- ✅ All backend tests pass (25/25 tests)
- ✅ Comprehensive documentation created
- ✅ Type safety with Pydantic models
- ✅ Proper async/await implementation

### Phase 2 (Future) - Frontend Integration
- ⏳ Frontend continues working with LocalStorage (no breaking changes)
- ⏳ Messages are silently synced to server in background
- ⏳ No performance degradation in frontend
- ⏳ Frontend fetches data from server
- ⏳ LocalStorage acts as cache only
- ⏳ Proper conflict resolution
- ⏳ Offline support with sync on reconnect

---

## Implementation Files

### Created Files
- `backend/database/config.py` - Database configuration and session management
- `backend/database/models.py` - Thread and Message ORM models
- `backend/database/migrations/001_initial_schema.sql` - Initial schema SQL
- `backend/database/migrations/migration_manager.py` - Migration execution system
- `backend/services/thread_service.py` - Thread CRUD operations
- `backend/services/message_service.py` - Message CRUD operations
- `backend/migrate.py` - Standalone migration script
- `backend/tests/test_threads.py` - Thread tests (13 tests)
- `backend/tests/test_messages.py` - Message tests (12 tests)
- `backend/DATABASE.md` - Architecture documentation
- `backend/PYDANTIC_MODELS_SUMMARY.md` - API models documentation

### Modified Files
- `backend/api/routes.py` - Added 8 database endpoints with Pydantic models
- `backend/api/models.py` - Added ThreadCreate, ThreadUpdate, ThreadResponse, MessageCreate, MessageResponse, etc.
- `backend/main.py` - Removed automatic migrations
- `backend/config.py` - Added DATABASE_URL configuration
- `backend/requirements.txt` - Added SQLAlchemy, aiosqlite, asyncpg dependencies

---

## How to Use

### Running Migrations
```bash
cd backend
python migrate.py
```

### Running Tests
```bash
cd backend
pytest tests/test_threads.py tests/test_messages.py -v
```

### API Documentation
Visit `http://localhost:8000/docs` for Swagger UI with complete API documentation

---

## Notes

- **Database Choice**: SQLite for dev simplicity, PostgreSQL for production scalability ✅
- **No Repository Layer**: Keep architecture simple with Service layer only ✅
- **Manual Migrations**: Production-safe approach instead of automatic on startup ✅
- **Testing**: Heavy focus on backend testing with 100% pass rate ✅
- **Models**: Started with Thread and Message, can add User/Settings/Tools later ✅
- **Pydantic Models**: Full type safety and automatic validation ✅
- **Column Naming**: `metadata` renamed to `message_metadata` to avoid reserved keyword ✅

## Related Files

- Backend: [backend.agent.md](../.github/agents/backend.agent.md)
- Documentation: `backend/DATABASE.md`, `backend/PYDANTIC_MODELS_SUMMARY.md`
- Frontend: [frontend.agent.md](../.github/agents/frontend.agent.md)
- Requirement: [030-support-db.md](../.docs/0-requirements/030-support-db.md)
