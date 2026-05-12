"""Compatibility exports for speech-to-text services."""

from app.services.speech.stt_service import (
    FasterWhisperSTTService,
    MockSTTService,
    STTResult,
    STTService,
    get_stt_service,
)

__all__ = [
    "FasterWhisperSTTService",
    "MockSTTService",
    "STTResult",
    "STTService",
    "get_stt_service",
]
