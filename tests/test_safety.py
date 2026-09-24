"""Tests for the safety engine."""

import pytest
from app.core.safety import SafetyEngine, RiskLevel


@pytest.fixture
def safety():
    return SafetyEngine()


@pytest.mark.asyncio
async def test_safe_action_allowed(safety):
    """Safe actions (read-only) should execute without confirmation."""
    result = await safety.check_action("list_tasks")
    assert result.allowed is True
    assert result.risk_level == RiskLevel.SAFE
    assert result.requires_confirmation is False


@pytest.mark.asyncio
async def test_moderate_action_allowed(safety):
    """Moderate actions should execute without confirmation."""
    result = await safety.check_action("create_task", {"title": "Test"})
    assert result.allowed is True
    assert result.risk_level == RiskLevel.MODERATE
    assert result.requires_confirmation is False


@pytest.mark.asyncio
async def test_dangerous_action_requires_confirmation(safety):
    """Dangerous actions should require user confirmation."""
    result = await safety.check_action("delete_task", {"task_id": 1})
    assert result.allowed is True
    assert result.risk_level == RiskLevel.DANGEROUS
    assert result.requires_confirmation is True


@pytest.mark.asyncio
async def test_blocked_action_denied(safety):
    """Blocked actions (shell commands) should be completely denied."""
    result = await safety.check_action("run_command", {"cmd": "rm -rf /"})
    assert result.allowed is False
    assert result.risk_level == RiskLevel.DANGEROUS


@pytest.mark.asyncio
async def test_unknown_action_treated_as_dangerous(safety):
    """Unknown actions should default to dangerous (requires confirmation)."""
    result = await safety.check_action("some_unknown_action")
    assert result.risk_level == RiskLevel.DANGEROUS
    assert result.requires_confirmation is True


@pytest.mark.asyncio
async def test_search_is_safe(safety):
    """Web search should be a safe action."""
    result = await safety.check_action("search_web")
    assert result.allowed is True
    assert result.risk_level == RiskLevel.SAFE
