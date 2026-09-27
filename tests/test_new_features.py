"""Tests for new feature modules: weather, expenses, pomodoro, habits, system monitor, daily summary."""

import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db.models import Base
from app.actions.expenses import ExpenseAction
from app.actions.habits import HabitAction
from app.actions.pomodoro import PomodoroAction
from app.actions.system_monitor import SystemMonitorAction
from app.actions.daily_summary import DailySummaryAction
from app.core.safety import SafetyEngine, RiskLevel


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


# ── Expense Tests ──


@pytest.mark.asyncio
async def test_add_expense(db_session):
    """Should add an expense successfully."""
    action = ExpenseAction(db_session)
    result = await action.execute({
        "action": "add_expense",
        "amount": 25.50,
        "category": "food",
        "description": "Lunch"
    })
    assert result["success"] is True
    assert result["amount"] == 25.50
    assert result["category"] == "food"


@pytest.mark.asyncio
async def test_list_expenses(db_session):
    """Should list expenses after adding them."""
    action = ExpenseAction(db_session)
    await action.execute({"action": "add_expense", "amount": 10, "category": "food"})
    await action.execute({"action": "add_expense", "amount": 50, "category": "transport"})
    result = await action.execute({"action": "list_expenses"})
    assert result["success"] is True
    assert len(result["expenses"]) == 2
    assert result["total"] == 60.0


@pytest.mark.asyncio
async def test_spending_summary(db_session):
    """Should generate spending summary grouped by category."""
    action = ExpenseAction(db_session)
    await action.execute({"action": "add_expense", "amount": 20, "category": "food"})
    await action.execute({"action": "add_expense", "amount": 30, "category": "food"})
    await action.execute({"action": "add_expense", "amount": 15, "category": "transport"})
    result = await action.execute({"action": "spending_summary", "period": "month"})
    assert result["success"] is True
    assert result["grand_total"] == 65.0


@pytest.mark.asyncio
async def test_invalid_expense_amount(db_session):
    """Should reject negative or zero amounts."""
    action = ExpenseAction(db_session)
    result = await action.execute({"action": "add_expense", "amount": -5})
    assert result["success"] is False


# ── Habit Tests ──


@pytest.mark.asyncio
async def test_create_habit(db_session):
    """Should create a habit."""
    action = HabitAction(db_session)
    result = await action.execute({"action": "create_habit", "name": "Exercise"})
    assert result["success"] is True
    assert "Exercise" in result["message"]


@pytest.mark.asyncio
async def test_log_habit(db_session):
    """Should log a habit and calculate streak."""
    action = HabitAction(db_session)
    create_result = await action.execute({"action": "create_habit", "name": "Read"})
    habit_id = create_result["habit_id"]
    
    log_result = await action.execute({"action": "log_habit", "habit_id": habit_id})
    assert log_result["success"] is True
    assert log_result["current_streak"] >= 1


@pytest.mark.asyncio
async def test_duplicate_habit_log(db_session):
    """Should prevent duplicate daily logs."""
    action = HabitAction(db_session)
    create_result = await action.execute({"action": "create_habit", "name": "Meditate"})
    habit_id = create_result["habit_id"]
    
    await action.execute({"action": "log_habit", "habit_id": habit_id})
    duplicate = await action.execute({"action": "log_habit", "habit_id": habit_id})
    assert duplicate["success"] is True
    assert "Already logged" in duplicate["message"]


@pytest.mark.asyncio
async def test_habit_report(db_session):
    """Should generate a habit report."""
    action = HabitAction(db_session)
    await action.execute({"action": "create_habit", "name": "Walk"})
    result = await action.execute({"action": "habit_report", "period": "week"})
    assert result["success"] is True
    assert result["period"] == "week"


# ── Pomodoro Tests ──


@pytest.mark.asyncio
async def test_start_pomodoro():
    """Should start a pomodoro session."""
    action = PomodoroAction()
    result = await action.execute({"action": "start", "task": "Study Python"})
    assert result["success"] is True
    assert "session_id" in result
    assert result["task"] == "Study Python"


@pytest.mark.asyncio
async def test_pomodoro_status():
    """Should return pomodoro status."""
    action = PomodoroAction()
    start_result = await action.execute({"action": "start", "task": "Code review"})
    session_id = start_result["session_id"]
    
    status_result = await action.execute({"action": "status", "session_id": session_id})
    assert status_result["success"] is True
    assert status_result["task"] == "Code review"


@pytest.mark.asyncio
async def test_pomodoro_complete():
    """Should complete a pomodoro session."""
    action = PomodoroAction()
    start_result = await action.execute({"action": "start", "task": "Write docs"})
    session_id = start_result["session_id"]
    
    complete_result = await action.execute({"action": "complete", "session_id": session_id})
    assert complete_result["success"] is True
    assert complete_result["completed_pomodoros"] >= 1


# ── System Monitor Tests ──


@pytest.mark.asyncio
async def test_system_status():
    """Should return system status."""
    action = SystemMonitorAction()
    result = await action.execute({"action": "system_status"})
    assert result["success"] is True
    assert "cpu_percent" in result
    assert "memory" in result
    assert "disk" in result


@pytest.mark.asyncio
async def test_cpu_alert():
    """Should check CPU against threshold."""
    action = SystemMonitorAction()
    result = await action.execute({"action": "cpu_alert", "threshold": 99})
    assert result["success"] is True
    assert "above_threshold" in result


@pytest.mark.asyncio
async def test_top_processes():
    """Should list top processes."""
    action = SystemMonitorAction()
    result = await action.execute({"action": "top_processes"})
    assert result["success"] is True
    assert "processes" in result


# ── Daily Summary Tests ──


@pytest.mark.asyncio
async def test_daily_summary(db_session):
    """Should generate a daily productivity summary."""
    action = DailySummaryAction(db_session)
    result = await action.execute({"action": "generate_summary"})
    assert result["success"] is True
    assert "productivity_score" in result
    assert 0 <= result["productivity_score"] <= 100
    assert "summary" in result


@pytest.mark.asyncio
async def test_weekly_report(db_session):
    """Should generate a weekly report."""
    action = DailySummaryAction(db_session)
    result = await action.execute({"action": "weekly_report"})
    assert result["success"] is True
    assert "trends" in result


# ── Safety Engine Tests for New Actions ──


@pytest.fixture
def safety():
    return SafetyEngine()


@pytest.mark.asyncio
async def test_weather_is_safe(safety):
    """Weather lookups should be safe."""
    result = await safety.check_action("get_weather")
    assert result.allowed is True
    assert result.risk_level == RiskLevel.SAFE


@pytest.mark.asyncio
async def test_add_expense_is_moderate(safety):
    """Adding expenses should be moderate risk."""
    result = await safety.check_action("add_expense")
    assert result.risk_level == RiskLevel.MODERATE


@pytest.mark.asyncio
async def test_delete_expense_is_dangerous(safety):
    """Deleting expenses should require confirmation."""
    result = await safety.check_action("delete_expense")
    assert result.risk_level == RiskLevel.DANGEROUS
    assert result.requires_confirmation is True


@pytest.mark.asyncio
async def test_system_monitor_is_safe(safety):
    """System monitoring should be safe."""
    result = await safety.check_action("system_status")
    assert result.allowed is True
    assert result.risk_level == RiskLevel.SAFE
