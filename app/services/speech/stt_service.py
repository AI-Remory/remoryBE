"""Speech-to-Text service interface and mock implementation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class STTResult:
    text: str
    language: str
    duration_seconds: float | None = None


class STTService(ABC):
    """Abstract base class for STT providers."""

    @abstractmethod
    async def transcribe(self, audio_file_path: str) -> STTResult: ...


class MockSTTService(STTService):
    """Mock STT service — used in test env and as fallback."""

    async def transcribe(self, audio_file_path: str) -> STTResult:
        return STTResult(
            text="테스트용 음성 변환 결과입니다.",
            language="ko",
            duration_seconds=None,
        )
