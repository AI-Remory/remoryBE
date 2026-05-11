"""Voice cloning service interface and implementations."""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.consent import ConsentLog, ConsentType
from app.models.target_verification import TargetVerificationRequest, VerificationStatus
from app.utils.exceptions import ForbiddenException


@dataclass
class VoiceCloneResult:
    audio_file_path: str
    provider: str


class VoiceCloneService(ABC):
    """Abstract base class for voice cloning providers."""

    @abstractmethod
    async def create_voice_profile(
        self,
        persona_id: int,
        reference_audio_paths: list[str],
    ) -> dict: ...

    @abstractmethod
    async def synthesize_with_cloned_voice(
        self,
        text: str,
        voice_profile: dict,
        output_path: str,
    ) -> VoiceCloneResult: ...


class MockVoiceCloneService(VoiceCloneService):
    """Deterministic mock voice cloning service used in tests and as fallback."""

    async def create_voice_profile(
        self,
        persona_id: int,
        reference_audio_paths: list[str],
    ) -> dict:
        return {
            "persona_id": persona_id,
            "provider": "mock",
            "model_name": None,
            "status": "READY",
            "reference_audio_count": len(reference_audio_paths),
            "reference_audio_total_seconds": None,
            "voice_profile_path": None,
            "sample_audio_path": None,
            "error_message": None,
        }

    async def synthesize_with_cloned_voice(
        self,
        text: str,
        voice_profile: dict,
        output_path: str,
    ) -> VoiceCloneResult:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(self._silent_wav_bytes())
        return VoiceCloneResult(
            audio_file_path=str(path),
            provider="mock",
        )

    @staticmethod
    def _silent_wav_bytes() -> bytes:
        return (
            b"RIFF$\x00\x00\x00WAVEfmt "
            b"\x10\x00\x00\x00\x01\x00\x01\x00"
            b"@\x1f\x00\x00@\x1f\x00\x00"
            b"\x01\x00\x08\x00data\x00\x00\x00\x00"
        )


class OpenVoiceV2VoiceCloneService(VoiceCloneService):
    """OpenVoice V2 integration shell with optional lazy imports.

    OpenVoice is intentionally optional. If the package, checkpoints, or runtime
    path are unavailable, calls fall back to the mock service instead of failing
    application startup.
    """

    def __init__(self, model_name: str = "openvoice-v2") -> None:
        self.model_name = model_name
        self._converter: Any | None = None
        self._mock = MockVoiceCloneService()

    async def create_voice_profile(
        self,
        persona_id: int,
        reference_audio_paths: list[str],
    ) -> dict:
        try:
            return await asyncio.to_thread(self._create_voice_profile_sync, persona_id, reference_audio_paths)
        except Exception as exc:
            profile = await self._mock.create_voice_profile(persona_id, reference_audio_paths)
            profile.update(
                {
                    "provider": "openvoice",
                    "model_name": self.model_name,
                    "status": "FAILED",
                    "error_message": str(exc)[:500],
                }
            )
            return profile

    async def synthesize_with_cloned_voice(
        self,
        text: str,
        voice_profile: dict,
        output_path: str,
    ) -> VoiceCloneResult:
        try:
            await asyncio.to_thread(self._synthesize_sync, text, voice_profile, output_path)
            return VoiceCloneResult(audio_file_path=output_path, provider="openvoice")
        except Exception:
            return await self._mock.synthesize_with_cloned_voice(text, voice_profile, output_path)

    def _create_voice_profile_sync(self, persona_id: int, reference_audio_paths: list[str]) -> dict:
        self._get_converter()
        # TODO: Extract and persist OpenVoice V2 speaker embeddings once model
        # checkpoints and storage layout are finalized.
        return {
            "persona_id": persona_id,
            "provider": "openvoice",
            "model_name": self.model_name,
            "status": "PENDING",
            "reference_audio_count": len(reference_audio_paths),
            "reference_audio_total_seconds": None,
            "voice_profile_path": None,
            "sample_audio_path": None,
            "error_message": None,
        }

    def _synthesize_sync(self, text: str, voice_profile: dict, output_path: str) -> None:
        self._get_converter()
        # TODO: Wire OpenVoice V2 tone color conversion here after base TTS audio
        # generation and speaker embedding persistence are available.
        raise NotImplementedError("OpenVoice V2 synthesis is not wired yet")

    def _get_converter(self):
        if self._converter is None:
            from openvoice.api import ToneColorConverter

            checkpoint_path = settings.OPENVOICE_CHECKPOINT_PATH or None
            if not checkpoint_path:
                raise RuntimeError("OPENVOICE_CHECKPOINT_PATH is not configured")
            self._converter = ToneColorConverter(checkpoint_path, device="cpu")
        return self._converter


def ensure_voice_clone_allowed(db: Session, user_id: int, target_id: int) -> None:
    """Validate policy gates before creating a voice clone profile.

    This is the service-layer checkpoint for the future API: voice cloning must
    require target verification approval and explicit voice collection consent.
    """

    verification = db.execute(
        select(TargetVerificationRequest).where(
            TargetVerificationRequest.target_id == target_id,
            TargetVerificationRequest.status == VerificationStatus.APPROVED,
            TargetVerificationRequest.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if verification is None:
        raise ForbiddenException("Target verification approval is required before voice cloning.")

    consent = db.execute(
        select(ConsentLog).where(
            ConsentLog.user_id == user_id,
            ConsentLog.target_id == target_id,
            ConsentLog.consent_type == ConsentType.VOICE_COLLECTION,
            ConsentLog.is_consented == True,
        )
    ).scalar_one_or_none()
    if consent is None:
        raise ForbiddenException("Voice collection consent is required before voice cloning.")


def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def get_voice_clone_service() -> VoiceCloneService:
    """Return the configured voice cloning service instance."""

    if settings.ENVIRONMENT == "test" or _running_under_pytest():
        return MockVoiceCloneService()

    if settings.VOICE_CLONE_PROVIDER == "openvoice":
        return OpenVoiceV2VoiceCloneService()

    return MockVoiceCloneService()
