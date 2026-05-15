"""Base TTS adapter used by OpenVoice tone conversion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.settings import settings


class BaseTTSService:
    """Generate source speech wav used before OpenVoice conversion."""

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}

    def synthesize_to_wav(
        self,
        text: str,
        output_path: str,
        language: str | None = None,
        speed: float | None = None,
        speaker_name: str | None = None,
    ) -> str:
        if not text or not text.strip():
            raise RuntimeError("Text is required for base TTS synthesis.")

        language = (language or settings.OPENVOICE_TTS_LANGUAGE or "KR").upper()
        speed = float(speed if speed is not None else settings.OPENVOICE_TTS_SPEED)
        speaker_name = speaker_name or settings.OPENVOICE_BASE_SPEAKER

        model = self._get_model(language)
        speaker_id = self._resolve_speaker_id(model, speaker_name)

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        model.tts_to_file(text, speaker_id, str(path), speed=speed)

        if not path.is_file() or path.stat().st_size <= 0:
            raise RuntimeError("Base TTS output file was not created.")
        return str(path).replace("\\", "/")

    def _get_model(self, language: str):
        if language not in self._models:
            try:
                from melo.api import TTS
            except Exception as exc:
                raise RuntimeError("MeloTTS is not installed. Install melo-tts for OpenVoice synthesis.") from exc
            self._models[language] = TTS(language=language, device="cpu")
        return self._models[language]

    @staticmethod
    def _resolve_speaker_id(model: Any, speaker_name: str | None) -> int:
        speaker_ids = getattr(getattr(model, "hps", None), "data", None)
        speaker_ids = getattr(speaker_ids, "spk2id", None)
        if not isinstance(speaker_ids, dict) or not speaker_ids:
            return 0
        if speaker_name and speaker_name in speaker_ids:
            return int(speaker_ids[speaker_name])
        return int(next(iter(speaker_ids.values())))

