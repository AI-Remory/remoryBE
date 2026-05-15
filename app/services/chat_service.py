"""Persona chat business logic."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditAction, AuditTargetType
from app.models.chat import MessageType, PersonaChat, PersonaMessage, SenderType
from app.models.persona import Persona, PersonaStatus
from app.models.target import Target
from app.schemas.chat import PersonaChatCreateRequest, PersonaMessageCreateRequest
from app.services.ai import get_llm_service
from app.services.audit_log_service import AuditLogService
from app.services.persona_service import PersonaService
from app.services.speech import get_stt_service, get_voice_clone_service
from app.utils.constants import MAX_UPLOAD_SIZE, UPLOAD_DIR
from app.utils.exceptions import FileUploadException, ForbiddenException, NotFoundException, ValidationException


class ChatService:
    """Persona chat and message service."""

    @staticmethod
    def _get_owned_persona(db: Session, persona_id: int, user_id: int) -> Persona:
        persona = db.execute(
            select(Persona)
            .join(Target, Target.id == Persona.target_id)
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
    def _get_owned_chat(db: Session, chat_id: int, user_id: int) -> PersonaChat:
        chat = db.execute(
            select(PersonaChat)
            .options(joinedload(PersonaChat.persona))
            .where(
                PersonaChat.id == chat_id,
                PersonaChat.deleted_at.is_(None),
            )
        ).scalar_one_or_none()

        if not chat:
            raise NotFoundException("PersonaChat", chat_id)
        if chat.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this chat")
        return chat

    @staticmethod
    def create_chat(
        db: Session,
        user_id: int,
        persona_id: int,
        chat_data: PersonaChatCreateRequest,
    ) -> PersonaChat:
        ChatService._get_owned_persona(db, persona_id, user_id)

        chat = PersonaChat(
            user_id=user_id,
            persona_id=persona_id,
            title=chat_data.title,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

    @staticmethod
    def list_chats(db: Session, user_id: int, persona_id: int) -> list[PersonaChat]:
        ChatService._get_owned_persona(db, persona_id, user_id)

        return db.execute(
            select(PersonaChat)
            .where(
                PersonaChat.user_id == user_id,
                PersonaChat.persona_id == persona_id,
                PersonaChat.deleted_at.is_(None),
            )
            .order_by(PersonaChat.created_at.desc(), PersonaChat.id.desc())
        ).scalars().all()

    @staticmethod
    def _build_persona_profile(persona: Persona) -> dict:
        return {
            "persona_name": persona.persona_name,
            "speaking_style": persona.speaking_style,
            "personality_summary": persona.personality_summary,
            "memory_summary": persona.memory_summary,
            "system_prompt": persona.system_prompt,
        }

    @staticmethod
    def _recent_messages(db: Session, chat_id: int, limit: int = 10) -> list[dict]:
        messages = (
            db.execute(
                select(PersonaMessage)
                .where(
                    PersonaMessage.chat_id == chat_id,
                    PersonaMessage.deleted_at.is_(None),
                )
                .order_by(PersonaMessage.created_at.desc(), PersonaMessage.id.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            {
                "sender_type": message.sender_type.value,
                "message_type": message.message_type.value,
                "content": message.content or "",
            }
            for message in reversed(messages)
        ]

    @staticmethod
    def _validate_message_request(message_data: PersonaMessageCreateRequest) -> None:
        if message_data.message_type == MessageType.TEXT and not message_data.content:
            raise ValidationException("Text messages require content")
        if message_data.message_type == MessageType.AUDIO and not message_data.audio_file_path:
            raise ValidationException("Audio messages require audio_file_path")

    @staticmethod
    async def _save_chat_audio_file(user_id: int, upload_file: UploadFile) -> str:
        if not upload_file.content_type or not upload_file.content_type.startswith("audio/"):
            raise FileUploadException("Invalid audio MIME type")

        contents = await upload_file.read()
        if len(contents) > MAX_UPLOAD_SIZE:
            raise FileUploadException(f"File size exceeds maximum limit ({MAX_UPLOAD_SIZE} bytes)")

        original_name = Path(upload_file.filename or "audio").name
        file_ext = Path(original_name).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uuid4().hex}{file_ext}"
        upload_dir = Path(UPLOAD_DIR) / "chat_audio" / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        file_path.write_bytes(contents)
        return str(file_path)

    @staticmethod
    async def _synthesize_persona_audio(db: Session, user_id: int, persona: Persona, reply_text: str) -> str:
        profile = PersonaService.ensure_voice_clone_usage_allowed(db, persona, user_id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uuid4().hex}.wav"
        output_dir = Path(UPLOAD_DIR) / "chat_tts" / str(user_id)
        output_path = output_dir / filename
        result = await get_voice_clone_service().synthesize_with_cloned_voice(
            reply_text,
            {
                "persona_id": persona.id,
                "provider": profile.provider or "mock",
                "model_name": profile.model_name,
                "voice_profile_path": profile.voice_profile_path,
            },
            str(output_path),
        )
        try:
            AuditLogService.create_audit_log(
                db=db,
                action=AuditAction.VOICE_SYNTHESIZED,
                actor_user_id=user_id,
                target_type=AuditTargetType.VOICE_PROFILE,
                target_id=profile.id,
                description="Persona voice response synthesized",
                metadata={"persona_id": persona.id, "chat_user_id": user_id},
            )
        except Exception:
            pass
        return result.audio_file_path

    @staticmethod
    async def _generate_persona_reply(
        persona: Persona,
        recent_messages: list[dict],
        user_message_text: str,
    ) -> str:
        return await get_llm_service().generate_persona_reply(
            persona=ChatService._build_persona_profile(persona),
            recent_messages=recent_messages,
            user_message=user_message_text,
        )

    @staticmethod
    async def create_message_pair(
        db: Session,
        user_id: int,
        chat_id: int,
        message_data: PersonaMessageCreateRequest,
    ) -> tuple[PersonaMessage, PersonaMessage]:
        ChatService._validate_message_request(message_data)
        chat = ChatService._get_owned_chat(db, chat_id, user_id)
        persona = chat.persona

        if persona.status != PersonaStatus.READY:
            raise ValidationException("Persona is not ready")

        recent_messages = ChatService._recent_messages(db, chat_id)
        user_message = PersonaMessage(
            chat_id=chat_id,
            sender_type=SenderType.USER,
            message_type=message_data.message_type,
            content=message_data.content,
            audio_file_path=message_data.audio_file_path,
            is_ai_generated=False,
        )
        db.add(user_message)
        db.flush()

        reply_content = await ChatService._generate_persona_reply(
            persona=persona,
            recent_messages=recent_messages,
            user_message_text=message_data.content or "",
        )
        persona_message = PersonaMessage(
            chat_id=chat_id,
            sender_type=SenderType.PERSONA,
            message_type=MessageType.TEXT,
            content=reply_content,
            audio_file_path=(
                await ChatService._synthesize_persona_audio(db, user_id, persona, reply_content)
                if message_data.generate_audio
                else None
            ),
            is_ai_generated=True,
        )
        db.add(persona_message)
        db.commit()
        db.refresh(user_message)
        db.refresh(persona_message)
        return user_message, persona_message

    @staticmethod
    async def create_audio_message_pair(
        db: Session,
        user_id: int,
        chat_id: int,
        upload_file: UploadFile,
        generate_audio: bool = False,
    ) -> tuple[PersonaMessage, PersonaMessage]:
        chat = ChatService._get_owned_chat(db, chat_id, user_id)
        persona = chat.persona

        if persona.status != PersonaStatus.READY:
            raise ValidationException("Persona is not ready")

        recent_messages = ChatService._recent_messages(db, chat_id)
        audio_file_path = await ChatService._save_chat_audio_file(user_id, upload_file)
        stt_result = await get_stt_service().transcribe(audio_file_path)

        user_message = PersonaMessage(
            chat_id=chat_id,
            sender_type=SenderType.USER,
            message_type=MessageType.AUDIO,
            content=stt_result.text,
            audio_file_path=audio_file_path,
            is_ai_generated=False,
        )
        db.add(user_message)
        db.flush()

        reply_content = await ChatService._generate_persona_reply(
            persona=persona,
            recent_messages=recent_messages,
            user_message_text=stt_result.text,
        )
        persona_message = PersonaMessage(
            chat_id=chat_id,
            sender_type=SenderType.PERSONA,
            message_type=MessageType.TEXT,
            content=reply_content,
            audio_file_path=(
                await ChatService._synthesize_persona_audio(db, user_id, persona, reply_content)
                if generate_audio
                else None
            ),
            is_ai_generated=True,
        )
        db.add(persona_message)
        db.commit()
        db.refresh(user_message)
        db.refresh(persona_message)
        return user_message, persona_message

    @staticmethod
    def list_messages(db: Session, user_id: int, chat_id: int) -> list[PersonaMessage]:
        ChatService._get_owned_chat(db, chat_id, user_id)

        return db.execute(
            select(PersonaMessage)
            .where(
                PersonaMessage.chat_id == chat_id,
                PersonaMessage.deleted_at.is_(None),
            )
            .order_by(PersonaMessage.created_at.asc(), PersonaMessage.id.asc())
        ).scalars().all()

    @staticmethod
    def get_message_audio(db: Session, user_id: int, chat_id: int, message_id: int) -> PersonaMessage:
        ChatService._get_owned_chat(db, chat_id, user_id)
        message = db.execute(
            select(PersonaMessage).where(
                PersonaMessage.id == message_id,
                PersonaMessage.chat_id == chat_id,
                PersonaMessage.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if not message:
            raise NotFoundException("PersonaMessage", message_id)
        if not message.audio_file_path:
            raise NotFoundException("PersonaMessage audio", message_id)
        return message


chat_service = ChatService()
