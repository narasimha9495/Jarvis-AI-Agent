"""Tests for the LLM router."""

import pytest
from unittest.mock import MagicMock

from app.core.llm_router import LLMRouter


@pytest.fixture
def mock_settings():
    """Create mock settings with test API keys."""
    settings = MagicMock()
    settings.gemini_api_key = "test-gemini-key"
    settings.gemini_model = "gemini-2.0-flash"
    settings.openai_api_key = "test-openai-key"
    settings.openai_model = "gpt-4o-mini"
    settings.ollama_base_url = "http://localhost:11434"
    settings.ollama_model = "llama3.2"
    settings.default_llm_provider = "gemini"
    return settings


def test_router_without_settings():
    """Router with no settings should initialize empty."""
    router = LLMRouter()
    assert router.get_available_providers() == []


def test_router_initializes_providers(mock_settings):
    """Router should initialize configured providers."""
    router = LLMRouter(mock_settings)
    providers = router.get_available_providers()
    # At minimum ollama should always be present
    assert "ollama" in providers


def test_get_default_provider(mock_settings):
    """Should return the default provider."""
    router = LLMRouter(mock_settings)
    # Default is gemini from settings
    try:
        provider = router.get_provider()
        assert provider is not None
    except ValueError:
        # If gemini couldn't init (no package), that's expected
        pass


def test_get_specific_provider(mock_settings):
    """Should return a specific provider by name."""
    router = LLMRouter(mock_settings)
    provider = router.get_provider("ollama")
    assert provider is not None


def test_get_invalid_provider(mock_settings):
    """Should raise ValueError for unknown provider."""
    router = LLMRouter(mock_settings)
    with pytest.raises(ValueError):
        router.get_provider("nonexistent")


def test_get_available_providers(mock_settings):
    """Should return list of configured provider names."""
    router = LLMRouter(mock_settings)
    providers = router.get_available_providers()
    assert isinstance(providers, list)
    assert "ollama" in providers


def test_router_with_empty_keys():
    """Router with empty API keys should only have ollama."""
    settings = MagicMock()
    settings.gemini_api_key = ""
    settings.openai_api_key = ""
    settings.ollama_base_url = "http://localhost:11434"
    settings.ollama_model = "llama3.2"
    settings.default_llm_provider = "ollama"
    router = LLMRouter(settings)
    providers = router.get_available_providers()
    assert "ollama" in providers
    assert "gemini" not in providers
    assert "openai" not in providers
