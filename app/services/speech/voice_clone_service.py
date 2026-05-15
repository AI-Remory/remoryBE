"""Voice cloning service interface and implementations."""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.consent import ConsentType
from app.models.target_verification import TargetVerificationRequest, VerificationStatus
from app.services.consent_service import consent_service
from app.services.speech.openvoice_service import OpenVoiceService
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
    """OpenVoice V2 integration with lazy loading."""

    def __init__(self, model_name: str = "openvoice-v2") -> None:
        self.model_name = model_name
        self._mock = MockVoiceCloneService()
        self._openvoice = OpenVoiceService()

    @property
    def _converter(self):
        return getattr(self._openvoice, "_converter", None)

    async def create_voice_profile(
        self,
        persona_id: int,
        reference_audio_paths: list[str],
    ) -> dict:
        try:
            return await asyncio.to_thread(self._create_voice_profile_sync, persona_id, reference_audio_paths)
        except Exception as exc:
            error_message = self._short_error(exc)
            if self._should_failover_to_mock():
                profile = await self._mock.create_voice_profile(persona_id, reference_audio_paths)
                profile.update(
                    {
                        "provider": "mock",
                        "model_name": self.model_name,
                        "status": "READY",
                        "error_message": f"OpenVoice fallback: {error_message}",
                    }
                )
                return profile
            return {
                "persona_id": persona_id,
                "provider": "openvoice",
                "model_name": self.model_name,
                "status": "FAILED",
                "reference_audio_count": len(reference_audio_paths),
                "reference_audio_total_seconds": None,
                "voice_profile_path": None,
                "sample_audio_path": None,
                "error_message": error_message,
            }

    async def synthesize_with_cloned_voice(
        self,
        text: str,
        voice_profile: dict,
        output_path: str,
    ) -> VoiceCloneResult:
        try:
            audio_path = await asyncio.to_thread(self._synthesize_sync, text, voice_profile, output_path)
            return VoiceCloneResult(audio_file_path=audio_path, provider="openvoice")
        except Exception as exc:
            if self._should_failover_to_mock():
                return await self._mock.synthesize_with_cloned_voice(text, voice_profile, output_path)
            raise RuntimeError(self._short_error(exc)) from exc

    def _create_voice_profile_sync(self, persona_id: int, reference_audio_paths: list[str]) -> dict:
        profile = self._openvoice.create_profile(persona_id, reference_audio_paths)
        profile["provider"] = "openvoice"
        profile["model_name"] = self.model_name
        return profile

    def _synthesize_sync(self, text: str, voice_profile: dict, output_path: str) -> str:
        profile_path = voice_profile.get("voice_profile_path")
        if not profile_path:
            raise RuntimeError("voice_profile_path is required for OpenVoice synthesis.")
        return self._openvoice.synthesize(text=text, voice_profile_path=profile_path, output_path=output_path)

    @staticmethod
    def _short_error(exc: Exception) -> str:
        return str(exc).strip()[:500] or "OpenVoice runtime error"

    @staticmethod
    def _should_failover_to_mock() -> bool:
        return bool(settings.OPENVOICE_FAILOVER_TO_MOCK and not settings.is_production)


def ensure_voice_clone_allowed(db: Session, user_id: int, target_id: int) -> None:
    """Validate policy gates before creating a voice clone profile.

    This is the service-layer checkpoint: voice cloning requires target
    verification approval, voice upload consent, and voice cloning consent.
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

    consent_service.check_consent(db, user_id, target_id, ConsentType.VOICE_UPLOAD_CONSENT)
    consent_service.check_consent(db, user_id, target_id, ConsentType.VOICE_CLONING_CONSENT)


def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def get_voice_clone_service() -> VoiceCloneService:
    """Return the configured voice cloning service instance."""

    if settings.ENVIRONMENT == "test" or _running_under_pytest():
        return MockVoiceCloneService()

    if settings.VOICE_CLONE_PROVIDER == "openvoice":
        return OpenVoiceV2VoiceCloneService()

    return MockVoiceCloneService()
