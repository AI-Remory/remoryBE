"""Persona business logic."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.media import MediaType, TargetMedia
from app.models.persona import Persona, PersonaStatus, PersonaVoiceProfile, VoiceProfileStatus
from app.models.target import Target
from app.services.ai_service import ai_service
from app.services.consent_service import consent_service
from app.services.speech import get_voice_clone_service
from app.services.verification_service import verification_service
from app.models.consent import ConsentType
from app.utils.exceptions import ForbiddenException, NotFoundException, RemoryException


class PersonaService:
    """Persona creation and lookup service."""

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
        # TODO: Enforce once policy work lands:
        # - TargetVerificationRequest status must be APPROVED for this target.
        # - ConsentLog must include explicit VOICE_CLONING consent.
        # Current MVP keeps the checkpoint here without blocking existing flows.
        return None

    @staticmethod
    async def create_persona(db: Session, target_id: int, user_id: int) -> Persona:
        target = PersonaService._get_owned_target(db, target_id, user_id)

        # Check target verification approval
        verification = verification_service.get_approved_verification_for_target(db, target_id)
        if verification is None:
            raise ForbiddenException("Target verification approval is required before creating persona.")

        image_count = PersonaService._count_media(db, target_id, MediaType.IMAGE)
        voice_count = PersonaService._count_media(db, target_id, MediaType.VOICE)

        consent_service.check_consent(db, user_id, target_id, ConsentType.PERSONA_CREATION)
        if image_count > 0:
            consent_service.check_consent(db, user_id, target_id, ConsentType.PHOTO_COLLECTION)
        if voice_count > 0:
            consent_service.check_consent(db, user_id, target_id, ConsentType.VOICE_COLLECTION)

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
            persona.is_voice_profile_created = True
            if persona.voice_profile is None:
                persona.voice_profile = PersonaVoiceProfile()

            persona.voice_profile.reference_voice_file_path = representative_voice.file_path
            persona.voice_profile.reference_voice_mime_type = representative_voice.mime_type
            persona.voice_profile.reference_voice_duration = representative_voice.duration_seconds
            persona.voice_profile.target_id = target_id
            persona.voice_profile.provider = "mock"
            persona.voice_profile.status = VoiceProfileStatus.READY
            persona.voice_profile.reference_audio_count = voice_count
            persona.voice_profile.reference_audio_total_seconds = representative_voice.duration_seconds
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

        voice_media = PersonaService._get_voice_media(db, persona.target_id)
        if not voice_media:
            raise RemoryException("Reference voice audio is required", "REFERENCE_AUDIO_REQUIRED")

        reference_audio_paths = [media.file_path for media in voice_media]
        generated = await get_voice_clone_service().create_voice_profile(
            persona_id=persona.id,
            reference_audio_paths=reference_audio_paths,
        )

        if persona.voice_profile is None:
            persona.voice_profile = PersonaVoiceProfile(persona_id=persona.id)

        profile = persona.voice_profile
        profile.target_id = persona.target_id
        profile.provider = generated.get("provider") or "mock"
        profile.model_name = generated.get("model_name")
        status_value = generated.get("status") or VoiceProfileStatus.PENDING.value
        profile.status = VoiceProfileStatus(status_value)
        profile.reference_audio_count = generated.get("reference_audio_count") or len(reference_audio_paths)
        profile.reference_audio_total_seconds = generated.get("reference_audio_total_seconds")
        profile.voice_profile_path = generated.get("voice_profile_path")
        profile.sample_audio_path = generated.get("sample_audio_path")
        profile.error_message = generated.get("error_message")

        representative_voice = voice_media[0]
        profile.reference_voice_file_path = representative_voice.file_path
        profile.reference_voice_mime_type = representative_voice.mime_type
        profile.reference_voice_duration = representative_voice.duration_seconds
        profile.voice_provider = profile.provider
        profile.profile_metadata = {
            "reference_audio_paths": reference_audio_paths,
            "voice_media_count": len(voice_media),
        }
        profile.is_deleted = False
        persona.is_voice_profile_created = profile.status == VoiceProfileStatus.READY

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_voice_profile(db: Session, persona_id: int, user_id: int) -> PersonaVoiceProfile:
        persona = PersonaService._get_owned_persona(db, persona_id, user_id)
        if persona.voice_profile is None or persona.voice_profile.is_deleted:
            raise NotFoundException("PersonaVoiceProfile", persona_id)
        return persona.voice_profile


persona_service = PersonaService()
