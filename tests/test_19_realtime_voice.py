import base64

import pytest
from starlette.websockets import WebSocketDisconnect

from app.models.chat import PersonaMessage, SenderType
from app.models.usage_limit import UsageLimit
from app.services.rate_limit_service import RateLimitService
from tests.conftest import TestingSessionLocal


def _prepare_confirmed_voice_profile(client, auth_headers, persona_id):
    create_response = client.post(f"/api/v1/personas/{persona_id}/voice-profile", headers=auth_headers)
    assert create_response.status_code == 201
    evaluate_response = client.post(f"/api/v1/personas/{persona_id}/voice-profile/evaluate", headers=auth_headers)
    assert evaluate_response.status_code == 200
    confirm_response = client.patch(
        f"/api/v1/personas/{persona_id}/voice-profile/user-confirm",
        headers=auth_headers,
        json={"review_note": "ready for calls"},
    )
    assert confirm_response.status_code == 200


def _voice_ws_url(persona_id, token):
    return f"/api/v1/ws/personas/{persona_id}/voice?token={token}"


def test_voice_websocket_auth_failure(client, created_persona):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(_voice_ws_url(created_persona["id"], "bad-token")):
            pass


def test_voice_websocket_other_user_persona_access_failure(client, created_persona, second_user):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(_voice_ws_url(created_persona["id"], second_user["access_token"])):
            pass


def test_voice_websocket_start_success(client, auth_token, auth_headers, created_chat):
    _prepare_confirmed_voice_profile(client, auth_headers, created_chat["persona_id"])

    with client.websocket_connect(_voice_ws_url(created_chat["persona_id"], auth_token)) as websocket:
        websocket.send_json({"type": "start", "chat_id": created_chat["id"]})
        assert websocket.receive_json()["type"] == "session_started"
        websocket.send_json({"type": "stop"})
        assert websocket.receive_json()["type"] == "session_ended"


def test_voice_websocket_audio_chunk_end_utterance_stop_success(
    client,
    auth_token,
    auth_headers,
    created_chat,
):
    _prepare_confirmed_voice_profile(client, auth_headers, created_chat["persona_id"])
    audio_b64 = base64.b64encode(b"fake audio content").decode("ascii")

    with client.websocket_connect(_voice_ws_url(created_chat["persona_id"], auth_token)) as websocket:
        websocket.send_json({"type": "start", "chat_id": created_chat["id"]})
        assert websocket.receive_json()["type"] == "session_started"

        websocket.send_json({"type": "audio_chunk", "data": audio_b64, "mime_type": "audio/webm"})
        websocket.send_json({"type": "end_utterance"})

        final_transcript = websocket.receive_json()
        persona_text = websocket.receive_json()
        persona_audio = websocket.receive_json()

        assert final_transcript["type"] == "final_transcript"
        assert final_transcript["text"]
        assert persona_text["type"] == "persona_text"
        assert persona_text["text"]
        assert persona_audio["type"] == "persona_audio"
        assert persona_audio["audio_url"]
        assert persona_audio["audio_file_path"]

        websocket.send_json({"type": "stop"})
        assert websocket.receive_json()["type"] == "session_ended"

    db = TestingSessionLocal()
    try:
        messages = (
            db.query(PersonaMessage)
            .filter(PersonaMessage.chat_id == created_chat["id"])
            .order_by(PersonaMessage.id.asc())
            .all()
        )
        user_message = next(message for message in messages if message.sender_type == SenderType.USER)
        persona_message = next(message for message in messages if message.sender_type == SenderType.PERSONA)

        assert user_message.content == final_transcript["text"]
        assert user_message.audio_file_path
        assert persona_message.content == persona_text["text"]
        assert persona_message.audio_file_path == persona_audio["audio_file_path"]
        assert persona_message.is_ai_generated is True
    finally:
        db.close()


def test_voice_websocket_voice_profile_ready_required(client, auth_token, created_chat):
    with client.websocket_connect(_voice_ws_url(created_chat["persona_id"], auth_token)) as websocket:
        websocket.send_json({"type": "start", "chat_id": created_chat["id"]})
        message = websocket.receive_json()
        assert message["type"] == "error"
        assert "Voice profile" in message["message"]


def test_voice_websocket_voice_cloning_consent_required(
    client,
    auth_token,
    auth_headers,
    created_chat,
    target_persona_consent,
):
    _prepare_confirmed_voice_profile(client, auth_headers, created_chat["persona_id"])
    revoke_response = client.patch(
        f"/api/v1/consents/{target_persona_consent['voice_cloning']['id']}/revoke",
        headers=auth_headers,
    )
    assert revoke_response.status_code == 200

    with client.websocket_connect(_voice_ws_url(created_chat["persona_id"], auth_token)) as websocket:
        websocket.send_json({"type": "start", "chat_id": created_chat["id"]})
        message = websocket.receive_json()
        assert message["type"] == "error"
        assert "voice_cloning_consent" in message["message"]


def test_voice_websocket_rate_limit_exceeded(client, auth_token, auth_headers, created_chat):
    _prepare_confirmed_voice_profile(client, auth_headers, created_chat["persona_id"])

    db = TestingSessionLocal()
    try:
        user_id = client.get("/api/v1/auth/me", headers=auth_headers).json()["id"]
        usage_limit = RateLimitService.get_user_usage_limit(db, user_id)
        usage_limit.voice_call_seconds_limit = 0
        db.commit()
    finally:
        db.close()

    with client.websocket_connect(_voice_ws_url(created_chat["persona_id"], auth_token)) as websocket:
        websocket.send_json({"type": "start", "chat_id": created_chat["id"]})
        message = websocket.receive_json()
        assert message["type"] == "error"
        assert "voice call" in message["message"].lower()
