"""Reminder management action."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.actions.base import BaseAction
from app.db.models import Reminder


class ReminderAction(BaseAction):
    """Set and manage reminders."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the reminder action with a database session."""
        self.session = session

    @property
    def name(self) -> str:
        return "reminders"

    @property
    def description(self) -> str:
        return "Set and manage reminders"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the action with given parameters."""
        action = params.get("action")
        if not action:
            return {"success": False, "message": "Missing 'action' parameter."}

        try:
            if action == "create_reminder":
                return await self._create_reminder(params)
            elif action == "list_reminders":
                return await self._list_reminders(params)
            elif action == "dismiss_reminder":
                return await self._dismiss_reminder(params)
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "message": f"Error executing reminder action: {e}"}

    async def _create_reminder(self, params: dict[str, Any]) -> dict[str, Any]:
        message = params.get("message")
        remind_at = params.get("remind_at")

        if not message or not remind_at:
            return {"success": False, "message": "Both 'message' and 'remind_at' are required."}

        if isinstance(remind_at, str):
            try:
                remind_at = datetime.fromisoformat(remind_at.replace("Z", "+00:00"))
            except ValueError:
                return {"success": False, "message": "Invalid remind_at format. Use ISO format."}

        reminder = Reminder(
            message=message,
            remind_at=remind_at
        )
        self.session.add(reminder)
        await self.session.commit()
        
        return {
            "success": True,
            "message": "Reminder created successfully.",
            "reminder_id": reminder.id
        }

    async def _list_reminders(self, params: dict[str, Any]) -> dict[str, Any]:
        triggered = params.get("triggered")
        stmt = select(Reminder)
        if triggered is not None:
            stmt = stmt.where(Reminder.triggered == triggered)
        
        result = await self.session.execute(stmt)
        reminders = result.scalars().all()
        
        reminders_data = [
            {
                "id": r.id,
                "message": r.message,
                "remind_at": r.remind_at.isoformat() if r.remind_at else None,
                "triggered": r.triggered
            }
            for r in reminders
        ]
        return {"success": True, "message": f"Found {len(reminders)} reminders.", "reminders": reminders_data}

    async def _dismiss_reminder(self, params: dict[str, Any]) -> dict[str, Any]:
        reminder_id = params.get("reminder_id")
        if not reminder_id:
            return {"success": False, "message": "reminder_id is required."}

        stmt = select(Reminder).where(Reminder.id == reminder_id)
        result = await self.session.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            return {"success": False, "message": f"Reminder {reminder_id} not found."}

        reminder.triggered = True
        await self.session.commit()
        return {"success": True, "message": f"Reminder {reminder_id} dismissed."}
