"""Tests for action modules."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db.models import Base
from app.actions.tasks import TaskAction
from app.actions.reminders import ReminderAction
from app.actions.notes import NoteAction


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_task(db_session):
    """Should create a task successfully."""
    action = TaskAction(db_session)
    result = await action.execute({
        "action": "create_task",
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "priority": "high"
    })
    assert result["success"] is True
    assert "Buy groceries" in result["message"]


@pytest.mark.asyncio
async def test_list_tasks(db_session):
    """Should list tasks after creation."""
    action = TaskAction(db_session)
    await action.execute({
        "action": "create_task",
        "title": "Task 1"
    })
    result = await action.execute({"action": "list_tasks"})
    assert result["success"] is True
    assert len(result["tasks"]) == 1


@pytest.mark.asyncio
async def test_complete_task(db_session):
    """Should mark a task as completed."""
    action = TaskAction(db_session)
    create_result = await action.execute({
        "action": "create_task",
        "title": "Finish homework"
    })
    task_id = create_result["task_id"]
    
    result = await action.execute({
        "action": "complete_task",
        "task_id": task_id
    })
    assert result["success"] is True


@pytest.mark.asyncio
async def test_create_reminder(db_session):
    """Should create a reminder."""
    action = ReminderAction(db_session)
    result = await action.execute({
        "action": "create_reminder",
        "message": "Call mom",
        "remind_at": "2026-12-25T10:00:00"
    })
    assert result["success"] is True


@pytest.mark.asyncio
async def test_create_note(db_session):
    """Should create a note."""
    action = NoteAction(db_session)
    result = await action.execute({
        "action": "create_note",
        "title": "Meeting notes",
        "content": "Discussed Q4 roadmap",
        "tags": "work,meeting"
    })
    assert result["success"] is True


@pytest.mark.asyncio
async def test_search_notes(db_session):
    """Should search notes by keyword."""
    action = NoteAction(db_session)
    await action.execute({
        "action": "create_note",
        "title": "Python tips",
        "content": "Use list comprehensions for cleaner code"
    })
    result = await action.execute({
        "action": "search_notes",
        "keyword": "Python"
    })
    assert result["success"] is True
    assert len(result["notes"]) >= 1
