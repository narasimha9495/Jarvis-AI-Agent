"""Text-to-speech using pyttsx3 (runs locally/offline).

This module provides local text-to-speech synthesis without
sending any data to external servers.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Local text-to-speech using pyttsx3.
    
    Runs entirely offline using the system's built-in
    speech synthesis engine.
    """

    def __init__(self, rate: int = 175, volume: float = 0.9):
        """Initialize TTS engine.
        
        Args:
            rate: Speech rate in words per minute (default: 175).
            volume: Volume level from 0.0 to 1.0 (default: 0.9).
        """
        self._engine = None
        self._rate = rate
        self._volume = volume
        self._initialized = False

    def _init_engine(self) -> None:
        """Lazy-initialize the TTS engine."""
        if self._initialized:
            return
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', self._rate)
            self._engine.setProperty('volume', self._volume)
            self._initialized = True
            logger.info("TTS engine initialized")
        except ImportError:
            logger.error("pyttsx3 not installed. Install with: pip install pyttsx3")
            raise RuntimeError(
                "pyttsx3 is not installed. Run: pip install pyttsx3"
            )
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise

    async def speak(self, text: str) -> None:
        """Convert text to speech and play it.
        
        Args:
            text: The text to speak.
        """
        if not text:
            return

        self._init_engine()

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._speak_sync, text)
        except Exception as e:
            logger.error(f"TTS failed: {e}")

    def _speak_sync(self, text: str) -> None:
        """Synchronous speech (runs in thread pool)."""
        self._engine.say(text)
        self._engine.runAndWait()

    async def save_to_file(self, text: str, filepath: str) -> None:
        """Save speech to an audio file.
        
        Args:
            text: The text to convert.
            filepath: Output file path.
        """
        self._init_engine()

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: self._save_sync(text, filepath)
            )
            logger.info(f"Saved audio to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise

    def _save_sync(self, text: str, filepath: str) -> None:
        """Synchronous file save (runs in thread pool)."""
        self._engine.save_to_file(text, filepath)
        self._engine.runAndWait()

    def set_voice(self, voice_index: int = 0) -> None:
        """Change the voice.
        
        Args:
            voice_index: Index of the voice to use (0 = default).
        """
        self._init_engine()
        voices = self._engine.getProperty('voices')
        if 0 <= voice_index < len(voices):
            self._engine.setProperty('voice', voices[voice_index].id)

    @property
    def is_available(self) -> bool:
        """Check if pyttsx3 is installed."""
        try:
            import pyttsx3  # noqa: F401
            return True
        except ImportError:
            return False
