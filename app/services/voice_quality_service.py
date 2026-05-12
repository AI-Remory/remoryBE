"""Voice sample quality checks for persona voice profile creation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.media import MediaType, TargetMedia
from app.services.speech import get_voice_clone_service


@dataclass
class VoiceSampleCheckResult:
    reference_audio_paths: list[str]
    total_duration_ms: int
    noise_score: float
    quality_score: float
    similarity_score: float
    error_message: str | None = None


class VoiceQualityService:
    """MVP-level quality checks with a stable interface for real analyzers later."""

    @staticmethod
    def check_voice_samples(db: Session, target_id: int) -> VoiceSampleCheckResult:
        media_items = (
            db.execute(
                select(TargetMedia)
                .where(
                    TargetMedia.target_id == target_id,
                    TargetMedia.media_type == MediaType.VOICE,
                    TargetMedia.is_deleted == False,
                )
                .order_by(TargetMedia.created_at.asc(), TargetMedia.id.asc())
            )
            .scalars()
            .all()
        )

        valid_items: list[TargetMedia] = []
        for item in media_items:
            if not item.mime_type or not item.mime_type.startswith("audio/"):
                continue
            if (item.file_size or 0) < settings.VOICE_SAMPLE_MIN_FILE_SIZE_BYTES:
                continue
            valid_items.append(item)

        count_ok, count_error = VoiceQualityService.validate_minimum_sample_count(valid_items)
        if not count_ok:
            return VoiceSampleCheckResult([], 0, 0.0, 0.0, 0.0, count_error)

        total_duration_ms = VoiceQualityService.calculate_total_duration(valid_items)
        duration_ok, duration_error = VoiceQualityService.validate_minimum_total_duration(total_duration_ms)
        if not duration_ok:
            return VoiceSampleCheckResult(
                [item.file_path for item in valid_items],
                total_duration_ms,
                0.0,
                0.0,
                0.0,
                duration_error,
            )

        noise_score = VoiceQualityService.estimate_noise_score(valid_items)
        quality_score = max(0.0, min(1.0, (total_duration_ms / 60000.0) * 0.4 + (1.0 - noise_score) * 0.6))
        similarity_score = max(0.0, min(1.0, 0.7 + (len(valid_items) / 20.0)))

        return VoiceSampleCheckResult(
            reference_audio_paths=[item.file_path for item in valid_items],
            total_duration_ms=total_duration_ms,
            noise_score=noise_score,
            quality_score=quality_score,
            similarity_score=similarity_score,
            error_message=None,
        )

    @staticmethod
    def calculate_total_duration(media_items: list[TargetMedia]) -> int:
        total = 0
        for item in media_items:
            if item.duration_seconds:
                total += int(item.duration_seconds * 1000)
            else:
                # Approximation fallback for MVP: infer rough duration from file size.
                total += int((item.file_size or 0) / 32)
        return total

    @staticmethod
    def estimate_noise_score(media_items: list[TargetMedia]) -> float:
        if not media_items:
            return 1.0
        # Placeholder heuristic: very small files are treated as noisier samples.
        min_size = min(item.file_size or 0 for item in media_items)
        if min_size < 4096:
            return 0.65
        if min_size < 16384:
            return 0.45
        return 0.2

    @staticmethod
    def validate_minimum_sample_count(media_items: list[TargetMedia]) -> tuple[bool, str | None]:
        if len(media_items) < settings.VOICE_SAMPLE_MIN_COUNT:
            return False, f"At least {settings.VOICE_SAMPLE_MIN_COUNT} voice sample(s) are required"
        return True, None

    @staticmethod
    def validate_minimum_total_duration(total_duration_ms: int) -> tuple[bool, str | None]:
        if total_duration_ms < settings.VOICE_SAMPLE_MIN_TOTAL_DURATION_MS:
            return (
                False,
                f"Minimum total voice duration is {settings.VOICE_SAMPLE_MIN_TOTAL_DURATION_MS}ms",
            )
        return True, None

    @staticmethod
    async def generate_sample_output(persona_id: int, voice_profile_payload: dict) -> str:
        output_dir = Path(settings.UPLOAD_DIR) / "voices" / "samples" / str(persona_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"sample_{uuid4().hex}.wav"
        result = await get_voice_clone_service().synthesize_with_cloned_voice(
            "안녕하세요. 이 음성은 품질 평가를 위한 샘플입니다.",
            voice_profile_payload,
            str(output_path),
        )
        return result.audio_file_path


voice_quality_service = VoiceQualityService()


