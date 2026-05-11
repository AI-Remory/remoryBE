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
