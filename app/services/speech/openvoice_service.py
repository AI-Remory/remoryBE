"""OpenVoice V2 runtime integration with lazy loading."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from uuid import uuid4
from typing import Any

from app.core.settings import settings
from app.services.speech.audio_preprocess_service import AudioPreprocessService
from app.services.speech.base_tts_service import BaseTTSService


class OpenVoiceService:
    """OpenVoice helper for converter init, profile creation and synthesis."""

    def __init__(self) -> None:
        self._converter: Any | None = None
        self._device: str | None = None
        self._audio_preprocess = AudioPreprocessService()
        self._base_tts = BaseTTSService()

    @property
    def converter(self) -> Any:
        return self._get_converter()

    def create_profile(self, persona_id: int, reference_audio_paths: list[str]) -> dict:
        if not reference_audio_paths:
            raise RuntimeError("Reference voice audio is required.")

        profile_dir = self._profiles_dir(persona_id)
        prepared_dir = profile_dir / "prepared"
        prepared_paths = self._audio_preprocess.prepare_reference_audios(reference_audio_paths, prepared_dir)

        converter = self._get_converter()
        target_se = self._extract_target_se(prepared_paths, converter)

        target_se_path = profile_dir / "target_se.pth"
        self._save_tensor(target_se, target_se_path)

        metadata_path = profile_dir / "profile_metadata.json"
        metadata = {
            "persona_id": persona_id,
            "provider": "openvoice",
            "model_name": "openvoice-v2",
            "target_se_path": str(target_se_path).replace("\\", "/"),
            "reference_audio_paths": [str(Path(p)).replace("\\", "/") for p in reference_audio_paths],
            "prepared_audio_paths": prepared_paths,
            "device": self._get_device(),
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "persona_id": persona_id,
            "provider": "openvoice",
            "model_name": "openvoice-v2",
            "status": "READY",
            "reference_audio_count": len(prepared_paths),
            "reference_audio_total_seconds": None,
            "voice_profile_path": str(target_se_path).replace("\\", "/"),
            "sample_audio_path": None,
            "error_message": None,
        }

    def synthesize(
        self,
        text: str,
        voice_profile_path: str,
        output_path: str,
    ) -> str:
        if not text or not text.strip():
            raise RuntimeError("Text is required for OpenVoice synthesis.")

        converter = self._get_converter()
        target_se_path = self._resolve_path(voice_profile_path, required=True)
        source_se_path = self._resolve_source_se_path()

        source_tmp_dir = self._tmp_dir()
        source_wav = source_tmp_dir / f"source_{uuid4().hex}.wav"
        self._base_tts.synthesize_to_wav(
            text=text,
            output_path=str(source_wav),
            language=settings.OPENVOICE_TTS_LANGUAGE,
            speed=settings.OPENVOICE_TTS_SPEED,
            speaker_name=settings.OPENVOICE_BASE_SPEAKER,
        )

        target_se = self._load_tensor(target_se_path)
        source_se = self._load_tensor(source_se_path)

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self._run_conversion(
            converter=converter,
            source_wav=str(source_wav).replace("\\", "/"),
            source_se=source_se,
            target_se=target_se,
            output_wav=str(out_path).replace("\\", "/"),
            watermark=settings.OPENVOICE_WATERMARK_MESSAGE,
        )

        if not out_path.is_file() or out_path.stat().st_size <= 0:
            raise RuntimeError("OpenVoice synthesis completed but output wav is missing or empty.")
        return str(out_path).replace("\\", "/")

    def _get_converter(self):
        if self._converter is not None:
            return self._converter

        config_path = self._resolve_converter_config_path()
        checkpoint_path = self._resolve_converter_checkpoint_path()
        device = self._get_device()

        try:
            from openvoice.api import ToneColorConverter
        except Exception as exc:
            raise RuntimeError("OpenVoice package is not installed or import failed.") from exc

        converter = ToneColorConverter(str(config_path), device=device)
        converter.load_ckpt(str(checkpoint_path))
        self._converter = converter
        return self._converter

    def _extract_target_se(self, prepared_paths: list[str], converter) -> Any:
        try:
            from openvoice import se_extractor
        except Exception as exc:
            raise RuntimeError("OpenVoice speaker embedding extractor import failed.") from exc

        if not prepared_paths:
            raise RuntimeError("No prepared reference audio paths.")

        ref_path = prepared_paths[0]
        get_se = se_extractor.get_se
        # Primary known signature: get_se(audio_path, tone_color_converter, vad=False)
        try:
            extracted = get_se(ref_path, converter, vad=True)
            return extracted[0] if isinstance(extracted, tuple) else extracted
        except TypeError:
            pass

        # Fallback by signature mapping for version differences.
        signature = inspect.signature(get_se)
        kwargs: dict[str, Any] = {}
        for name in signature.parameters:
            if name in {"wav_path", "audio_path", "ref_audio_path"}:
                kwargs[name] = ref_path
            elif name in {"tone_color_converter", "converter", "vc_model"}:
                kwargs[name] = converter
            elif name == "vad":
                kwargs[name] = True
        extracted = get_se(**kwargs)
        return extracted[0] if isinstance(extracted, tuple) else extracted

    @staticmethod
    def _run_conversion(
        converter,
        source_wav: str,
        source_se: Any,
        target_se: Any,
        output_wav: str,
        watermark: str,
    ) -> None:
        try:
            converter.convert(
                audio_src_path=source_wav,
                src_se=source_se,
                tgt_se=target_se,
                output_path=output_wav,
                message=watermark,
            )
            return
        except TypeError:
            pass

        converter.convert(source_wav, source_se, target_se, output_wav, watermark)

    def _resolve_converter_config_path(self) -> Path:
        explicit = settings.OPENVOICE_CONVERTER_CONFIG_PATH.strip()
        if explicit:
            return self._resolve_path(explicit, required=True)

        root = settings.OPENVOICE_CHECKPOINT_ROOT.strip()
        if root:
            candidate = self._resolve_path(f"{root}/converter/config.json", required=False)
            if candidate.is_file():
                return candidate
        raise RuntimeError("OPENVOICE_CONVERTER_CONFIG_PATH is not configured.")

    def _resolve_converter_checkpoint_path(self) -> Path:
        explicit = settings.OPENVOICE_CONVERTER_CHECKPOINT_PATH.strip()
        if explicit:
            return self._resolve_path(explicit, required=True)

        root = settings.OPENVOICE_CHECKPOINT_ROOT.strip()
        if root:
            candidate = self._resolve_path(f"{root}/converter/checkpoint.pth", required=False)
            if candidate.is_file():
                return candidate
        raise RuntimeError("OPENVOICE_CONVERTER_CHECKPOINT_PATH is not configured.")

    def _resolve_source_se_path(self) -> Path:
        explicit = settings.OPENVOICE_SOURCE_SE_PATH.strip()
        if explicit:
            return self._resolve_path(explicit, required=True)

        root = settings.OPENVOICE_CHECKPOINT_ROOT.strip()
        if root:
            candidate = self._resolve_path(f"{root}/base_speakers/ses/zh.pth", required=False)
            if candidate.is_file():
                return candidate
        raise RuntimeError("OPENVOICE_SOURCE_SE_PATH is not configured.")

    def _profiles_dir(self, persona_id: int) -> Path:
        base = self._resolve_path(settings.OPENVOICE_OUTPUT_DIR, required=False)
        path = base / "profiles" / f"persona_{persona_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _tmp_dir(self) -> Path:
        base = self._resolve_path(settings.OPENVOICE_OUTPUT_DIR, required=False)
        path = base / "tmp"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_device(self) -> str:
        if self._device is not None:
            return self._device

        requested = (settings.OPENVOICE_DEVICE or "auto").strip().lower()
        if requested in {"", "auto"}:
            requested = "cuda" if self._cuda_available() else "cpu"

        if requested == "cuda" and not self._cuda_available():
            raise RuntimeError("OPENVOICE_DEVICE is cuda but CUDA is not available.")

        self._device = requested
        return self._device

    @staticmethod
    def _cuda_available() -> bool:
        try:
            import torch
            return bool(torch.cuda.is_available())
        except Exception:
            return False

    @staticmethod
    def _save_tensor(value: Any, output_path: Path) -> None:
        try:
            import torch
        except Exception as exc:
            raise RuntimeError("torch is required for OpenVoice tensor persistence.") from exc
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(value, str(output_path))

    @staticmethod
    def _load_tensor(input_path: Path) -> Any:
        try:
            import torch
        except Exception as exc:
            raise RuntimeError("torch is required for OpenVoice tensor loading.") from exc
        return torch.load(str(input_path), map_location="cpu")

    @staticmethod
    def _resolve_path(raw_path: str, required: bool = True) -> Path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if required and not path.exists():
            raise RuntimeError(f"Path does not exist: {path}")
        return path

