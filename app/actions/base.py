"""Abstract base class for actions."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAction(ABC):
    """Base class for all Jarvis actions.
    
    Each action represents a specific capability of the assistant,
    such as managing tasks, setting reminders, or searching the web.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name identifier for this action."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this action does."""
        ...

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the action with given parameters.
        
        Args:
            params: Action-specific parameters.
            
        Returns:
            A dict with 'success' (bool) and 'message' (str) keys,
            plus any action-specific data.
        """
        ...
