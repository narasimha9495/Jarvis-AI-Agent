"""Gemini LLM provider implementation."""

from typing import AsyncIterator
import google.generativeai as genai

from app.providers.base import BaseLLMProvider


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
        genai.configure(api_key=self.api_key)

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt if system_prompt else None
            )
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {str(e)}") from e

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncIterator[str]:
        """Stream a response using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt if system_prompt else None
            )
            response = await model.generate_content_async(prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise RuntimeError(f"Gemini streaming failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if Gemini is reachable and functional."""
        try:
            model = genai.GenerativeModel(model_name=self.model_name)
            await model.generate_content_async("ping")
            return True
        except Exception:
            return False
