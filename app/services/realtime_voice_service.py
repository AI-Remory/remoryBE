"""Realtime voice chat websocket service helpers."""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.core.settings import settings
from app.models.audit_log import AuditAction, AuditTargetType
from app.models.chat import MessageType, PersonaChat, PersonaMessage, SenderType
from app.models.persona import Persona
from app.models.voice_call import VoiceCallSession, VoiceCallSessionStatus
from app.services.ai import get_llm_service
from app.services.audit_log_service import AuditLogService
from app.services.persona_service import persona_service
from app.services.rate_limit_service import RateLimitService
from app.services.speech import get_stt_service, get_tts_service, get_voice_clone_service
from app.services.user_service import user_service
from app.utils.exceptions import ForbiddenException, ValidationException


class RealtimeVoiceService:
    """Service methods for websocket realtime voice chat protocol."""

    _active_connections: dict[int, int] = {}
    _utterance_counters: dict[tuple[int, str], int] = {}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _minute_key() -> str:
        return datetime.now(UTC).strftime("%Y%m%d%H%M")

    @staticmethod
    def authenticate_token(token: str | None) -> int:
        if not token:
            raise ForbiddenException("Missing websocket token")
        payload = verify_token(token, expected_type="access")
        raw_sub = payload.get("sub")
        if raw_sub is None:
            raise ForbiddenException("Invalid websocket token")
        try:
            return int(raw_sub)
        except (TypeError, ValueError):
            raise ForbiddenException("Invalid websocket token")

    @classmethod
    def _increase_connection_count(cls, user_id: int) -> None:
        count = cls._active_connections.get(user_id, 0)
        if count >= getattr(settings, "VOICE_WS_MAX_ACTIVE_CONNECTIONS_PER_USER", 2):
            raise ValidationException("Too many active voice websocket connections")
        cls._active_connections[user_id] = count + 1

    @classmethod
    def _decrease_connection_count(cls, user_id: int) -> None:
        count = cls._active_connections.get(user_id, 0)
        if count <= 1:
            cls._active_connections.pop(user_id, None)
            return
        cls._active_connections[user_id] = count - 1

    @classmethod
    def _consume_utterance_budget(cls, user_id: int) -> None:
        key = (user_id, cls._minute_key())
        used = cls._utterance_counters.get(key, 0)
        max_per_minute = getattr(settings, "VOICE_WS_MAX_UTTERANCES_PER_MINUTE", 20)
        if used >= max_per_minute:
            raise ValidationException("Voice utterance rate limit exceeded")
        cls._utterance_counters[key] = used + 1

    @staticmethod
    def _audit_block(
        db: Session,
        user_id: int | None,
        action: AuditAction,
        target_type: AuditTargetType,
        target_id: int | None,
        description: str,
        metadata: dict | None = None,
    ) -> None:
        try:
            AuditLogService.create_audit_log(
                db=db,
                action=action,
                actor_user_id=user_id,
                target_type=target_type,
                target_id=target_id,
                description=description,
                metadata=metadata,
            )
        except Exception:
            pass

    @staticmethod
    def _build_input_path(user_id: int, mime_type: str | None) -> Path:
        ext = ".webm"
        if mime_type == "audio/wav":
            ext = ".wav"
        elif mime_type == "audio/mpeg":
            ext = ".mp3"
        elif mime_type == "audio/mp4":
            ext = ".m4a"
        base_dir = Path(settings.UPLOAD_DIR) / "voices" / "call_inputs" / str(user_id)
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex}{ext}"

    @staticmethod
    def _build_output_path(user_id: int) -> Path:
        base_dir = Path(settings.UPLOAD_DIR) / "voices" / "call_outputs" / str(user_id)
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex}.wav"

    @staticmethod
    def _resolve_chat(db: Session, user_id: int, persona_id: int, chat_id: int | None) -> PersonaChat:
        if chat_id is not None:
            chat = db.execute(
                select(PersonaChat).where(
                    PersonaChat.id == chat_id,
                    PersonaChat.user_id == user_id,
                    PersonaChat.persona_id == persona_id,
                    PersonaChat.deleted_at.is_(None),
                )
            ).scalar_one_or_none()
            if chat is None:
                raise ForbiddenException("Invalid chat_id for persona voice websocket")
            return chat

        chat = PersonaChat(user_id=user_id, persona_id=persona_id, title="Voice call")
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

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
                "sender_type": item.sender_type.value,
                "message_type": item.message_type.value,
                "content": item.content or "",
            }
            for item in reversed(messages)
        ]

    @staticmethod
    async def start_session(
        db: Session,
        websocket: WebSocket,
        user_id: int,
        persona_id: int,
        chat_id: int | None,
    ) -> dict:
        user_service.get_user_by_id(db, user_id)
        persona = persona_service.get_persona(db, persona_id, user_id)
        persona_service.ensure_voice_clone_usage_allowed(db, persona, user_id)

        allowed, reason = RateLimitService.check_voice_call_limit(db, user_id, 1)
        if not allowed:
            RateLimitService.record_rate_limit_event(
                db,
                user_id=user_id,
                ip_address=websocket.client.host if websocket.client else None,
                endpoint=f"/api/v1/ws/personas/{persona_id}/voice",
                event_type="voice_call",
                blocked=True,
                reason=reason,
                window_seconds=60,
            )
            RealtimeVoiceService._audit_block(
                db,
                user_id,
                AuditAction.RATE_LIMIT_BLOCKED,
                AuditTargetType.PERSONA,
                persona_id,
                reason or "Voice call limit exceeded",
                {"event_type": "voice_call"},
            )
            raise ValidationException(reason or "Voice call limit exceeded")

        chat = RealtimeVoiceService._resolve_chat(db, user_id, persona_id, chat_id)
        RealtimeVoiceService._increase_connection_count(user_id)

        session = VoiceCallSession(
            user_id=user_id,
            persona_id=persona_id,
            chat_id=chat.id,
            status=VoiceCallSessionStatus.CONNECTED,
            started_at=RealtimeVoiceService._now(),
            total_duration_seconds=0,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        try:
            AuditLogService.create_audit_log(
                db=db,
                action=AuditAction.VOICE_CALL_STARTED,
                actor_user_id=user_id,
                target_type=AuditTargetType.PERSONA,
                target_id=persona_id,
                description="Voice call session started",
                metadata={"voice_call_session_id": session.id, "chat_id": chat.id},
            )
        except Exception:
            pass

        return {
            "session": session,
            "persona": persona,
            "chat": chat,
            "audio_buffer": bytearray(),
            "chunk_count": 0,
            "mime_type": None,
        }

    @staticmethod
    def handle_audio_chunk(state: dict, chunk_b64: str, mime_type: str | None) -> None:
        try:
            raw = base64.b64decode(chunk_b64)
        except Exception:
            raise ValidationException("Invalid base64 audio chunk")

        max_chunk = getattr(settings, "VOICE_WS_MAX_CHUNK_BYTES", 262144)
        if len(raw) > max_chunk:
            raise ValidationException("Audio chunk too large")

        state["chunk_count"] += 1
        if state["chunk_count"] > getattr(settings, "VOICE_WS_MAX_CHUNKS_PER_UTTERANCE", 100):
            raise ValidationException("Too many audio chunks in one utterance")

        state["audio_buffer"].extend(raw)
        state["mime_type"] = mime_type or state.get("mime_type") or "audio/webm"

    @staticmethod
    async def process_utterance(db: Session, websocket: WebSocket, state: dict) -> dict:
        session: VoiceCallSession = state["session"]
        persona: Persona = state["persona"]
        chat: PersonaChat = state["chat"]
        user_id = session.user_id

        if not state["audio_buffer"]:
            raise ValidationException("No audio chunks received")

        RealtimeVoiceService._consume_utterance_budget(user_id)

        allowed_stt, stt_reason = RateLimitService.check_stt_limit(db, user_id)
        if not allowed_stt:
            RateLimitService.record_rate_limit_event(
                db,
                user_id=user_id,
                ip_address=websocket.client.host if websocket.client else None,
                endpoint=f"/api/v1/ws/personas/{persona.id}/voice",
                event_type="stt",
                blocked=True,
                reason=stt_reason,
                window_seconds=60,
            )
            RealtimeVoiceService._audit_block(
                db,
                user_id,
                AuditAction.RATE_LIMIT_BLOCKED,
                AuditTargetType.PERSONA,
                persona.id,
                stt_reason or "STT limit exceeded",
                {"event_type": "stt"},
            )
            raise ValidationException(stt_reason or "STT limit exceeded")

        allowed_voice, voice_reason = RateLimitService.check_voice_generation_limit(db, user_id)
        if not allowed_voice:
            RateLimitService.record_rate_limit_event(
                db,
                user_id=user_id,
                ip_address=websocket.client.host if websocket.client else None,
                endpoint=f"/api/v1/ws/personas/{persona.id}/voice",
                event_type="voice_generation",
                blocked=True,
                reason=voice_reason,
                window_seconds=60,
            )
            RealtimeVoiceService._audit_block(
                db,
                user_id,
                AuditAction.RATE_LIMIT_BLOCKED,
                AuditTargetType.PERSONA,
                persona.id,
                voice_reason or "Voice generation limit exceeded",
                {"event_type": "voice_generation"},
            )
            raise ValidationException(voice_reason or "Voice generation limit exceeded")

        allowed_persona_voice, persona_voice_reason = RateLimitService.check_persona_voice_generation_limit(db, persona.id)
        if not allowed_persona_voice:
            RateLimitService.record_rate_limit_event(
                db,
                user_id=user_id,
                ip_address=websocket.client.host if websocket.client else None,
                endpoint=f"/api/v1/ws/personas/{persona.id}/voice",
                event_type="voice_generation_persona",
                blocked=True,
                reason=persona_voice_reason,
                window_seconds=60,
            )
            RealtimeVoiceService._audit_block(
                db,
                user_id,
                AuditAction.RATE_LIMIT_BLOCKED,
                AuditTargetType.PERSONA,
                persona.id,
                persona_voice_reason or "Persona voice generation limit exceeded",
                {"event_type": "voice_generation_persona"},
            )
            raise ValidationException(persona_voice_reason or "Persona voice generation limit exceeded")

        input_path = RealtimeVoiceService._build_input_path(user_id, state.get("mime_type"))
        input_path.write_bytes(bytes(state["audio_buffer"]))

        try:
            stt_result = await get_stt_service().transcribe(str(input_path))
            transcript = stt_result.text.strip() or ""
        except Exception as exc:
            raise ValidationException(f"STT failed: {str(exc)}")

        user_message = PersonaMessage(
            chat_id=chat.id,
            sender_type=SenderType.USER,
            message_type=MessageType.AUDIO,
            content=transcript,
            audio_file_path=str(input_path).replace("\\", "/"),
            is_ai_generated=False,
        )
        db.add(user_message)
        db.flush()

        try:
            reply_text = await get_llm_service().generate_persona_reply(
                persona={
                    "persona_name": persona.persona_name,
                    "speaking_style": persona.speaking_style,
                    "personality_summary": persona.personality_summary,
                    "memory_summary": persona.memory_summary,
                    "system_prompt": persona.system_prompt,
                },
                recent_messages=RealtimeVoiceService._recent_messages(db, chat.id),
                user_message=transcript,
            )
        except Exception:
            reply_text = "지금은 음성 응답을 생성하기 어려워요. 잠시 후 다시 시도해 주세요."

        output_path = RealtimeVoiceService._build_output_path(user_id)
        audio_file_path: str | None = None
        audio_url: str | None = None
        profile = None

        try:
            profile = persona_service.ensure_voice_clone_usage_allowed(db, persona, user_id)
            cloned = await get_voice_clone_service().synthesize_with_cloned_voice(
                reply_text,
                {
                    "persona_id": persona.id,
                    "provider": profile.provider or "mock",
                    "model_name": profile.model_name,
                    "voice_profile_path": profile.voice_profile_path,
                },
                str(output_path),
            )
            audio_file_path = cloned.audio_file_path.replace("\\", "/")
            audio_url = f"/{audio_file_path.lstrip('./')}"
            try:
                AuditLogService.create_audit_log(
                    db=db,
                    action=AuditAction.VOICE_SYNTHESIZED,
                    actor_user_id=user_id,
                    target_type=AuditTargetType.VOICE_PROFILE,
                    target_id=profile.id,
                    description="Voice synthesized in realtime websocket",
                    metadata={"voice_call_session_id": session.id},
                )
            except Exception:
                pass
        except Exception as exc:
            provider = (profile.provider if profile else "").lower() if profile else ""
            if provider == "openvoice" and not settings.OPENVOICE_FAILOVER_TO_MOCK:
                raise ValidationException(f"Voice synthesis failed: {str(exc)[:500]}")
            try:
                tts_result = await get_tts_service().synthesize(reply_text, str(output_path))
                audio_file_path = tts_result.audio_file_path.replace("\\", "/")
                audio_url = f"/{audio_file_path.lstrip('./')}"
            except Exception:
                audio_file_path = None
                audio_url = None

        persona_message = PersonaMessage(
            chat_id=chat.id,
            sender_type=SenderType.PERSONA,
            message_type=MessageType.AUDIO,
            content=reply_text,
            audio_file_path=audio_file_path,
            is_ai_generated=True,
        )
        db.add(persona_message)

        session.status = VoiceCallSessionStatus.ACTIVE
        db.commit()

        RateLimitService.increment_stt(db, user_id)
        if audio_file_path:
            RateLimitService.increment_voice_generation(db, user_id, persona.id)

        state["audio_buffer"] = bytearray()
        state["chunk_count"] = 0

        return {
            "final_transcript": transcript,
            "persona_text": reply_text,
            "audio_url": audio_url,
            "audio_file_path": audio_file_path,
        }

    @staticmethod
    def fail_session(db: Session, session: VoiceCallSession | None, message: str) -> None:
        if session is None:
            return
        session.status = VoiceCallSessionStatus.FAILED
        session.error_message = message[:512]
        session.ended_at = RealtimeVoiceService._now()
        session.total_duration_seconds = max(0, int((session.ended_at - session.started_at).total_seconds()))
        db.commit()

    @staticmethod
    def end_session(db: Session, websocket: WebSocket, state: dict | None) -> None:
        if not state:
            return
        session: VoiceCallSession = state.get("session")
        if session is None:
            return

        ended_at = RealtimeVoiceService._now()
        duration_seconds = max(0, int((ended_at - session.started_at).total_seconds()))
        session.ended_at = ended_at
        if session.status != VoiceCallSessionStatus.FAILED:
            session.status = VoiceCallSessionStatus.ENDED
        session.total_duration_seconds = duration_seconds
        db.commit()

        allowed, reason = RateLimitService.check_voice_call_limit(db, session.user_id, duration_seconds)
        if allowed:
            RateLimitService.increment_voice_call(db, session.user_id, session.persona_id, duration_seconds)
        else:
            RateLimitService.record_rate_limit_event(
                db,
                user_id=session.user_id,
                ip_address=websocket.client.host if websocket.client else None,
                endpoint=f"/api/v1/ws/personas/{session.persona_id}/voice",
                event_type="voice_call_duration",
                blocked=True,
                reason=reason,
                window_seconds=60,
            )
            RealtimeVoiceService._audit_block(
                db,
                session.user_id,
                AuditAction.RATE_LIMIT_BLOCKED,
                AuditTargetType.PERSONA,
                session.persona_id,
                reason or "Voice call duration limit exceeded",
                {"event_type": "voice_call_duration"},
            )

        try:
            AuditLogService.create_audit_log(
                db=db,
                action=AuditAction.VOICE_CALL_ENDED,
                actor_user_id=session.user_id,
                target_type=AuditTargetType.PERSONA,
                target_id=session.persona_id,
                description="Voice call session ended",
                metadata={
                    "voice_call_session_id": session.id,
                    "duration_seconds": duration_seconds,
                    "status": session.status.value,
                },
            )
        except Exception:
            pass

        RealtimeVoiceService._decrease_connection_count(session.user_id)


realtime_voice_service = RealtimeVoiceService()

