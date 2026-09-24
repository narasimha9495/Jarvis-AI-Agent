"""Task management action."""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime

from app.actions.base import BaseAction
from app.db.models import Task


class TaskAction(BaseAction):
    """Manage personal tasks - create, list, complete, and delete tasks."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the task action with a database session."""
        self.session = session

    @property
    def name(self) -> str:
        return "tasks"

    @property
    def description(self) -> str:
        return "Manage personal tasks - create, list, complete, and delete tasks"

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the action with given parameters."""
        action = params.get("action")
        if not action:
            return {"success": False, "message": "Missing 'action' parameter."}

        try:
            if action == "create_task":
                return await self._create_task(params)
            elif action == "list_tasks":
                return await self._list_tasks(params)
            elif action == "complete_task":
                return await self._complete_task(params)
            elif action == "delete_task":
                return await self._delete_task(params)
            else:
                return {"success": False, "message": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "message": f"Error executing task action: {e}"}

    async def _create_task(self, params: dict[str, Any]) -> dict[str, Any]:
        title = params.get("title")
        description = params.get("description", "")
        priority = params.get("priority", 1)
        due_date = params.get("due_date")

        if not title:
            return {"success": False, "message": "Title is required to create a task."}

        if due_date and isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            except ValueError:
                return {"success": False, "message": "Invalid due_date format. Use ISO format."}

        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date
        )
        self.session.add(task)
        await self.session.commit()
        
        return {
            "success": True,
            "message": "Task created successfully.",
            "task_id": task.id
        }

    async def _list_tasks(self, params: dict[str, Any]) -> dict[str, Any]:
        completed = params.get("completed")
        stmt = select(Task)
        if completed is not None:
            stmt = stmt.where(Task.completed == completed)
        
        result = await self.session.execute(stmt)
        tasks = result.scalars().all()
        
        tasks_data = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "completed": t.completed,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None
            }
            for t in tasks
        ]
        return {"success": True, "message": f"Found {len(tasks)} tasks.", "tasks": tasks_data}

    async def _complete_task(self, params: dict[str, Any]) -> dict[str, Any]:
        task_id = params.get("task_id")
        if not task_id:
            return {"success": False, "message": "task_id is required."}

        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return {"success": False, "message": f"Task {task_id} not found."}

        task.completed = True
        await self.session.commit()
        return {"success": True, "message": f"Task {task_id} marked as completed."}

    async def _delete_task(self, params: dict[str, Any]) -> dict[str, Any]:
        task_id = params.get("task_id")
        if not task_id:
            return {"success": False, "message": "task_id is required."}

        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return {"success": False, "message": f"Task {task_id} not found."}

        await self.session.delete(task)
        await self.session.commit()
        return {"success": True, "message": f"Task {task_id} deleted successfully."}
