"""Expense tracking action module.

Track daily expenses, categorize spending, and view summaries
to help manage personal finances.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.actions.base import BaseAction
from app.db.models import Expense

logger = logging.getLogger(__name__)


class ExpenseAction(BaseAction):
    """Track and manage personal expenses."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def name(self) -> str:
        return "expenses"

    @property
    def description(self) -> str:
        return "Track daily expenses and view spending summaries"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Route to the appropriate expense sub-action."""
        action = params.get("action", "")
        handlers = {
            "add_expense": self._add_expense,
            "list_expenses": self._list_expenses,
            "spending_summary": self._spending_summary,
            "delete_expense": self._delete_expense,
        }
        handler = handlers.get(action)
        if not handler:
            return {"success": False, "message": f"Unknown expense action: {action}"}
        return await handler(params)

    async def _add_expense(self, params: dict) -> dict[str, Any]:
        """Add a new expense record."""
        try:
            amount = float(params.get("amount", 0))
            if amount <= 0:
                return {"success": False, "message": "Amount must be positive"}

            expense_date = date.today()
            if "date" in params and params["date"]:
                expense_date = date.fromisoformat(params["date"])

            expense = Expense(
                amount=amount,
                category=params.get("category", "general"),
                description=params.get("description", ""),
                date=expense_date,
            )
            self._session.add(expense)
            await self._session.commit()
            await self._session.refresh(expense)

            return {
                "success": True,
                "message": f"Added expense: ${amount:.2f} ({expense.category})",
                "expense_id": expense.id,
                "amount": amount,
                "category": expense.category,
                "date": str(expense_date),
            }
        except ValueError as e:
            return {"success": False, "message": f"Invalid input: {e}"}
        except Exception as e:
            logger.error(f"Failed to add expense: {e}")
            return {"success": False, "message": f"Failed to add expense: {e}"}

    async def _list_expenses(self, params: dict) -> dict[str, Any]:
        """List expenses with optional filters."""
        try:
            query = select(Expense).order_by(Expense.date.desc())

            category = params.get("category")
            if category:
                query = query.where(Expense.category == category)

            start_date = params.get("start_date")
            if start_date:
                query = query.where(Expense.date >= date.fromisoformat(start_date))

            end_date = params.get("end_date")
            if end_date:
                query = query.where(Expense.date <= date.fromisoformat(end_date))

            result = await self._session.execute(query)
            expenses = result.scalars().all()

            return {
                "success": True,
                "expenses": [
                    {
                        "id": e.id,
                        "amount": e.amount,
                        "category": e.category,
                        "description": e.description,
                        "date": str(e.date),
                    }
                    for e in expenses
                ],
                "total": sum(e.amount for e in expenses),
                "message": f"Found {len(expenses)} expense(s)",
            }
        except Exception as e:
            logger.error(f"Failed to list expenses: {e}")
            return {"success": False, "message": f"Failed to list expenses: {e}"}

    async def _spending_summary(self, params: dict) -> dict[str, Any]:
        """Get spending summary grouped by category."""
        try:
            period = params.get("period", "month")
            today = date.today()

            if period == "today":
                start = today
            elif period == "week":
                start = today - timedelta(days=7)
            else:  # month
                start = today - timedelta(days=30)

            query = (
                select(Expense.category, func.sum(Expense.amount).label("total"))
                .where(Expense.date >= start)
                .group_by(Expense.category)
                .order_by(func.sum(Expense.amount).desc())
            )
            result = await self._session.execute(query)
            rows = result.all()

            categories = [{"name": row[0], "total": round(row[1], 2)} for row in rows]
            grand_total = round(sum(c["total"] for c in categories), 2)

            return {
                "success": True,
                "period": period,
                "categories": categories,
                "grand_total": grand_total,
                "message": f"Total spending ({period}): ${grand_total:.2f}",
            }
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {"success": False, "message": f"Failed to generate summary: {e}"}

    async def _delete_expense(self, params: dict) -> dict[str, Any]:
        """Delete an expense by ID."""
        try:
            expense_id = int(params.get("expense_id", 0))
            result = await self._session.execute(
                select(Expense).where(Expense.id == expense_id)
            )
            expense = result.scalar_one_or_none()
            if not expense:
                return {"success": False, "message": f"Expense {expense_id} not found"}

            await self._session.delete(expense)
            await self._session.commit()
            return {"success": True, "message": f"Deleted expense #{expense_id}"}
        except Exception as e:
            logger.error(f"Failed to delete expense: {e}")
            return {"success": False, "message": f"Failed to delete expense: {e}"}
