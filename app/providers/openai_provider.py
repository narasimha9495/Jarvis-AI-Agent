"""OpenAI LLM provider implementation."""

import logging
from typing import AsyncIterator

from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """Provider for OpenAI models."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        """Initialize the OpenAI provider.
        
        Args:
            api_key: The OpenAI API key.
            model_name: The OpenAI model to use.
        """
        self.api_key = api_key
        self.model_name = model_name
        self._client = None

    def _get_client(self):
        """Lazy-initialize the AsyncOpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except ImportError:
            raise RuntimeError("openai is not installed. Run: pip install openai")
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {e}") from e

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncIterator[str]:
        """Stream a response using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            client = self._get_client()
            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except ImportError:
            raise RuntimeError("openai is not installed.")
        except Exception as e:
            raise RuntimeError(f"OpenAI streaming failed: {e}") from e

    async def health_check(self) -> bool:
        """Check if OpenAI is reachable."""
        try:
            self._get_client()
            return True
        except Exception:
            return False
