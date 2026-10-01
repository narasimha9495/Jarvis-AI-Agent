"""Tests for utility functions."""

import pytest
from app.utils import parse_json_response, utc_now, format_duration, truncate, sanitize_input
from datetime import timezone


def test_parse_json_from_raw():
    """Should parse raw JSON with action key."""
    text = '{"action": "create_task", "params": {"title": "Test"}}'
    result = parse_json_response(text)
    assert result is not None
    assert result["action"] == "create_task"


def test_parse_json_from_markdown_block():
    """Should extract JSON from markdown code fence."""
    text = 'Here is the action:\n```json\n{"action": "list_tasks", "params": {}}\n```'
    result = parse_json_response(text)
    assert result is not None
    assert result["action"] == "list_tasks"


def test_parse_json_returns_none_for_text():
    """Should return None for plain text without JSON."""
    result = parse_json_response("Hello, how are you?")
    assert result is None


def test_parse_json_returns_none_for_no_action():
    """Should return None for JSON without action key."""
    result = parse_json_response('{"name": "test"}')
    assert result is None


def test_utc_now_is_timezone_aware():
    """utc_now should return timezone-aware datetime."""
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_format_duration_seconds():
    """Should format seconds-only durations."""
    assert format_duration(30) == "30s"
    assert format_duration(0) == "0s"


def test_format_duration_minutes():
    """Should format minute durations."""
    assert format_duration(300) == "5m"
    assert format_duration(90) == "1m"


def test_format_duration_hours():
    """Should format hour durations."""
    assert format_duration(3600) == "1h"
    assert format_duration(5400) == "1h 30m"
    assert format_duration(7200) == "2h"


def test_truncate_short_text():
    """Short text should not be truncated."""
    assert truncate("Hello", 100) == "Hello"


def test_truncate_long_text():
    """Long text should be truncated with ellipsis."""
    result = truncate("A" * 200, 100)
    assert len(result) == 100
    assert result.endswith("...")


def test_sanitize_input():
    """Should strip control characters and whitespace."""
    assert sanitize_input("  hello\x00world  ") == "helloworld"
    assert sanitize_input("normal text") == "normal text"
    assert sanitize_input("  spaces  ") == "spaces"
