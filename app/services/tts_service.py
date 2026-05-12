"""Compatibility exports for text-to-speech services."""

from app.services.speech.tts_service import (
    MeloTTSService,
    MockTTSService,
    TTSResult,
    TTSService,
    get_tts_service,
)

__all__ = [
    "MeloTTSService",
    "MockTTSService",
    "TTSResult",
    "TTSService",
    "get_tts_service",
]
