"""Realtime voice chat WebSocket API."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.audit_log_service import AuditLogService
from app.models.audit_log import AuditAction, AuditTargetType
from app.services.persona_service import persona_service
from app.services.realtime_voice_service import realtime_voice_service
from app.utils.exceptions import RemoryException

router = APIRouter(tags=["realtime-voice"])


async def _send_error(websocket: WebSocket, message: str) -> None:
    await websocket.send_json({"type": "error", "message": message})


def _audit_abnormal_request(db: Session, user_id: int | None, persona_id: int, message: str) -> None:
    try:
        AuditLogService.create_audit_log(
            db=db,
            action=AuditAction.ABNORMAL_REQUEST_BLOCKED,
            actor_user_id=user_id,
            target_type=AuditTargetType.PERSONA,
            target_id=persona_id,
            description=message,
            metadata={"endpoint": f"/api/v1/ws/personas/{persona_id}/voice"},
        )
    except Exception:
        pass


@router.websocket("/ws/personas/{persona_id}/voice")
async def persona_voice_websocket(
    websocket: WebSocket,
    persona_id: int,
    db: Session = Depends(get_db),
):
    """Chunked realtime voice conversation over Remory-owned WebSocket."""

    user_id: int | None = None
    state: dict | None = None

    try:
        user_id = realtime_voice_service.authenticate_token(websocket.query_params.get("token"))
        persona_service.get_persona(db, persona_id, user_id)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")

            if message_type == "start":
                if state is not None:
                    await _send_error(websocket, "Voice call session already started")
                    continue

                try:
                    state = await realtime_voice_service.start_session(
                        db=db,
                        websocket=websocket,
                        user_id=user_id,
                        persona_id=persona_id,
                        chat_id=message.get("chat_id"),
                    )
                    await websocket.send_json(
                        {
                            "type": "session_started",
                            "session_id": state["session"].id,
                        }
                    )
                except RemoryException as exc:
                    await _send_error(websocket, exc.message)
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    break
                except Exception:
                    await _send_error(websocket, "Failed to start voice call session")
                    await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                    break

            elif message_type == "audio_chunk":
                if state is None:
                    _audit_abnormal_request(db, user_id, persona_id, "audio_chunk sent before start")
                    await _send_error(websocket, "Voice call session has not started")
                    continue

                try:
                    realtime_voice_service.handle_audio_chunk(
                        state=state,
                        chunk_b64=message.get("data") or "",
                        mime_type=message.get("mime_type"),
                    )
                except RemoryException as exc:
                    _audit_abnormal_request(db, user_id, persona_id, exc.message)
                    await _send_error(websocket, exc.message)

            elif message_type == "end_utterance":
                if state is None:
                    _audit_abnormal_request(db, user_id, persona_id, "end_utterance sent before start")
                    await _send_error(websocket, "Voice call session has not started")
                    continue

                try:
                    result = await realtime_voice_service.process_utterance(db, websocket, state)
                    await websocket.send_json(
                        {"type": "final_transcript", "text": result["final_transcript"]}
                    )
                    await websocket.send_json({"type": "persona_text", "text": result["persona_text"]})
                    await websocket.send_json(
                        {
                            "type": "persona_audio",
                            "audio_url": result["audio_url"],
                            "audio_file_path": result["audio_file_path"],
                        }
                    )
                except RemoryException as exc:
                    await _send_error(websocket, exc.message)
                except Exception:
                    await _send_error(websocket, "Failed to process utterance")

            elif message_type == "stop":
                realtime_voice_service.end_session(db, websocket, state)
                state = None
                await websocket.send_json({"type": "session_ended"})
                await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
                break

            else:
                _audit_abnormal_request(db, user_id, persona_id, f"Unknown voice websocket message: {message_type}")
                await _send_error(websocket, "Unknown message type")

    except WebSocketDisconnect:
        realtime_voice_service.end_session(db, websocket, state)
        state = None
    except Exception:
        if state is not None:
            realtime_voice_service.fail_session(db, state.get("session"), "Unexpected websocket failure")
            realtime_voice_service.end_session(db, websocket, state)
            state = None
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
    finally:
        realtime_voice_service.end_session(db, websocket, state)
