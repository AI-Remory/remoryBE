"""Text-to-Speech service interface and mock implementation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSResult:
    audio_file_path: str
    provider: str
    duration_seconds: float | None = None


class TTSService(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_profile=None,
    ) -> TTSResult: ...


class MockTTSService(TTSService):
    """Mock TTS service — used in test env and as fallback."""

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_profile=None,
    ) -> TTSResult:
        return TTSResult(
            audio_file_path=output_path,
            provider="mock",
            duration_seconds=None,
        )
