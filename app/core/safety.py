"""Safety engine with risk assessment, confirmation flow, and rate limiting.

Every action goes through the safety engine before execution.
Actions are categorized by risk level, and dangerous actions
are blocked entirely — the assistant never runs shell commands.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk classification for actions."""
    SAFE = "safe"           # Read-only: search, list tasks, list notes
    MODERATE = "moderate"   # Write: create task, set reminder, create note
    DANGEROUS = "dangerous" # Never auto-execute: delete, modify system


@dataclass
class SafetyCheck:
    """Result of a safety check on an action."""
    allowed: bool
    risk_level: RiskLevel
    requires_confirmation: bool
    message: str


# Action to risk level mapping
ACTION_RISK_MAP: dict[str, RiskLevel] = {
    # Safe actions - read only
    "list_tasks": RiskLevel.SAFE,
    "list_reminders": RiskLevel.SAFE,
    "list_notes": RiskLevel.SAFE,
    "search_notes": RiskLevel.SAFE,
    "search_web": RiskLevel.SAFE,
    "get_weather": RiskLevel.SAFE,
    "list_expenses": RiskLevel.SAFE,
    "spending_summary": RiskLevel.SAFE,
    "pomodoro_status": RiskLevel.SAFE,
    "pomodoro_stats": RiskLevel.SAFE,
    "list_habits": RiskLevel.SAFE,
    "habit_report": RiskLevel.SAFE,
    "system_status": RiskLevel.SAFE,
    "cpu_alert": RiskLevel.SAFE,
    "disk_alert": RiskLevel.SAFE,
    "top_processes": RiskLevel.SAFE,
    "generate_summary": RiskLevel.SAFE,
    "weekly_report": RiskLevel.SAFE,

    # Moderate actions - create/update
    "create_task": RiskLevel.MODERATE,
    "complete_task": RiskLevel.MODERATE,
    "create_reminder": RiskLevel.MODERATE,
    "dismiss_reminder": RiskLevel.MODERATE,
    "create_note": RiskLevel.MODERATE,
    "add_expense": RiskLevel.MODERATE,
    "start_pomodoro": RiskLevel.MODERATE,
    "complete_pomodoro": RiskLevel.MODERATE,
    "stop_pomodoro": RiskLevel.MODERATE,
    "create_habit": RiskLevel.MODERATE,
    "log_habit": RiskLevel.MODERATE,

    # Dangerous actions - destructive
    "delete_task": RiskLevel.DANGEROUS,
    "delete_note": RiskLevel.DANGEROUS,
    "delete_expense": RiskLevel.DANGEROUS,
    "delete_habit": RiskLevel.DANGEROUS,
}

# Actions that are completely blocked
BLOCKED_ACTIONS: set[str] = {
    "run_command",
    "execute_shell",
    "system_command",
    "delete_file",
    "modify_system",
}

# Rate limiting: max calls per action per minute
RATE_LIMITS: dict[str, int] = {
    "search_web": 10,
    "get_weather": 15,
    "create_task": 20,
    "create_reminder": 20,
    "add_expense": 30,
    "delete_task": 5,
    "delete_expense": 5,
    "delete_habit": 5,
}
DEFAULT_RATE_LIMIT = 60  # per minute


class SafetyEngine:
    """Evaluates actions for safety before execution.
    
    Risk levels:
    - SAFE: Execute immediately (list, search, read operations)
    - MODERATE: Execute with notification (create, update operations)  
    - DANGEROUS: Require explicit user confirmation (delete operations)
    
    Blocked actions are never allowed regardless of confirmation.
    Includes per-action rate limiting to prevent abuse.
    """

    def __init__(self):
        # Track action call timestamps for rate limiting
        self._action_log: dict[str, list[datetime]] = defaultdict(list)

    def _check_rate_limit(self, action_name: str) -> bool:
        """Check if the action is within its rate limit.
        
        Args:
            action_name: The action to check.
            
        Returns:
            True if allowed, False if rate limited.
        """
        now = datetime.now(timezone.utc)
        limit = RATE_LIMITS.get(action_name, DEFAULT_RATE_LIMIT)

        # Clean old entries (older than 60 seconds)
        self._action_log[action_name] = [
            ts for ts in self._action_log[action_name]
            if (now - ts).total_seconds() < 60
        ]

        if len(self._action_log[action_name]) >= limit:
            return False

        self._action_log[action_name].append(now)
        return True

    async def check_action(
        self, action_name: str, params: dict | None = None
    ) -> SafetyCheck:
        """Evaluate whether an action is safe to execute.
        
        Args:
            action_name: The name of the action to check.
            params: Optional parameters for the action.
            
        Returns:
            SafetyCheck with the assessment result.
        """
        # Block dangerous system actions entirely
        if action_name in BLOCKED_ACTIONS:
            logger.warning(f"Blocked dangerous action: {action_name}")
            return SafetyCheck(
                allowed=False,
                risk_level=RiskLevel.DANGEROUS,
                requires_confirmation=False,
                message=f"Action '{action_name}' is blocked for safety reasons. "
                        f"This assistant does not execute system commands.",
            )

        # Check rate limit
        if not self._check_rate_limit(action_name):
            logger.warning(f"Rate limited action: {action_name}")
            return SafetyCheck(
                allowed=False,
                risk_level=RiskLevel.MODERATE,
                requires_confirmation=False,
                message=f"Action '{action_name}' is rate limited. Please wait a moment.",
            )

        # Look up risk level
        risk_level = ACTION_RISK_MAP.get(action_name, RiskLevel.DANGEROUS)

        if risk_level == RiskLevel.SAFE:
            return SafetyCheck(
                allowed=True,
                risk_level=risk_level,
                requires_confirmation=False,
                message="Action is safe to execute.",
            )

        if risk_level == RiskLevel.MODERATE:
            return SafetyCheck(
                allowed=True,
                risk_level=risk_level,
                requires_confirmation=False,
                message=f"Executing action: {action_name}",
            )

        # DANGEROUS - requires confirmation
        return SafetyCheck(
            allowed=True,
            risk_level=risk_level,
            requires_confirmation=True,
            message=f"Action '{action_name}' requires your confirmation before executing. "
                    f"Parameters: {params}",
        )
