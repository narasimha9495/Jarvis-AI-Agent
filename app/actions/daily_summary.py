"""Daily productivity summary action module.

Generate AI-powered daily and weekly productivity reports
with a productivity score based on task completion, habits, and more.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.actions.base import BaseAction
from app.db.models import Task, Reminder, Note, Expense, Habit, HabitLog

logger = logging.getLogger(__name__)


class DailySummaryAction(BaseAction):
    """Generate productivity summaries and insights."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def name(self) -> str:
        return "daily_summary"

    @property
    def description(self) -> str:
        return "Generate AI-powered daily productivity summary and insights"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Route to the appropriate summary sub-action."""
        action = params.get("action", "")
        handlers = {
            "generate_summary": self._generate_summary,
            "weekly_report": self._weekly_report,
        }
        handler = handlers.get(action)
        if not handler:
            return {"success": False, "message": f"Unknown summary action: {action}"}
        return await handler(params)

    async def _generate_summary(self, params: dict) -> dict[str, Any]:
        """Generate today's productivity summary."""
        try:
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())

            # Tasks
            tasks_created = await self._count(
                select(func.count(Task.id)).where(
                    Task.created_at.between(today_start, today_end)
                )
            )
            tasks_completed = await self._count(
                select(func.count(Task.id)).where(
                    Task.completed == True,
                    Task.created_at.between(today_start, today_end),
                )
            )

            # Reminders
            reminders_set = await self._count(
                select(func.count(Reminder.id)).where(
                    Reminder.created_at.between(today_start, today_end)
                )
            )

            # Notes
            notes_created = await self._count(
                select(func.count(Note.id)).where(
                    Note.created_at.between(today_start, today_end)
                )
            )

            # Expenses
            expense_result = await self._session.execute(
                select(func.sum(Expense.amount)).where(Expense.date == today)
            )
            expenses_total = round(expense_result.scalar() or 0, 2)

            # Habits
            habits_logged = await self._count(
                select(func.count(HabitLog.id)).where(
                    HabitLog.completed_date == today
                )
            )

            # Overdue tasks
            overdue = await self._count(
                select(func.count(Task.id)).where(
                    Task.completed == False,
                    Task.due_date < today_start,
                )
            )

            # Calculate productivity score
            score = self._calculate_score(
                tasks_completed, tasks_created, habits_logged, overdue
            )
            message = self._score_message(score)

            return {
                "success": True,
                "date": str(today),
                "summary": {
                    "tasks_created": tasks_created,
                    "tasks_completed": tasks_completed,
                    "reminders_set": reminders_set,
                    "notes_created": notes_created,
                    "expenses_total": expenses_total,
                    "habits_logged": habits_logged,
                    "overdue_tasks": overdue,
                },
                "productivity_score": score,
                "message": message,
            }
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {"success": False, "message": f"Failed to generate summary: {e}"}

    async def _weekly_report(self, params: dict) -> dict[str, Any]:
        """Generate a weekly productivity report with trends."""
        try:
            today = date.today()
            week_start = today - timedelta(days=7)
            prev_week_start = today - timedelta(days=14)

            week_start_dt = datetime.combine(week_start, datetime.min.time())
            prev_week_start_dt = datetime.combine(prev_week_start, datetime.min.time())
            today_dt = datetime.combine(today, datetime.max.time())

            # This week stats
            tasks_this_week = await self._count(
                select(func.count(Task.id)).where(
                    Task.completed == True,
                    Task.created_at.between(week_start_dt, today_dt),
                )
            )
            habits_this_week = await self._count(
                select(func.count(HabitLog.id)).where(
                    HabitLog.completed_date >= week_start
                )
            )

            # Last week stats (for trends)
            tasks_last_week = await self._count(
                select(func.count(Task.id)).where(
                    Task.completed == True,
                    Task.created_at.between(prev_week_start_dt, week_start_dt),
                )
            )
            habits_last_week = await self._count(
                select(func.count(HabitLog.id)).where(
                    HabitLog.completed_date >= prev_week_start,
                    HabitLog.completed_date < week_start,
                )
            )

            # Expenses this week
            expense_result = await self._session.execute(
                select(func.sum(Expense.amount)).where(Expense.date >= week_start)
            )
            expenses_total = round(expense_result.scalar() or 0, 2)

            # Trends
            task_trend = self._trend(tasks_this_week, tasks_last_week)
            habit_trend = self._trend(habits_this_week, habits_last_week)

            return {
                "success": True,
                "period": "week",
                "start_date": str(week_start),
                "end_date": str(today),
                "stats": {
                    "tasks_completed": tasks_this_week,
                    "habits_logged": habits_this_week,
                    "expenses_total": expenses_total,
                },
                "trends": {
                    "tasks": task_trend,
                    "habits": habit_trend,
                },
                "message": (
                    f"This week: {tasks_this_week} tasks completed ({task_trend}), "
                    f"{habits_this_week} habits logged ({habit_trend}), "
                    f"${expenses_total:.2f} spent"
                ),
            }
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            return {"success": False, "message": f"Failed to generate report: {e}"}

    async def _count(self, query) -> int:
        """Execute a count query and return the result."""
        result = await self._session.execute(query)
        return result.scalar() or 0

    @staticmethod
    def _calculate_score(
        completed: int, created: int, habits: int, overdue: int
    ) -> int:
        """Calculate productivity score (0-100)."""
        score = 50  # Base score

        # Tasks completed bonus (max +30)
        score += min(completed * 10, 30)

        # Habits logged bonus (max +20)
        score += min(habits * 10, 20)

        # Overdue tasks penalty
        score -= overdue * 5

        return max(0, min(100, score))

    @staticmethod
    def _score_message(score: int) -> str:
        """Generate a motivational message based on the score."""
        if score >= 90:
            return "🏆 Outstanding! You're crushing it today!"
        elif score >= 75:
            return "🌟 Great job! You're being very productive!"
        elif score >= 60:
            return "👍 Good progress! Keep the momentum going!"
        elif score >= 40:
            return "💪 Decent start. Try completing a few more tasks!"
        else:
            return "🌱 Every step counts. Start with one small task!"

    @staticmethod
    def _trend(current: int, previous: int) -> str:
        """Calculate trend percentage between two periods."""
        if previous == 0:
            return f"+{current}" if current > 0 else "No change"
        change = round(((current - previous) / previous) * 100)
        if change > 0:
            return f"+{change}% vs last week"
        elif change < 0:
            return f"{change}% vs last week"
        return "Same as last week"
