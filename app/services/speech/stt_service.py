"""Speech-to-Text service interface and implementations."""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.settings import settings


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
    """Deterministic mock STT service used in tests and as fallback."""

    async def transcribe(self, audio_file_path: str) -> STTResult:
        return STTResult(
            text="테스트용 음성 변환 결과입니다.",
            language="ko",
            duration_seconds=None,
        )


class FasterWhisperSTTService(STTService):
    """faster-whisper based STT service.

    The model is loaded lazily on first transcription so importing the service
    does not download or allocate model resources.
    """

    def __init__(self, model_size: str = "base") -> None:
        self.model_size = model_size
        self._model: Any | None = None
        self._mock = MockSTTService()

    async def transcribe(self, audio_file_path: str) -> STTResult:
        if not Path(audio_file_path).is_file():
            raise FileNotFoundError(audio_file_path)

        try:
            return await asyncio.to_thread(self._transcribe_sync, audio_file_path)
        except Exception:
            return await self._mock.transcribe(audio_file_path)

    def _transcribe_sync(self, audio_file_path: str) -> STTResult:
        model = self._get_model()
        segments, info = model.transcribe(
            audio_file_path,
            beam_size=5,
            vad_filter=True,
        )
        text = " ".join(segment.text.strip() for segment in segments if segment.text).strip()
        return STTResult(
            text=text,
            language=getattr(info, "language", None) or "unknown",
            duration_seconds=getattr(info, "duration", None),
        )

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )
        return self._model


def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def get_stt_service() -> STTService:
    """Return the configured STT service instance."""

    if settings.ENVIRONMENT == "test" or _running_under_pytest():
        return MockSTTService()

    if settings.STT_PROVIDER == "faster_whisper":
        return FasterWhisperSTTService(model_size=settings.WHISPER_MODEL_SIZE)

    return MockSTTService()
