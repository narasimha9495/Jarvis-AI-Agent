"""Ollama LLM provider implementation."""

from typing import AsyncIterator
import ollama

from app.providers.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Provider for Ollama local models."""

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3.2"):
        """Initialize the Ollama provider.
        
        Args:
            base_url: The URL of the Ollama server.
            model_name: The Ollama model to use.
        """
        self.base_url = base_url
        self.model_name = model_name
        self.client = ollama.AsyncClient(host=base_url)

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response using Ollama."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=messages
            )
            return response.get('message', {}).get('content', '')
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {str(e)}") from e

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncIterator[str]:
        """Stream a response using Ollama."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            async for chunk in stream:
                content = chunk.get('message', {}).get('content', '')
                if content:
                    yield content
        except Exception as e:
            raise RuntimeError(f"Ollama streaming failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if Ollama is reachable and functional."""
        try:
            await self.client.list()
            return True
        except Exception:
            return False
