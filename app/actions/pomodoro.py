import uuid
from datetime import datetime, timedelta
from typing import Any, Dict
from app.actions.base import BaseAction


class PomodoroAction(BaseAction):
    """Pomodoro focus timer for productivity."""
    
    # Class-level state for in-memory tracking
    _sessions: Dict[str, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "pomodoro"

    @property
    def description(self) -> str:
        return "Pomodoro focus timer for productivity"

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action")
        
        if action == "start":
            task = params.get("task", "Focus")
            duration = int(params.get("duration", 25))
            break_duration = int(params.get("break_duration", 5))
            
            session_id = uuid.uuid4().hex[:8]
            
            self._sessions[session_id] = {
                "task": task,
                "start_time": datetime.utcnow(),
                "duration": duration,
                "break_duration": break_duration,
                "status": "focusing",
                "completed_pomodoros": 0
            }
            
            return {
                "success": True,
                "session_id": session_id,
                "task": task,
                "duration": duration,
                "message": f"Pomodoro started! Focus for {duration} minutes."
            }
            
        elif action == "status":
            session_id = params.get("session_id")
            if not session_id or session_id not in self._sessions:
                return {"success": False, "error": "Invalid or missing session_id"}
                
            session = self._sessions[session_id]
            elapsed = datetime.utcnow() - session["start_time"]
            elapsed_minutes = int(elapsed.total_seconds() // 60)
            
            current_phase_duration = session["duration"] if session["status"] == "focusing" else session["break_duration"]
            remaining_minutes = max(0, current_phase_duration - elapsed_minutes)
            
            return {
                "success": True,
                "task": session["task"],
                "elapsed_minutes": elapsed_minutes,
                "remaining_minutes": remaining_minutes,
                "status": session["status"]
            }
            
        elif action == "complete":
            session_id = params.get("session_id")
            if not session_id or session_id not in self._sessions:
                return {"success": False, "error": "Invalid or missing session_id"}
                
            session = self._sessions[session_id]
            session["completed_pomodoros"] += 1
            session["status"] = "break"
            session["start_time"] = datetime.utcnow()
            
            return {
                "success": True,
                "completed_pomodoros": session["completed_pomodoros"],
                "message": f"Pomodoro completed! Take a {session['break_duration']} minute break."
            }
            
        elif action == "stop":
            session_id = params.get("session_id")
            if session_id in self._sessions:
                del self._sessions[session_id]
            return {"success": True, "message": "Pomodoro stopped."}
            
        elif action == "stats":
            total_completed = sum(session.get("completed_pomodoros", 0) for session in self._sessions.values())
            return {
                "success": True,
                "total_completed_pomodoros": total_completed
            }
            
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
