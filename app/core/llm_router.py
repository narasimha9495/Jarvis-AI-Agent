"""Router for managing multiple LLM providers."""

import logging
from typing import AsyncIterator, Optional, Dict, Any

from app.providers.base import BaseLLMProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    """Router to manage and route requests to different LLM providers."""

    def __init__(self, settings: Any):
        """Initialize the router and providers based on settings.
        
        Args:
            settings: Application settings containing API keys and configurations.
        """
        self.settings = settings
        self._providers: Dict[str, BaseLLMProvider] = {}
        
        # Determine the default provider
        self.default_provider_name = getattr(settings, 'default_llm_provider', 'ollama')

        # Initialize Gemini if configured
        gemini_api_key = getattr(settings, 'gemini_api_key', None)
        if gemini_api_key:
            self._providers['gemini'] = GeminiProvider(api_key=gemini_api_key)

        # Initialize OpenAI if configured
        openai_api_key = getattr(settings, 'openai_api_key', None)
        if openai_api_key:
            self._providers['openai'] = OpenAIProvider(api_key=openai_api_key)

        # Always initialize Ollama
        ollama_base_url = getattr(settings, 'ollama_base_url', 'http://localhost:11434')
        self._providers['ollama'] = OllamaProvider(base_url=ollama_base_url)

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """Get a specific provider by name, or the default provider.
        
        Args:
            name: The name of the provider (e.g., 'gemini', 'openai', 'ollama').
            
        Returns:
            The requested BaseLLMProvider instance.
            
        Raises:
            ValueError: If the requested provider is not found or not configured.
        """
        target_name = name or self.default_provider_name
        
        if target_name not in self._providers:
            raise ValueError(f"Provider '{target_name}' is not configured or not found.")
            
        return self._providers[target_name]

    async def generate(self, prompt: str, system_prompt: str = "", provider: Optional[str] = None) -> str:
        """Generate a response using the specified or default provider."""
        target_provider = self.get_provider(provider)
        try:
            return await target_provider.generate(prompt, system_prompt)
        except Exception as e:
            logger.error(f"Error generating with provider: {str(e)}")
            raise

    async def generate_stream(self, prompt: str, system_prompt: str = "", provider: Optional[str] = None) -> AsyncIterator[str]:
        """Stream a response using the specified or default provider."""
        target_provider = self.get_provider(provider)
        try:
            async for chunk in target_provider.generate_stream(prompt, system_prompt):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming with provider: {str(e)}")
            raise

    async def list_available(self) -> list[str]:
        """List all available providers that pass the health check.
        
        Returns:
            A list of provider names that are healthy.
        """
        available = []
        for name, provider_instance in self._providers.items():
            try:
                if await provider_instance.health_check():
                    available.append(name)
            except Exception as e:
                logger.warning(f"Health check failed for provider '{name}': {str(e)}")
                
        return available
