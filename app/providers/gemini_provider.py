"""Gemini LLM provider implementation."""

import logging
from typing import AsyncIterator

from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Provider for Google's Gemini models."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """Initialize the Gemini provider.
        
        Args:
            api_key: The Google Gemini API key.
            model_name: The Gemini model to use.
        """
        self.api_key = api_key
        self.model_name = model_name
        self._configured = False

    def _ensure_configured(self):
        """Lazy-configure the genai library."""
        if not self._configured:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._configured = True

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response using Gemini."""
        try:
            import google.generativeai as genai
            self._ensure_configured()
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt if system_prompt else None
            )
            response = await model.generate_content_async(prompt)
            return response.text
        except ImportError:
            raise RuntimeError("google-generativeai is not installed. Run: pip install google-generativeai")
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {e}") from e

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncIterator[str]:
        """Stream a response using Gemini."""
        try:
            import google.generativeai as genai
            self._ensure_configured()
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt if system_prompt else None
            )
            response = await model.generate_content_async(prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except ImportError:
            raise RuntimeError("google-generativeai is not installed.")
        except Exception as e:
            raise RuntimeError(f"Gemini streaming failed: {e}") from e

    async def health_check(self) -> bool:
        """Check if Gemini is reachable."""
        try:
            import google.generativeai as genai  # noqa: F401
            self._ensure_configured()
            return True
        except Exception:
            return False
