"""REST API routes for Jarvis AI Agent."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime, timedelta
from sqlalchemy import func

from app.db.database import get_db
from app.db.models import Task, Reminder, Note, Expense, Habit, HabitLog
from app.models.schemas import (
    HealthResponse, ChatRequest, ChatResponse,
    TaskCreate, TaskResponse,
    ReminderCreate, ReminderResponse,
    NoteCreate, NoteResponse,
    ExpenseCreate, ExpenseResponse,
    HabitCreate, HabitResponse
)
from app.core.llm_router import LLMRouter
from app.config import get_settings

router = APIRouter()

SYSTEM_PROMPT = """You are Jarvis, a personal productivity AI assistant.
You can manage tasks, reminders, notes, and answer questions.
If you detect an action intent from the user, you MUST respond with a JSON object in this format:
{"action": "action_name", "params": {"param1": "value1", ...}}

Supported actions:
- create_task: {"title": str, "description": str, "priority": str}
- list_tasks: {}
- complete_task: {"task_id": int}
- create_reminder: {"message": str, "remind_at": str}
- list_reminders: {}
- create_note: {"title": str, "content": str, "tags": str}
- list_notes: {}
- search_web: {"query": str}
- get_weather: {"city": str}
- add_expense: {"amount": float, "category": str, "description": str}
- list_expenses: {}
- spending_summary: {"period": str}
- start_pomodoro: {"task": str, "duration": int}
- create_habit: {"name": str}
- log_habit: {"habit_id": int}
- list_habits: {}
- system_status: {}
- generate_summary: {}

