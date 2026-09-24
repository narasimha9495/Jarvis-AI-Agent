"""Tests for API endpoints."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.db.models import Base
from app.db.database import get_db


@pytest_asyncio.fixture
async def test_client():
    """Create a test client with in-memory database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async def override_get_db():
        async with session_factory() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_root(test_client):
    """Root should return something (API info or frontend)."""
    response = await test_client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_task_api(test_client):
    """POST /api/tasks should create a task."""
    response = await test_client.post("/api/tasks", json={
        "title": "Test task",
        "description": "A test task",
        "priority": "high"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test task"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks_api(test_client):
    """GET /api/tasks should return task list."""
    # Create a task first
    await test_client.post("/api/tasks", json={"title": "Task A"})
    
    response = await test_client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) >= 1


@pytest.mark.asyncio
async def test_create_note_api(test_client):
    """POST /api/notes should create a note."""
    response = await test_client.post("/api/notes", json={
        "title": "Test note",
        "content": "Some content",
        "tags": "test"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Test note"


@pytest.mark.asyncio
async def test_create_reminder_api(test_client):
    """POST /api/reminders should create a reminder."""
    response = await test_client.post("/api/reminders", json={
        "message": "Call dentist",
        "remind_at": "2026-12-25T10:00:00"
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Call dentist"
