"""Persona business logic."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.media import MediaType, TargetMedia
from app.models.persona import Persona, PersonaStatus, PersonaVoiceProfile
from app.models.target import Target
from app.services.ai_service import ai_service
from app.services.consent_service import consent_service
from app.models.consent import ConsentType
from app.utils.exceptions import ForbiddenException, NotFoundException


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
    async def create_persona(db: Session, target_id: int, user_id: int) -> Persona:
        target = PersonaService._get_owned_target(db, target_id, user_id)

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


persona_service = PersonaService()
