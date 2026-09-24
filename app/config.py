"""Application configuration using pydantic-settings.

Loads settings from .env file and environment variables.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM API Keys
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama server URL"
    )

    # Default provider
    default_llm_provider: str = Field(
        default="gemini", description="Default LLM provider: gemini, openai, or ollama"
    )

    # Model names
    gemini_model: str = Field(default="gemini-2.0-flash")
    openai_model: str = Field(default="gpt-4o-mini")
    ollama_model: str = Field(default="llama3.2")

    # App
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    debug: bool = Field(default=False)

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./jarvis.db")

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
