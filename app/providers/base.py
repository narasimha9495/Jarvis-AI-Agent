"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLMProvider(ABC):
    """Base class that all LLM providers must implement."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response for the given prompt.
        
        Args:
            prompt: The user's message.
            system_prompt: Optional system instructions.
            
        Returns:
            The model's text response.
        """
        ...

    @abstractmethod
    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncIterator[str]:
        """Stream a response token by token.
        
        Args:
            prompt: The user's message.
            system_prompt: Optional system instructions.
            
        Yields:
            Individual text chunks from the model.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and configured.
        
        Returns:
            True if the provider is ready to use.
        """
        ...
