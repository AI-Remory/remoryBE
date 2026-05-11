"""Text-to-Speech service interface and implementations."""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.settings import settings


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
    """Deterministic mock TTS service used in tests and as fallback."""

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_profile=None,
    ) -> TTSResult:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(self._silent_wav_bytes())
        return TTSResult(
            audio_file_path=str(path),
            provider="mock",
            duration_seconds=None,
        )

    @staticmethod
    def _silent_wav_bytes() -> bytes:
        return (
            b"RIFF$\x00\x00\x00WAVEfmt "
            b"\x10\x00\x00\x00\x01\x00\x01\x00"
            b"@\x1f\x00\x00@\x1f\x00\x00"
            b"\x01\x00\x08\x00data\x00\x00\x00\x00"
        )


class MeloTTSService(TTSService):
    """MeloTTS-based TTS service with lazy model loading and mock fallback."""

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        self._mock = MockTTSService()

    async def synthesize(
        self,
        text: str,
        output_path: str,
        voice_profile=None,
    ) -> TTSResult:
        if not text.strip():
            return await self._mock.synthesize(text, output_path, voice_profile)

        try:
            await asyncio.to_thread(self._synthesize_sync, text, output_path, voice_profile or {})
        except Exception:
            return await self._mock.synthesize(text, output_path, voice_profile)

        return TTSResult(
            audio_file_path=output_path,
            provider="melotts",
            duration_seconds=None,
        )

    def _synthesize_sync(self, text: str, output_path: str, voice_profile: dict) -> None:
        language = voice_profile.get("language") or voice_profile.get("lang") or "EN"
        model = self._get_model(language)
        speaker_id = self._speaker_id(model, voice_profile)
        speed = float(voice_profile.get("speed", 1.0))

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        model.tts_to_file(text, speaker_id, output_path, speed=speed)

    def _get_model(self, language: str):
        language = language.upper()
        if language not in self._models:
            from melo.api import TTS

            self._models[language] = TTS(language=language, device="cpu")
        return self._models[language]

    @staticmethod
    def _speaker_id(model, voice_profile: dict) -> int:
        if "speaker_id" in voice_profile:
            return int(voice_profile["speaker_id"])

        speaker_name = voice_profile.get("speaker_name")
        speaker_ids = getattr(getattr(model, "hps", None), "data", None)
        speaker_ids = getattr(speaker_ids, "spk2id", None)
        if isinstance(speaker_ids, dict) and speaker_ids:
            if speaker_name in speaker_ids:
                return int(speaker_ids[speaker_name])
            return int(next(iter(speaker_ids.values())))

        return 0


def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def get_tts_service() -> TTSService:
    """Return the configured TTS service instance."""

    if settings.ENVIRONMENT == "test" or _running_under_pytest():
        return MockTTSService()

    if settings.TTS_PROVIDER == "melotts":
        return MeloTTSService()

    return MockTTSService()
