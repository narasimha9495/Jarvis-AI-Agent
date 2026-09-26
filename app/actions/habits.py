"""Habit tracking action module.

Track daily habits, build streaks, and view completion reports
to support consistent self-improvement.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.actions.base import BaseAction
from app.db.models import Habit, HabitLog

logger = logging.getLogger(__name__)


class HabitAction(BaseAction):
    """Track daily habits and build streaks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def name(self) -> str:
        return "habits"

    @property
    def description(self) -> str:
        return "Track daily habits and build streaks"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Route to the appropriate habit sub-action."""
        action = params.get("action", "")
        handlers = {
            "create_habit": self._create_habit,
            "log_habit": self._log_habit,
            "list_habits": self._list_habits,
            "habit_report": self._habit_report,
            "delete_habit": self._delete_habit,
        }
        handler = handlers.get(action)
        if not handler:
            return {"success": False, "message": f"Unknown habit action: {action}"}
        return await handler(params)

    async def _create_habit(self, params: dict) -> dict[str, Any]:
        """Create a new habit to track."""
        try:
            name = params.get("name", "").strip()
            if not name:
                return {"success": False, "message": "Habit name is required"}

            habit = Habit(
                name=name,
                frequency=params.get("frequency", "daily"),
            )
            self._session.add(habit)
            await self._session.commit()
            await self._session.refresh(habit)

            return {
                "success": True,
                "message": f"Created habit: {name}",
                "habit_id": habit.id,
            }
        except Exception as e:
            logger.error(f"Failed to create habit: {e}")
            return {"success": False, "message": f"Failed to create habit: {e}"}

    async def _log_habit(self, params: dict) -> dict[str, Any]:
        """Log completion of a habit for today."""
        try:
            habit_id = int(params.get("habit_id", 0))

            # Check habit exists
            result = await self._session.execute(
                select(Habit).where(Habit.id == habit_id)
            )
            habit = result.scalar_one_or_none()
            if not habit:
                return {"success": False, "message": f"Habit {habit_id} not found"}

            # Check if already logged today
            today = date.today()
            existing = await self._session.execute(
                select(HabitLog).where(
                    HabitLog.habit_id == habit_id,
                    HabitLog.completed_date == today,
                )
            )
            if existing.scalar_one_or_none():
                streak = await self._calculate_streak(habit_id)
                return {
                    "success": True,
                    "message": f"Already logged '{habit.name}' today!",
                    "current_streak": streak,
                }

            # Log it
            log = HabitLog(habit_id=habit_id, completed_date=today)
            self._session.add(log)
            await self._session.commit()

            streak = await self._calculate_streak(habit_id)
            return {
                "success": True,
                "message": f"Logged '{habit.name}' ✅ Streak: {streak} day(s)",
                "current_streak": streak,
            }
        except Exception as e:
            logger.error(f"Failed to log habit: {e}")
            return {"success": False, "message": f"Failed to log habit: {e}"}

    async def _list_habits(self, params: dict) -> dict[str, Any]:
        """List all habits with current streaks."""
        try:
            result = await self._session.execute(
                select(Habit).where(Habit.active == True).order_by(Habit.created_at)
            )
            habits = result.scalars().all()

            habit_list = []
            for habit in habits:
                streak = await self._calculate_streak(habit.id)
                total = await self._session.execute(
                    select(func.count(HabitLog.id)).where(
                        HabitLog.habit_id == habit.id
                    )
                )
                total_count = total.scalar() or 0

                habit_list.append({
                    "id": habit.id,
                    "name": habit.name,
                    "frequency": habit.frequency,
                    "current_streak": streak,
                    "total_completions": total_count,
                })

            return {
                "success": True,
                "habits": habit_list,
                "message": f"Tracking {len(habit_list)} habit(s)",
            }
        except Exception as e:
            logger.error(f"Failed to list habits: {e}")
            return {"success": False, "message": f"Failed to list habits: {e}"}

    async def _habit_report(self, params: dict) -> dict[str, Any]:
        """Generate weekly or monthly habit completion report."""
        try:
            period = params.get("period", "week")
            days = 7 if period == "week" else 30
            start_date = date.today() - timedelta(days=days)

            result = await self._session.execute(
                select(Habit).where(Habit.active == True)
            )
            habits = result.scalars().all()

            report = []
            for habit in habits:
                logs = await self._session.execute(
                    select(func.count(HabitLog.id)).where(
                        HabitLog.habit_id == habit.id,
                        HabitLog.completed_date >= start_date,
                    )
                )
                completed_days = logs.scalar() or 0
                completion_rate = round((completed_days / days) * 100, 1)
                streak = await self._calculate_streak(habit.id)

                report.append({
                    "name": habit.name,
                    "completed_days": completed_days,
                    "total_days": days,
                    "completion_rate": completion_rate,
                    "streak": streak,
                })

            return {
                "success": True,
                "period": period,
                "habits": report,
                "message": f"Habit report for the last {days} days",
            }
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {"success": False, "message": f"Failed to generate report: {e}"}

    async def _delete_habit(self, params: dict) -> dict[str, Any]:
        """Delete a habit and all its logs."""
        try:
            habit_id = int(params.get("habit_id", 0))
            result = await self._session.execute(
                select(Habit).where(Habit.id == habit_id)
            )
            habit = result.scalar_one_or_none()
            if not habit:
                return {"success": False, "message": f"Habit {habit_id} not found"}

            # Delete logs first
            await self._session.execute(
                delete(HabitLog).where(HabitLog.habit_id == habit_id)
            )
            await self._session.delete(habit)
            await self._session.commit()

            return {"success": True, "message": f"Deleted habit: {habit.name}"}
        except Exception as e:
            logger.error(f"Failed to delete habit: {e}")
            return {"success": False, "message": f"Failed to delete habit: {e}"}

    async def _calculate_streak(self, habit_id: int) -> int:
        """Calculate consecutive days streak ending today."""
        streak = 0
        check_date = date.today()

        while True:
            result = await self._session.execute(
                select(HabitLog).where(
                    HabitLog.habit_id == habit_id,
                    HabitLog.completed_date == check_date,
                )
            )
            if not result.scalar_one_or_none():
                break
            streak += 1
            check_date -= timedelta(days=1)

        return streak
