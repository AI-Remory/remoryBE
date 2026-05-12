class CapturingLLMService:
    def __init__(self):
        self.calls = []

    async def generate_persona_reply(self, persona, recent_messages, user_message):
        self.calls.append(
            {
                "persona": persona,
                "recent_messages": recent_messages,
                "user_message": user_message,
            }
        )
        return "Captured persona reply"


def _prepare_confirmed_voice_profile(client, auth_headers, persona_id):
    create_response = client.post(f"/api/v1/personas/{persona_id}/voice-profile", headers=auth_headers)
    assert create_response.status_code == 201
    evaluate_response = client.post(f"/api/v1/personas/{persona_id}/voice-profile/evaluate", headers=auth_headers)
    assert evaluate_response.status_code == 200
    confirm_response = client.patch(
        f"/api/v1/personas/{persona_id}/voice-profile/user-confirm",
        headers=auth_headers,
        json={"review_note": "sounds good"},
    )
    assert confirm_response.status_code == 200


def test_create_chat(client, auth_headers, created_chat):
    response = client.get(f"/api/v1/personas/{created_chat['persona_id']}/chats", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == created_chat["id"]


def test_send_persona_message(client, auth_headers, created_chat):
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/messages",
        json={"message_type": "TEXT", "content": "Tell me about this memory."},
        headers=auth_headers,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["user_message"]["sender_type"] == "USER"
    assert payload["persona_message"]["sender_type"] == "PERSONA"
    assert payload["persona_message"]["is_ai_generated"] is True


def test_send_persona_message_can_generate_audio(client, auth_headers, created_chat):
    _prepare_confirmed_voice_profile(client, auth_headers, created_chat["persona_id"])
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/messages",
        json={
            "message_type": "TEXT",
            "content": "Tell me about this memory.",
            "generate_audio": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["persona_message"]["sender_type"] == "PERSONA"
    assert payload["persona_message"]["message_type"] == "TEXT"
    assert payload["persona_message"]["audio_file_path"]
    assert "uploads" in payload["persona_message"]["audio_file_path"]
    assert payload["persona_message"]["is_ai_generated"] is True


def test_send_persona_message_passes_context_to_llm(client, auth_headers, created_chat, monkeypatch):
    llm_service = CapturingLLMService()
    monkeypatch.setattr("app.services.chat_service.get_llm_service", lambda: llm_service)

    first_response = client.post(
        f"/api/v1/chats/{created_chat['id']}/messages",
        json={"message_type": "TEXT", "content": "First message"},
        headers=auth_headers,
    )
    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/v1/chats/{created_chat['id']}/messages",
        json={"message_type": "TEXT", "content": "Second message"},
        headers=auth_headers,
    )
    assert second_response.status_code == 201

    second_call = llm_service.calls[-1]
    assert second_call["user_message"] == "Second message"
    assert second_call["persona"]["persona_name"]
    assert "speaking_style" in second_call["persona"]
    assert "personality_summary" in second_call["persona"]
    assert "memory_summary" in second_call["persona"]
    assert "system_prompt" in second_call["persona"]
    assert [item["sender_type"] for item in second_call["recent_messages"]] == ["USER", "PERSONA"]
    assert second_call["recent_messages"][0]["content"] == "First message"


def test_send_persona_audio_message_uses_stt_and_creates_reply(client, auth_headers, created_chat):
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/audio",
        files={"file": ("voice.wav", b"fake audio content", "audio/wav")},
        headers=auth_headers,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["user_message"]["sender_type"] == "USER"
    assert payload["user_message"]["message_type"] == "AUDIO"
    assert payload["user_message"]["content"] == "테스트용 음성 변환 결과입니다."
    assert payload["user_message"]["audio_file_path"]
    assert "uploads" in payload["user_message"]["audio_file_path"]
    assert payload["persona_message"]["sender_type"] == "PERSONA"
    assert payload["persona_message"]["message_type"] == "TEXT"
    assert payload["persona_message"]["audio_file_path"] is None
    assert payload["persona_message"]["is_ai_generated"] is True


def test_send_persona_audio_message_can_generate_audio_reply(client, auth_headers, created_chat):
    _prepare_confirmed_voice_profile(client, auth_headers, created_chat["persona_id"])
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/audio",
        data={"generate_audio": "true"},
        files={"file": ("voice.wav", b"fake audio content", "audio/wav")},
        headers=auth_headers,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["user_message"]["message_type"] == "AUDIO"
    assert payload["persona_message"]["message_type"] == "TEXT"
    assert payload["persona_message"]["audio_file_path"]
    assert "uploads" in payload["persona_message"]["audio_file_path"]


def test_send_persona_audio_message_rejects_non_audio_mime(client, auth_headers, created_chat):
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/audio",
        files={"file": ("voice.txt", b"not audio", "text/plain")},
        headers=auth_headers,
    )

    assert response.status_code == 400


def test_other_user_cannot_send_persona_audio_message(client, created_chat, second_user_headers):
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/audio",
        files={"file": ("voice.wav", b"fake audio content", "audio/wav")},
        headers=second_user_headers,
    )

    assert response.status_code in (403, 404)


def test_list_chat_messages(client, auth_headers, created_chat):
    client.post(
        f"/api/v1/chats/{created_chat['id']}/messages",
        json={"message_type": "TEXT", "content": "Hello"},
        headers=auth_headers,
    )
    response = client.get(f"/api/v1/chats/{created_chat['id']}/messages", headers=auth_headers)
    assert response.status_code == 200
    assert [item["sender_type"] for item in response.json()] == ["USER", "PERSONA"]


def test_other_user_cannot_access_chat(client, created_chat, second_user_headers):
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/messages",
        json={"message_type": "TEXT", "content": "Blocked"},
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)