If no action is needed, just respond normally with a text message.
"""


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    llm_router = LLMRouter()
    return HealthResponse(
        status="ok",
        available_providers=llm_router.get_available_providers()
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Chat with the AI assistant."""
    llm_router = LLMRouter()
    
    # In a real implementation, we'd build full conversation history here
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message}
    ]
    
    try:
        response_text = await llm_router.generate(
            messages=messages,
            provider=request.provider
        )
        
        # Simple extraction logic (in reality, use the one from websocket)
        import json
        import re
        action_taken = None
        
        # Try to parse as JSON first
        try:
            # Look for JSON block
            match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            json_str = match.group(1) if match else response_text
            
            data = json.loads(json_str)
            if isinstance(data, dict) and "action" in data:
                action_taken = data["action"]
                # In a real app we'd execute it here too, but this is simplified
        except json.JSONDecodeError:
            pass

        return ChatResponse(
            response=response_text,
            provider=request.provider or "default",
            action_taken=action_taken
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """List all tasks."""
    result = await db.execute(select(Task).order_by(Task.created_at.desc()))
    return result.scalars().all()


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Create a new task."""
    task = Task(
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority,
        due_date=task_in.due_date
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a task as completed."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.completed = True
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await db.delete(task)
    await db.commit()
    return None


@router.get("/reminders", response_model=List[ReminderResponse])
async def list_reminders(db: AsyncSession = Depends(get_db)):
    """List all reminders."""
    result = await db.execute(select(Reminder).order_by(Reminder.remind_at.asc()))
    return result.scalars().all()


@router.post("/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(reminder_in: ReminderCreate, db: AsyncSession = Depends(get_db)):
    """Create a new reminder."""
    reminder = Reminder(
        message=reminder_in.message,
        remind_at=reminder_in.remind_at
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder


@router.get("/notes", response_model=List[NoteResponse])
async def list_notes(db: AsyncSession = Depends(get_db)):
    """List all notes."""
    result = await db.execute(select(Note).order_by(Note.updated_at.desc()))
    return result.scalars().all()


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(note_in: NoteCreate, db: AsyncSession = Depends(get_db)):
    """Create a new note."""
    note = Note(
        title=note_in.title,
        content=note_in.content,
        tags=note_in.tags
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/providers")
async def list_providers():
    """List available LLM providers."""
    llm_router = LLMRouter()
    return {"providers": llm_router.get_available_providers()}


@router.post("/providers/switch")
async def switch_provider(payload: Dict[str, str]):
    """Switch default LLM provider."""
    provider = payload.get("provider")
    if not provider:
        raise HTTPException(status_code=400, detail="Provider must be specified")
        
    llm_router = LLMRouter()
    if provider not in llm_router.get_available_providers():
        raise HTTPException(status_code=400, detail=f"Provider {provider} is not available")
        
    # In a real app we'd save this to settings/db
    return {"message": f"Successfully switched provider to {provider}"}

@router.get("/weather/{city}")
async def get_weather(city: str):
    """Get current weather and 3-day forecast for a city."""
    from app.actions.weather import WeatherAction
    action = WeatherAction()
    result = await action.execute({"action": "get_weather", "city": city})
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@router.get("/expenses")
async def list_expenses(category: str = None, db: AsyncSession = Depends(get_db)):
    """List all expenses, optionally filtered by category."""
    from app.actions.expenses import ExpenseAction
    action = ExpenseAction(db)
    params = {"action": "list_expenses"}
    if category:
        params["category"] = category
    return await action.execute(params)

@router.post("/expenses", status_code=status.HTTP_201_CREATED)
async def add_expense(expense_in: ExpenseCreate, db: AsyncSession = Depends(get_db)):
    """Add a new expense."""
    from app.actions.expenses import ExpenseAction
    action = ExpenseAction(db)
    return await action.execute({
        "action": "add_expense",
        "amount": expense_in.amount,
        "category": expense_in.category,
        "description": expense_in.description,
        "date": expense_in.date,
    })

@router.get("/expenses/summary")
async def spending_summary(period: str = "month", db: AsyncSession = Depends(get_db)):
    """Get spending summary grouped by category."""
    from app.actions.expenses import ExpenseAction
    action = ExpenseAction(db)
    return await action.execute({"action": "spending_summary", "period": period})

@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an expense."""
    from app.actions.expenses import ExpenseAction
    action = ExpenseAction(db)
    result = await action.execute({"action": "delete_expense", "expense_id": expense_id})
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return None

@router.get("/habits")
async def list_habits(db: AsyncSession = Depends(get_db)):
    """List all habits with streaks."""
    from app.actions.habits import HabitAction
    action = HabitAction(db)
    return await action.execute({"action": "list_habits"})

@router.post("/habits", status_code=status.HTTP_201_CREATED)
async def create_habit(habit_in: HabitCreate, db: AsyncSession = Depends(get_db)):
    """Create a new habit to track."""
    from app.actions.habits import HabitAction
    action = HabitAction(db)
    return await action.execute({"action": "create_habit", "name": habit_in.name, "frequency": habit_in.frequency})

@router.post("/habits/{habit_id}/log")
async def log_habit(habit_id: int, db: AsyncSession = Depends(get_db)):
    """Log a habit completion for today."""
    from app.actions.habits import HabitAction
    action = HabitAction(db)
    return await action.execute({"action": "log_habit", "habit_id": habit_id})

@router.get("/habits/report")
async def habit_report(period: str = "week", db: AsyncSession = Depends(get_db)):
    """Get habit completion report."""
    from app.actions.habits import HabitAction
    action = HabitAction(db)
    return await action.execute({"action": "habit_report", "period": period})

@router.delete("/habits/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habit(habit_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a habit and its logs."""
    from app.actions.habits import HabitAction
    action = HabitAction(db)
    result = await action.execute({"action": "delete_habit", "habit_id": habit_id})
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return None

@router.post("/pomodoro/start")
async def start_pomodoro(payload: Dict[str, Any]):
    """Start a new pomodoro focus session."""
    from app.actions.pomodoro import PomodoroAction
    action = PomodoroAction()
    return await action.execute({"action": "start", **payload})

@router.get("/pomodoro/{session_id}")
async def pomodoro_status(session_id: str):
    """Check pomodoro session status."""
    from app.actions.pomodoro import PomodoroAction
    action = PomodoroAction()
    return await action.execute({"action": "status", "session_id": session_id})

@router.post("/pomodoro/{session_id}/complete")
async def complete_pomodoro(session_id: str):
    """Mark a pomodoro session as completed."""
    from app.actions.pomodoro import PomodoroAction
    action = PomodoroAction()
    return await action.execute({"action": "complete", "session_id": session_id})

@router.delete("/pomodoro/{session_id}")
async def stop_pomodoro(session_id: str):
    """Stop/cancel a pomodoro session."""
    from app.actions.pomodoro import PomodoroAction
    action = PomodoroAction()
    return await action.execute({"action": "stop", "session_id": session_id})

@router.get("/system/status")
async def system_status():
    """Get full system health status."""
    from app.actions.system_monitor import SystemMonitorAction
    action = SystemMonitorAction()
    return await action.execute({"action": "system_status"})

@router.get("/system/processes")
async def top_processes():
    """Get top 5 processes by CPU usage."""
    from app.actions.system_monitor import SystemMonitorAction
    action = SystemMonitorAction()
    return await action.execute({"action": "top_processes"})

@router.get("/summary/daily")
async def daily_summary(db: AsyncSession = Depends(get_db)):
    """Generate today's productivity summary."""
    from app.actions.daily_summary import DailySummaryAction
    action = DailySummaryAction(db)
    return await action.execute({"action": "generate_summary"})

@router.get("/summary/weekly")
async def weekly_report(db: AsyncSession = Depends(get_db)):
    """Generate weekly productivity report."""
    from app.actions.daily_summary import DailySummaryAction
    action = DailySummaryAction(db)
    return await action.execute({"action": "weekly_report"})
