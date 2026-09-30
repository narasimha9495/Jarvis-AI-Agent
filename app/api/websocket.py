"""WebSocket endpoints for real-time communication."""

import json
import logging
import re
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.schemas import WebSocketMessage
from app.core.llm_router import LLMRouter
from app.core.safety import SafetyEngine

logger = logging.getLogger(__name__)

ws_router = APIRouter()

SYSTEM_PROMPT = """You are Jarvis, a personal productivity AI assistant.
You can manage tasks, reminders, notes, expenses, habits, and answer questions.
If you detect an action intent from the user, you MUST respond with a JSON object in this format:
{"action": "action_name", "params": {"param1": "value1", ...}}

Supported actions:
- create_task: {"title": str, "description": str, "priority": str}
- list_tasks: {}
- complete_task: {"task_id": int}
- delete_task: {"task_id": int}
- create_reminder: {"message": str, "remind_at": str}
- list_reminders: {}
- create_note: {"title": str, "content": str, "tags": str}
- list_notes: {}
- search_notes: {"query": str}
- search_web: {"query": str}
- get_weather: {"city": str}
- add_expense: {"amount": float, "category": str, "description": str}
- list_expenses: {}
- spending_summary: {"period": str}  (today/week/month)
- start_pomodoro: {"task": str, "duration": int}
- create_habit: {"name": str}
- log_habit: {"habit_id": int}
- list_habits: {}
- system_status: {}
- generate_summary: {}

If no action is needed, just respond normally with a text message.
"""


async def execute_action(action_name: str, params: dict, db: AsyncSession) -> dict:
    """Execute an action by name using the appropriate action handler.
    
    Routes action names to their corresponding action classes,
    instantiates them with required dependencies, and executes.
    """
    # Actions that need database session
    db_actions = {
        "create_task", "list_tasks", "complete_task", "delete_task",
        "create_reminder", "list_reminders", "dismiss_reminder",
        "create_note", "list_notes", "search_notes",
        "add_expense", "list_expenses", "spending_summary", "delete_expense",
        "create_habit", "log_habit", "list_habits", "habit_report", "delete_habit",
        "generate_summary", "weekly_report",
    }
    
    # Actions that don't need DB
    no_db_actions = {
        "search_web", "get_weather",
        "start", "status", "complete", "stop",  # pomodoro
        "system_status", "cpu_alert", "disk_alert", "top_processes",
    }

    # Map action names to their action class and the sub-action key
    action_map = {
        # Tasks
        "create_task": ("app.actions.tasks", "TaskAction"),
        "list_tasks": ("app.actions.tasks", "TaskAction"),
        "complete_task": ("app.actions.tasks", "TaskAction"),
        "delete_task": ("app.actions.tasks", "TaskAction"),
        # Reminders
        "create_reminder": ("app.actions.reminders", "ReminderAction"),
        "list_reminders": ("app.actions.reminders", "ReminderAction"),
        "dismiss_reminder": ("app.actions.reminders", "ReminderAction"),
        # Notes
        "create_note": ("app.actions.notes", "NoteAction"),
        "list_notes": ("app.actions.notes", "NoteAction"),
        "search_notes": ("app.actions.notes", "NoteAction"),
        # Search
        "search_web": ("app.actions.search", "SearchAction"),
        # Weather
        "get_weather": ("app.actions.weather", "WeatherAction"),
        # Expenses
        "add_expense": ("app.actions.expenses", "ExpenseAction"),
        "list_expenses": ("app.actions.expenses", "ExpenseAction"),
        "spending_summary": ("app.actions.expenses", "ExpenseAction"),
        "delete_expense": ("app.actions.expenses", "ExpenseAction"),
        # Pomodoro
        "start_pomodoro": ("app.actions.pomodoro", "PomodoroAction"),
        "pomodoro_status": ("app.actions.pomodoro", "PomodoroAction"),
        "complete_pomodoro": ("app.actions.pomodoro", "PomodoroAction"),
        "stop_pomodoro": ("app.actions.pomodoro", "PomodoroAction"),
        # Habits
        "create_habit": ("app.actions.habits", "HabitAction"),
        "log_habit": ("app.actions.habits", "HabitAction"),
        "list_habits": ("app.actions.habits", "HabitAction"),
        "habit_report": ("app.actions.habits", "HabitAction"),
        "delete_habit": ("app.actions.habits", "HabitAction"),
        # System Monitor
        "system_status": ("app.actions.system_monitor", "SystemMonitorAction"),
        "cpu_alert": ("app.actions.system_monitor", "SystemMonitorAction"),
        "disk_alert": ("app.actions.system_monitor", "SystemMonitorAction"),
        "top_processes": ("app.actions.system_monitor", "SystemMonitorAction"),
        # Daily Summary
        "generate_summary": ("app.actions.daily_summary", "DailySummaryAction"),
        "weekly_report": ("app.actions.daily_summary", "DailySummaryAction"),
    }

    if action_name not in action_map:
        return {"success": False, "message": f"Unknown action: {action_name}"}

    module_path, class_name = action_map[action_name]
    
    try:
        import importlib
        module = importlib.import_module(module_path)
        action_class = getattr(module, class_name)

        # Instantiate with or without db
        if action_name in db_actions:
            action_instance = action_class(db)
        else:
            action_instance = action_class()

        # Build params with action name
        exec_params = {"action": action_name, **params}
        return await action_instance.execute(exec_params)

    except Exception as e:
        logger.error(f"Failed to execute action '{action_name}': {e}")
        return {"success": False, "message": f"Action execution failed: {e}"}


