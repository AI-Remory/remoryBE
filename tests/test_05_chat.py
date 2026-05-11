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
