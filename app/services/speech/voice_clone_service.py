"""Voice Cloning service interface and mock implementation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VoiceCloneResult:
    audio_file_path: str
    provider: str


class VoiceCloneService(ABC):
    """Abstract base class for Voice Cloning providers."""

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
    """Mock Voice Cloning service — used in test env and as fallback."""

    async def create_voice_profile(
        self,
        persona_id: int,
        reference_audio_paths: list[str],
    ) -> dict:
        return {
            "persona_id": persona_id,
            "provider": "mock",
            "status": "READY",
            "reference_audio_count": len(reference_audio_paths),
        }

    async def synthesize_with_cloned_voice(
        self,
        text: str,
        voice_profile: dict,
        output_path: str,
    ) -> VoiceCloneResult:
        return VoiceCloneResult(
            audio_file_path=output_path,
            provider="mock",
        )
