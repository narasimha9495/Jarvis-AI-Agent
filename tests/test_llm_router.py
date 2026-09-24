"""Tests for the LLM router."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.llm_router import LLMRouter
from app.config import Settings


@pytest.fixture
def settings():
    return Settings(
        gemini_api_key="test-gemini-key",
        openai_api_key="test-openai-key",
        default_llm_provider="gemini",
    )


@pytest.fixture
def router(settings):
    return LLMRouter(settings)


def test_router_initializes_providers(router):
    """Router should initialize configured providers."""
    assert "gemini" in router._providers
    assert "openai" in router._providers
    assert "ollama" in router._providers


def test_get_default_provider(router):
    """Should return the default provider."""
    provider = router.get_provider()
    assert provider is not None


def test_get_specific_provider(router):
    """Should return a specific provider by name."""
    provider = router.get_provider("openai")
    assert provider is not None


def test_get_invalid_provider(router):
    """Should raise ValueError for unknown provider."""
    with pytest.raises(ValueError):
        router.get_provider("nonexistent")


def test_router_without_api_keys():
    """Router with no API keys should still initialize ollama."""
    settings = Settings(
        gemini_api_key="",
        openai_api_key="",
        default_llm_provider="ollama",
    )
    router = LLMRouter(settings)
    assert "ollama" in router._providers
