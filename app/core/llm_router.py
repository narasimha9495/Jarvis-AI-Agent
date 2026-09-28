"""Router for managing multiple LLM providers."""

import logging
from typing import AsyncIterator, Optional, Dict, Any, List

from app.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    """Router to manage and route requests to different LLM providers.
    
    Can be instantiated with or without settings. When called without
    settings, it creates a minimal router with no providers configured.
    """

    def __init__(self, settings: Any = None):
        """Initialize the router and providers based on settings.
        
        Args:
            settings: Application settings containing API keys and configurations.
                     If None, creates an empty router.
        """
        self._providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider_name = "ollama"

        if settings is None:
            return

        self.default_provider_name = getattr(settings, 'default_llm_provider', 'ollama')

        # Initialize Gemini if configured (lazy import)
        gemini_api_key = getattr(settings, 'gemini_api_key', None)
        if gemini_api_key:
            try:
                from app.providers.gemini_provider import GeminiProvider
                model = getattr(settings, 'gemini_model', 'gemini-2.0-flash')
                self._providers['gemini'] = GeminiProvider(api_key=gemini_api_key, model_name=model)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini provider: {e}")

        # Initialize OpenAI if configured (lazy import)
        openai_api_key = getattr(settings, 'openai_api_key', None)
        if openai_api_key:
            try:
                from app.providers.openai_provider import OpenAIProvider
                model = getattr(settings, 'openai_model', 'gpt-4o-mini')
                self._providers['openai'] = OpenAIProvider(api_key=openai_api_key, model_name=model)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")

        # Always try to initialize Ollama (lazy import)
        try:
            from app.providers.ollama_provider import OllamaProvider
            ollama_base_url = getattr(settings, 'ollama_base_url', 'http://localhost:11434')
            model = getattr(settings, 'ollama_model', 'llama3.2')
            self._providers['ollama'] = OllamaProvider(base_url=ollama_base_url, model_name=model)
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")

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
            raise ValueError(
                f"Provider '{target_name}' is not configured. "
                f"Available: {list(self._providers.keys())}"
            )
            
        return self._providers[target_name]

    def get_available_providers(self) -> List[str]:
        """Return the list of configured provider names.
        
        Returns:
            List of provider name strings.
        """
        return list(self._providers.keys())

    async def generate(
        self,
        prompt: str = "",
        system_prompt: str = "",
        provider: Optional[str] = None,
        messages: Optional[list] = None,
    ) -> str:
        """Generate a response using the specified or default provider.
        
        Supports both simple prompt mode and messages mode.
        If messages is provided, the prompt is built from messages.
        """
        target_provider = self.get_provider(provider)

        # Build prompt from messages if provided
        if messages:
            sys_parts = [m["content"] for m in messages if m.get("role") == "system"]
            user_parts = [m["content"] for m in messages if m.get("role") == "user"]
            if sys_parts:
                system_prompt = "\n".join(sys_parts)
            if user_parts:
                prompt = "\n".join(user_parts)

        try:
            return await target_provider.generate(prompt, system_prompt)
        except Exception as e:
            logger.error(f"Error generating with provider: {e}")
            raise

    async def generate_stream(
        self, prompt: str, system_prompt: str = "", provider: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Stream a response using the specified or default provider."""
        target_provider = self.get_provider(provider)
        try:
            async for chunk in target_provider.generate_stream(prompt, system_prompt):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming with provider: {e}")
            raise

    async def list_available(self) -> List[str]:
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
                logger.warning(f"Health check failed for '{name}': {e}")
                
        return available
