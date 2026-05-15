"""Audio preprocessing utilities for OpenVoice reference and synthesis inputs."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class AudioPreprocessService:
    """Prepare audio files for downstream OpenVoice processing."""

    def __init__(self) -> None:
        self._ffmpeg_available: bool | None = None

    def prepare_reference_audios(
        self,
        reference_audio_paths: list[str],
        output_dir: Path,
        sample_rate: int = 16000,
    ) -> list[str]:
        if not reference_audio_paths:
            raise RuntimeError("Reference audio paths are empty.")

        output_dir.mkdir(parents=True, exist_ok=True)
        processed_paths: list[str] = []
        for index, raw_path in enumerate(reference_audio_paths):
            source = self._resolve_existing_path(raw_path)
            out_path = output_dir / f"reference_{index:03d}.wav"
            processed_paths.append(self._to_wav_mono(source, out_path, sample_rate))
        return processed_paths

    def ensure_wav_mono(
        self,
        source_audio_path: str,
        output_path: str,
        sample_rate: int = 16000,
    ) -> str:
        source = self._resolve_existing_path(source_audio_path)
        return self._to_wav_mono(source, Path(output_path), sample_rate)

    def _resolve_existing_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if not path.is_file():
            raise RuntimeError(f"Audio file not found: {path}")
        return path

    def _to_wav_mono(self, source: Path, output: Path, sample_rate: int) -> str:
        output.parent.mkdir(parents=True, exist_ok=True)
        if self._run_ffmpeg_convert(source, output, sample_rate):
            return str(output).replace("\\", "/")

        # If ffmpeg is unavailable, pass through only if already wav.
        if source.suffix.lower() == ".wav":
            if source.resolve() != output.resolve():
                shutil.copyfile(source, output)
                return str(output).replace("\\", "/")
            return str(source).replace("\\", "/")

        raise RuntimeError(
            "ffmpeg is required to convert non-wav audio for OpenVoice preprocessing."
        )

    def _run_ffmpeg_convert(self, source: Path, output: Path, sample_rate: int) -> bool:
        if not self._has_ffmpeg():
            return False

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            str(output),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr.strip()[:300]}")
        return True

    def _has_ffmpeg(self) -> bool:
        if self._ffmpeg_available is not None:
            return self._ffmpeg_available

        result = shutil.which("ffmpeg")
        self._ffmpeg_available = result is not None
        return self._ffmpeg_available

