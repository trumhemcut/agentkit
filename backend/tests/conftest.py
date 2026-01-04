"""Test configuration and fixtures for pytest."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database.config import Base, get_db
from main import app
from httpx import AsyncClient

# Use in-memory async SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session():
    """
    Create test database session.
    
    Sets up an in-memory SQLite database for each test,
    creates all tables, yields the session for testing,
    and tears down the database after the test completes.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide session for test
    async with TestingSessionLocal() as session:
        yield session
    
    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """
    Create test HTTP client with test database.
    
    Overrides the database dependency to use the test database
    instead of the production database.
    
    Args:
        db_session: Test database session fixture
    
    Yields:
        AsyncClient: HTTP client for testing API endpoints
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
