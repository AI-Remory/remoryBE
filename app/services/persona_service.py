"""Persona business logic."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.settings import settings
from app.models.audit_log import AuditAction, AuditTargetType
from app.models.media import MediaType, TargetMedia
from app.models.persona import (
    Persona,
    PersonaStatus,
    PersonaVoiceProfile,
    VoiceProfileReviewStatus,
    VoiceProfileStatus,
)
from app.models.target import Target
from app.services.ai_service import ai_service
from app.services.audit_log_service import AuditLogService
from app.services.consent_service import consent_service
from app.services.speech import get_voice_clone_service
from app.services.voice_quality_service import voice_quality_service
from app.services.verification_service import verification_service
from app.models.consent import ConsentType
from app.utils.exceptions import BadRequestException, ForbiddenException, NotFoundException, RemoryException


class PersonaService:
    """Persona creation and lookup service."""

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _log_voice_profile_event(
        db: Session,
        action: AuditAction,
        actor_user_id: int,
        profile_id: int,
        description: str,
        metadata: dict | None = None,
    ) -> None:
        try:
            AuditLogService.create_audit_log(
                db=db,
                action=action,
                actor_user_id=actor_user_id,
                target_type=AuditTargetType.VOICE_PROFILE,
                target_id=profile_id,
                description=description,
                metadata=metadata,
            )
        except Exception:
            pass

    @staticmethod
    def _get_owned_target(db: Session, target_id: int, user_id: int) -> Target:
        target = db.execute(
            select(Target).where(
                Target.id == target_id,
                Target.is_deleted == False,
            )
        ).scalar_one_or_none()

        if not target:
            raise NotFoundException("Target", target_id)
        if target.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this target")
        return target

    @staticmethod
    def _get_owned_persona(db: Session, persona_id: int, user_id: int) -> Persona:
        persona = db.execute(
            select(Persona)
            .join(Target, Target.id == Persona.target_id)
            .options(joinedload(Persona.voice_profile))
            .where(
                Persona.id == persona_id,
                Persona.is_deleted == False,
                Target.is_deleted == False,
            )
        ).scalar_one_or_none()

        if not persona:
            raise NotFoundException("Persona", persona_id)
        if persona.target.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this persona")
        return persona

    @staticmethod
    def _get_voice_profile_by_id(db: Session, voice_profile_id: int) -> PersonaVoiceProfile:
        profile = db.execute(
            select(PersonaVoiceProfile)
            .options(joinedload(PersonaVoiceProfile.persona).joinedload(Persona.target))
            .where(
                PersonaVoiceProfile.id == voice_profile_id,
                PersonaVoiceProfile.is_deleted == False,
            )
        ).scalar_one_or_none()
        if profile is None:
            raise NotFoundException("PersonaVoiceProfile", voice_profile_id)
        return profile

    @staticmethod
    def _count_media(db: Session, target_id: int, media_type: MediaType) -> int:
        return db.execute(
            select(func.count(TargetMedia.id)).where(
                TargetMedia.target_id == target_id,
                TargetMedia.media_type == media_type,
                TargetMedia.is_deleted == False,
            )
        ).scalar() or 0

    @staticmethod
    def _get_representative_voice(db: Session, target_id: int) -> TargetMedia | None:
        return db.execute(
            select(TargetMedia)
            .where(
                TargetMedia.target_id == target_id,
                TargetMedia.media_type == MediaType.VOICE,
                TargetMedia.is_deleted == False,
            )
            .order_by(TargetMedia.created_at.asc(), TargetMedia.id.asc())
        ).scalars().first()

    @staticmethod
    def _get_voice_media(db: Session, target_id: int) -> list[TargetMedia]:
        return db.execute(
            select(TargetMedia)
            .where(
                TargetMedia.target_id == target_id,
                TargetMedia.media_type == MediaType.VOICE,
                TargetMedia.is_deleted == False,
            )
            .order_by(TargetMedia.created_at.asc(), TargetMedia.id.asc())
        ).scalars().all()

    @staticmethod
    def _ensure_voice_profile_creation_allowed(db: Session, user_id: int, target_id: int) -> None:
        # Policy checkpoint: relationship verification and explicit voice cloning
        # consent must be present before cloned voice assets are created.
        verification = verification_service.get_approved_verification_for_target(db, target_id)
        if verification is None:
            raise ForbiddenException("Target verification approval is required before voice cloning.")
        consent_service.check_consent(db, user_id, target_id, ConsentType.VOICE_UPLOAD_CONSENT)
        consent_service.check_consent(db, user_id, target_id, ConsentType.VOICE_CLONING_CONSENT)

    @staticmethod
    def ensure_voice_clone_usage_allowed(db: Session, persona: Persona, user_id: int) -> PersonaVoiceProfile:
        PersonaService._ensure_voice_profile_creation_allowed(db, user_id, persona.target_id)

        voice_media = PersonaService._get_voice_media(db, persona.target_id)
        if not voice_media:
            raise ForbiddenException("Target voice media is required for voice synthesis.")

        profile = persona.voice_profile
        if profile is None or profile.is_deleted:
            raise ForbiddenException("Voice profile is required for voice synthesis.")
        if profile.status != VoiceProfileStatus.READY:
            raise ForbiddenException("Voice profile is not READY.")
        if profile.review_status not in {
            VoiceProfileReviewStatus.USER_CONFIRMED,
            VoiceProfileReviewStatus.ADMIN_APPROVED,
        }:
            raise ForbiddenException("Voice profile review is not approved.")
        return profile

    @staticmethod
    async def create_persona(db: Session, target_id: int, user_id: int) -> Persona:
        target = PersonaService._get_owned_target(db, target_id, user_id)

        # Check target verification approval
        verification = verification_service.get_approved_verification_for_target(db, target_id)
        if verification is None:
            raise ForbiddenException("Target verification approval is required before creating persona.")

        image_count = PersonaService._count_media(db, target_id, MediaType.IMAGE)
        voice_count = PersonaService._count_media(db, target_id, MediaType.VOICE)

        consent_service.check_consent(db, user_id, target_id, ConsentType.AI_PERSONA_CREATION_CONSENT)
        consent_service.check_consent(db, user_id, target_id, ConsentType.AI_RESPONSE_NOTICE_CONSENT)
        if image_count > 0:
            consent_service.check_consent(db, user_id, target_id, ConsentType.PHOTO_UPLOAD_CONSENT)
        if voice_count > 0:
            PersonaService._ensure_voice_profile_creation_allowed(db, user_id, target_id)

        profile = await ai_service.generate_persona_profile(
            target_name=target.name,
            relationship=target.target_type,
            description=target.description,
            image_count=image_count,
            voice_count=voice_count,
        )

        persona = db.execute(
            select(Persona)
            .options(joinedload(Persona.voice_profile))
            .where(Persona.target_id == target_id)
        ).scalar_one_or_none()

        if persona is None:
            persona = Persona(target_id=target_id)
            db.add(persona)

        persona.status = PersonaStatus.READY
        persona.persona_name = profile["persona_name"]
        persona.speaking_style = profile["speaking_style"]
        persona.personality_summary = profile["personality_summary"]
        persona.memory_summary = profile["memory_summary"]
        persona.system_prompt = profile["system_prompt"]
        persona.is_deleted = False

        representative_voice = PersonaService._get_representative_voice(db, target_id)
        if voice_count > 0 and representative_voice is not None:
            persona.is_voice_profile_created = False
            if persona.voice_profile is None:
                persona.voice_profile = PersonaVoiceProfile()

            persona.voice_profile.reference_voice_file_path = representative_voice.file_path
            persona.voice_profile.reference_voice_mime_type = representative_voice.mime_type
            persona.voice_profile.reference_voice_duration = representative_voice.duration_seconds
            persona.voice_profile.target_id = target_id
            persona.voice_profile.provider = "mock"
            persona.voice_profile.status = VoiceProfileStatus.PENDING
            persona.voice_profile.review_status = VoiceProfileReviewStatus.NOT_REVIEWED
            persona.voice_profile.reference_audio_count = voice_count
            persona.voice_profile.reference_audio_total_seconds = representative_voice.duration_seconds
            persona.voice_profile.total_reference_duration_ms = (representative_voice.duration_seconds or 0) * 1000
            persona.voice_profile.reference_audio_paths_json = [media.file_path for media in PersonaService._get_voice_media(db, target_id)]
            persona.voice_profile.error_message = None
            persona.voice_profile.profile_metadata = {
                "voice_media_count": voice_count,
                "representative_voice_file_path": representative_voice.file_path,
            }
            persona.voice_profile.is_deleted = False
        else:
            persona.is_voice_profile_created = False

        db.commit()
        db.refresh(persona)
        return PersonaService._get_owned_persona(db, persona.id, user_id)

    @staticmethod
    def get_persona(db: Session, persona_id: int, user_id: int) -> Persona:
        return PersonaService._get_owned_persona(db, persona_id, user_id)

    @staticmethod
    def get_persona_status(db: Session, persona_id: int, user_id: int) -> Persona:
        return PersonaService._get_owned_persona(db, persona_id, user_id)

    @staticmethod
    async def create_voice_profile(db: Session, persona_id: int, user_id: int) -> PersonaVoiceProfile:
        persona = PersonaService._get_owned_persona(db, persona_id, user_id)
        PersonaService._ensure_voice_profile_creation_allowed(db, user_id, persona.target_id)

        sample_check = voice_quality_service.check_voice_samples(db, persona.target_id)
        if not sample_check.reference_audio_paths:
            raise RemoryException("Reference voice audio is required", "REFERENCE_AUDIO_REQUIRED")

        if persona.voice_profile is None:
            persona.voice_profile = PersonaVoiceProfile(persona_id=persona.id)

        profile = persona.voice_profile
        profile.target_id = persona.target_id
        profile.provider = "mock"
        profile.model_name = None
        profile.status = (
            VoiceProfileStatus.PENDING
            if sample_check.error_message is None
            else VoiceProfileStatus.NEEDS_MORE_SAMPLES
        )
        profile.review_status = VoiceProfileReviewStatus.NOT_REVIEWED
        profile.reference_audio_count = len(sample_check.reference_audio_paths)
        profile.reference_audio_total_seconds = sample_check.total_duration_ms / 1000 if sample_check.total_duration_ms else None
        profile.reference_audio_paths_json = sample_check.reference_audio_paths
        profile.total_reference_duration_ms = sample_check.total_duration_ms
        profile.voice_profile_path = None
        profile.sample_audio_path = None
        profile.quality_score = None
        profile.similarity_score = None
        profile.noise_score = None
        profile.reviewed_by = None
        profile.reviewed_at = None
        profile.review_note = None
        profile.error_message = sample_check.error_message

        representative_voice = PersonaService._get_voice_media(db, persona.target_id)[0]
        profile.reference_voice_file_path = representative_voice.file_path
        profile.reference_voice_mime_type = representative_voice.mime_type
        profile.reference_voice_duration = representative_voice.duration_seconds
        profile.voice_provider = profile.provider
        profile.profile_metadata = {
            "reference_audio_paths": sample_check.reference_audio_paths,
            "voice_media_count": len(sample_check.reference_audio_paths),
        }
        profile.is_deleted = False
        persona.is_voice_profile_created = False

        db.commit()
        db.refresh(profile)
        PersonaService._log_voice_profile_event(
            db,
            action=AuditAction.VOICE_PROFILE_CREATED,
            actor_user_id=user_id,
            profile_id=profile.id,
            description="Voice profile created",
            metadata={"persona_id": persona.id, "status": profile.status.value},
        )
        return profile

    @staticmethod
    async def evaluate_voice_profile(db: Session, persona_id: int, user_id: int) -> PersonaVoiceProfile:
        persona = PersonaService._get_owned_persona(db, persona_id, user_id)
        PersonaService._ensure_voice_profile_creation_allowed(db, user_id, persona.target_id)

        if persona.voice_profile is None:
            raise NotFoundException("PersonaVoiceProfile", persona_id)

        profile = persona.voice_profile
        profile.status = VoiceProfileStatus.PROCESSING
        db.commit()

        sample_check = voice_quality_service.check_voice_samples(db, persona.target_id)
        profile.reference_audio_count = len(sample_check.reference_audio_paths)
        profile.reference_audio_paths_json = sample_check.reference_audio_paths
        profile.total_reference_duration_ms = sample_check.total_duration_ms
        profile.reference_audio_total_seconds = sample_check.total_duration_ms / 1000 if sample_check.total_duration_ms else None
        profile.noise_score = sample_check.noise_score
        profile.quality_score = sample_check.quality_score
        profile.similarity_score = sample_check.similarity_score

        if sample_check.error_message:
            profile.status = VoiceProfileStatus.NEEDS_MORE_SAMPLES
            profile.error_message = sample_check.error_message
            persona.is_voice_profile_created = False
        elif sample_check.quality_score < settings.VOICE_PROFILE_MIN_QUALITY_SCORE:
            profile.status = VoiceProfileStatus.NEEDS_MORE_SAMPLES
            profile.error_message = "Voice quality is below minimum threshold"
            persona.is_voice_profile_created = False
        else:
            generated = await get_voice_clone_service().create_voice_profile(
                persona_id=persona.id,
                reference_audio_paths=sample_check.reference_audio_paths,
            )
            profile.provider = generated.get("provider") or "mock"
            profile.model_name = generated.get("model_name")
            provider_status = generated.get("status") or VoiceProfileStatus.READY.value
            profile.status = VoiceProfileStatus(provider_status)
            profile.voice_profile_path = generated.get("voice_profile_path")
            profile.error_message = generated.get("error_message")
            profile.sample_audio_path = await voice_quality_service.generate_sample_output(
                persona_id=persona.id,
                voice_profile_payload={"persona_id": persona.id, "provider": profile.provider},
            )
            if profile.status != VoiceProfileStatus.FAILED:
                profile.status = VoiceProfileStatus.READY
            persona.is_voice_profile_created = profile.status == VoiceProfileStatus.READY

        profile.review_status = VoiceProfileReviewStatus.NOT_REVIEWED
        profile.reviewed_by = None
        profile.reviewed_at = None
        profile.review_note = None

        db.commit()
        db.refresh(profile)
        PersonaService._log_voice_profile_event(
            db,
            action=AuditAction.VOICE_PROFILE_REVIEWED,
            actor_user_id=user_id,
            profile_id=profile.id,
            description="Voice profile evaluated",
            metadata={"status": profile.status.value, "quality_score": profile.quality_score},
        )
        return profile

    @staticmethod
    def user_confirm_voice_profile(
        db: Session,
        persona_id: int,
        user_id: int,
        review_note: str | None = None,
    ) -> PersonaVoiceProfile:
        persona = PersonaService._get_owned_persona(db, persona_id, user_id)
        profile = persona.voice_profile
        if profile is None or profile.is_deleted:
            raise NotFoundException("PersonaVoiceProfile", persona_id)
        if profile.status != VoiceProfileStatus.READY:
            raise BadRequestException("Voice profile must be READY before confirmation")

        profile.review_status = VoiceProfileReviewStatus.USER_CONFIRMED
        profile.review_note = review_note
        profile.reviewed_at = PersonaService._now()
        db.commit()
        db.refresh(profile)
        PersonaService._log_voice_profile_event(
            db,
            action=AuditAction.VOICE_PROFILE_REVIEWED,
            actor_user_id=user_id,
            profile_id=profile.id,
            description="Voice profile confirmed by user",
            metadata={"review_status": profile.review_status.value},
        )
        return profile

    @staticmethod
    def admin_get_voice_profile(db: Session, voice_profile_id: int) -> PersonaVoiceProfile:
        return PersonaService._get_voice_profile_by_id(db, voice_profile_id)

    @staticmethod
    def admin_approve_voice_profile(
        db: Session,
        voice_profile_id: int,
        admin_user_id: int,
        review_note: str | None = None,
    ) -> PersonaVoiceProfile:
        profile = PersonaService._get_voice_profile_by_id(db, voice_profile_id)
        if profile.status != VoiceProfileStatus.READY:
            raise BadRequestException("Only READY voice profiles can be approved")
        profile.review_status = VoiceProfileReviewStatus.ADMIN_APPROVED
        profile.reviewed_by = admin_user_id
        profile.reviewed_at = PersonaService._now()
        profile.review_note = review_note
        db.commit()
        db.refresh(profile)
        PersonaService._log_voice_profile_event(
            db,
            action=AuditAction.VOICE_PROFILE_REVIEWED,
            actor_user_id=admin_user_id,
            profile_id=profile.id,
            description="Voice profile approved by admin",
            metadata={"review_status": profile.review_status.value},
        )
        return profile

    @staticmethod
    def admin_reject_voice_profile(
        db: Session,
        voice_profile_id: int,
        admin_user_id: int,
        review_note: str | None = None,
    ) -> PersonaVoiceProfile:
        profile = PersonaService._get_voice_profile_by_id(db, voice_profile_id)
        profile.review_status = VoiceProfileReviewStatus.REJECTED
        profile.status = VoiceProfileStatus.FAILED
        profile.reviewed_by = admin_user_id
        profile.reviewed_at = PersonaService._now()
        profile.review_note = review_note
        profile.error_message = review_note or "Rejected by admin review"
        if profile.persona is not None:
            profile.persona.is_voice_profile_created = False
        db.commit()
        db.refresh(profile)
        PersonaService._log_voice_profile_event(
            db,
            action=AuditAction.VOICE_PROFILE_REVIEWED,
            actor_user_id=admin_user_id,
            profile_id=profile.id,
            description="Voice profile rejected by admin",
            metadata={"review_status": profile.review_status.value},
        )
        return profile

    @staticmethod
    def admin_revoke_voice_profile(
        db: Session,
        voice_profile_id: int,
        admin_user_id: int,
        review_note: str | None = None,
    ) -> PersonaVoiceProfile:
        profile = PersonaService._get_voice_profile_by_id(db, voice_profile_id)
        profile.status = VoiceProfileStatus.REVOKED
        profile.review_status = VoiceProfileReviewStatus.REJECTED
        profile.reviewed_by = admin_user_id
        profile.reviewed_at = PersonaService._now()
        profile.review_note = review_note
        if profile.persona is not None:
            profile.persona.is_voice_profile_created = False
        db.commit()
        db.refresh(profile)
        PersonaService._log_voice_profile_event(
            db,
            action=AuditAction.VOICE_PROFILE_REVIEWED,
            actor_user_id=admin_user_id,
            profile_id=profile.id,
            description="Voice profile revoked by admin",
            metadata={"status": profile.status.value},
        )
        return profile

    @staticmethod
    def get_voice_profile(db: Session, persona_id: int, user_id: int) -> PersonaVoiceProfile:
        persona = PersonaService._get_owned_persona(db, persona_id, user_id)
        if persona.voice_profile is None or persona.voice_profile.is_deleted:
            raise NotFoundException("PersonaVoiceProfile", persona_id)
        return persona.voice_profile


persona_service = PersonaService()
