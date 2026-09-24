"""Speech-to-text using OpenAI Whisper (runs locally).

This module provides local speech recognition without sending
audio data to external servers, ensuring user privacy.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SpeechToText:
    """Local speech-to-text using OpenAI Whisper.
    
    Whisper runs entirely on your machine - no audio is sent
    to any cloud service.
    """

    def __init__(self, model_size: str = "base"):
        """Initialize Whisper model.
        
        Args:
            model_size: Whisper model size. Options: tiny, base, small, 
                       medium, large. Smaller = faster, larger = more accurate.
        """
        self._model = None
        self._model_size = model_size
        self._loaded = False

    def _load_model(self) -> None:
        """Lazy-load the Whisper model on first use."""
        if self._loaded:
            return
        try:
            import whisper
            logger.info(f"Loading Whisper model: {self._model_size}")
            self._model = whisper.load_model(self._model_size)
            self._loaded = True
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error(
                "Whisper not installed. Install with: pip install openai-whisper"
            )
            raise RuntimeError(
                "openai-whisper is not installed. "
                "Run: pip install openai-whisper"
            )
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    async def transcribe(self, audio_path: str | Path) -> str:
        """Transcribe an audio file to text.
        
        Args:
            audio_path: Path to the audio file (WAV, MP3, etc.).
            
        Returns:
            Transcribed text string.
            
        Raises:
            FileNotFoundError: If audio file doesn't exist.
            RuntimeError: If Whisper is not installed or transcription fails.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()

        try:
            import asyncio
            # Run in thread pool since Whisper is CPU-bound
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self._model.transcribe(str(audio_path))
            )
            text = result.get("text", "").strip()
            logger.info(f"Transcribed: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

    @property
    def is_available(self) -> bool:
        """Check if Whisper is installed and usable."""
        try:
            import whisper  # noqa: F401
            return True
        except ImportError:
            return False
