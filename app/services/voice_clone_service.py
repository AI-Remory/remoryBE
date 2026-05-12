"""Compatibility exports for voice clone services."""

from app.services.speech.voice_clone_service import (
    MockVoiceCloneService,
    OpenVoiceV2VoiceCloneService,
    VoiceCloneResult,
    VoiceCloneService,
    ensure_voice_clone_allowed,
    get_voice_clone_service,
)

__all__ = [
    "MockVoiceCloneService",
    "OpenVoiceV2VoiceCloneService",
    "VoiceCloneResult",
    "VoiceCloneService",
    "ensure_voice_clone_allowed",
    "get_voice_clone_service",
]
