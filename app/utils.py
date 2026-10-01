"""Utility helpers for the Jarvis AI Agent.

Shared utility functions used across multiple modules
to avoid code duplication and improve maintainability.
"""

import re
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON action object from an LLM response.
    
    Handles both raw JSON and markdown code-fenced JSON blocks.
    
    Args:
        text: The raw text response from the LLM.
        
    Returns:
        Parsed dict with 'action' key if found, else None.
    """
    try:
        # Try markdown JSON block first: ```json { ... } ```
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        json_str = match.group(1) if match else text

        data = json.loads(json_str)
        if isinstance(data, dict) and "action" in data:
            return data
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime.
    
    Replaces deprecated datetime.utcnow() throughout the project.
    """
    return datetime.now(timezone.utc)


def format_duration(seconds: int) -> str:
    """Format seconds into a human-readable duration string.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted string like '2h 15m' or '45m' or '30s'.
    """
    if seconds < 60:
        return f"{seconds}s"
    
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    return f"{minutes}m"


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text to max_length with ellipsis.
    
    Args:
        text: The text to truncate.
        max_length: Maximum character length.
        
    Returns:
        Truncated text with '...' if it exceeded max_length.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitize_input(text: str) -> str:
    """Basic input sanitization — strip whitespace and control characters.
    
    Args:
        text: Raw user input.
        
    Returns:
        Cleaned string safe for processing.
    """
    # Remove control characters except newline and tab
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return cleaned.strip()