def _extract_action(response: str) -> Optional[Dict[str, Any]]:
    """Helper to extract action JSON from LLM response."""
    try:
        # Check for JSON block markdown
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        json_str = match.group(1) if match else response
        
        # Try to parse the string as JSON
        data = json.loads(json_str)
        if isinstance(data, dict) and "action" in data:
            return data
    except Exception:
        pass
        
    return None


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    """WebSocket endpoint for real-time interaction."""
    await websocket.accept()
    
    llm_router = LLMRouter()
    safety_engine = SafetyEngine()
    
    # Send welcome message
    welcome_msg = WebSocketMessage(
        type="chat",
        content="Hello! I am Jarvis. How can I help you today?"
    )
    await websocket.send_text(welcome_msg.model_dump_json())
    
    # In-memory history for this connection
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    try:
        while True:
            text_data = await websocket.receive_text()
            
            try:
                data = json.loads(text_data)
                msg = WebSocketMessage(**data)
            except Exception as e:
                error_msg = WebSocketMessage(type="status", content=f"Error parsing message: {e}")
                await websocket.send_text(error_msg.model_dump_json())
                continue
                
            if msg.type == "chat":
                messages.append({"role": "user", "content": msg.content})
                
                try:
                    response_text = await llm_router.generate(
                        messages=messages,
                        provider=msg.provider
                    )
                    
                    messages.append({"role": "assistant", "content": response_text})
                    
                    # Extract potential action
                    action_data = _extract_action(response_text)
                    
                    if action_data:
                        action_name = action_data.get("action")
                        params = action_data.get("params", {})
                        
                        # Check safety
                        safety_check = await safety_engine.check_action(action_name, params)
                        
                        if not safety_check.allowed:
                            out_msg = WebSocketMessage(
                                type="status",
                                content=f"Action '{action_name}' blocked: {safety_check.message}"
                            )
                            await websocket.send_text(out_msg.model_dump_json())
                            continue
                            
                        if safety_check.requires_confirmation:
                            out_msg = WebSocketMessage(
                                type="confirm",
                                content=f"Confirmation required for: {action_name}. {safety_check.message}",
                                action=action_name,
                                params=params,
                                requires_confirmation=True
                            )
                            await websocket.send_text(out_msg.model_dump_json())
                            continue
                            
                        # Execute action
                        try:
                            result = await execute_action(action_name, params, db)
                            out_msg = WebSocketMessage(
                                type="action",
                                content=f"Executed: {action_name}",
                                action=action_name,
                                params={"result": result}
                            )
                            await websocket.send_text(out_msg.model_dump_json())
                        except Exception as e:
                            logger.error(f"Action execution error: {e}")
                            out_msg = WebSocketMessage(
                                type="status",
                                content=f"Failed to execute {action_name}: {e}"
                            )
                            await websocket.send_text(out_msg.model_dump_json())
                    else:
                        # Normal text response
                        out_msg = WebSocketMessage(type="chat", content=response_text)
                        await websocket.send_text(out_msg.model_dump_json())
                        
                except Exception as e:
                    logger.error(f"LLM generation error: {e}")
                    error_msg = WebSocketMessage(type="status", content=f"Error: {e}")
                    await websocket.send_text(error_msg.model_dump_json())
                    
            elif msg.type == "confirm":
                if msg.action:
                    try:
                        result = await execute_action(msg.action, msg.params or {}, db)
                        out_msg = WebSocketMessage(
                            type="action",
                            content=f"Confirmed & executed: {msg.action}",
                            action=msg.action,
                            params={"result": result}
                        )
                        await websocket.send_text(out_msg.model_dump_json())
                    except Exception as e:
                        out_msg = WebSocketMessage(
                            type="status",
                            content=f"Failed to execute {msg.action}: {e}"
                        )
                        await websocket.send_text(out_msg.model_dump_json())
                        
            elif msg.type == "status":
                status_msg = WebSocketMessage(
                    type="status",
                    content="System is online and running."
                )
                await websocket.send_text(status_msg.model_dump_json())
                
    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
