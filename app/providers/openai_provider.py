"""OpenAI LLM provider implementation."""

from typing import AsyncIterator
from openai import AsyncOpenAI

from app.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """Provider for OpenAI models."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        """Initialize the OpenAI provider.
        
        Args:
            api_key: The OpenAI API key.
            model_name: The OpenAI model to use.
        """
        self.model_name = model_name
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}") from e

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncIterator[str]:
        """Stream a response using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            raise RuntimeError(f"OpenAI streaming failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if OpenAI is reachable and functional."""
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
