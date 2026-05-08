"""API 테스트"""
from pathlib import Path
import pytest


def test_health_check(client):
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


class TestAuth:
    """인증 API 테스트"""

    def test_register(self, client):
        user_data = {
            "email": "testuser@example.com",
            "nickname": "testuser",
            "password": "securepassword123",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["nickname"] == user_data["nickname"]

    def test_login(self, client):
        user_data = {
            "email": "logintest@example.com",
            "nickname": "loginuser",
            "password": "securepassword123",
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_data = {
            "email": user_data["email"],
            "password": user_data["password"],
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["user"]["email"] == user_data["email"]

    def test_me(self, client):
        user_data = {
            "email": "me@example.com",
            "nickname": "meuser",
            "password": "securepassword123",
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == user_data["email"]

    def test_refresh_token_rotation(self, client):
        user_data = {
            "email": "refresh@example.com",
            "nickname": "refreshuser",
            "password": "securepassword123",
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        old_refresh = register_response.json()["refresh_token"]

        first_refresh = client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": old_refresh},
        )
        assert first_refresh.status_code == 200
        new_refresh = first_refresh.json()["refresh_token"]

        reuse_old = client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": old_refresh},
        )
        assert reuse_old.status_code == 401

        second_refresh = client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": new_refresh},
        )
        assert second_refresh.status_code == 200

    def test_logout_revokes_refresh_token(self, client):
        user_data = {
            "email": "logout@example.com",
            "nickname": "logoutuser",
            "password": "securepassword123",
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        refresh_token = register_response.json()["refresh_token"]

        logout_response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_response.status_code == 200

        refresh_after_logout = client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": refresh_token},
        )
        assert refresh_after_logout.status_code == 401


class TestTarget:
    """Target API 테스트"""

    @pytest.fixture
    def auth_token(self, client):
        user_data = {
            "email": "targettest@example.com",
            "nickname": "targetuser",
            "password": "securepassword123",
        }
        response = client.post("/api/v1/auth/register", json=user_data)
        return response.json()["access_token"]

    def test_create_target(self, client, auth_token):
        target_data = {
            "name": "Mom",
            "description": "My beloved mother",
            "target_type": "parent",
        }
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/v1/targets", json=target_data, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == target_data["name"]
        assert data["id"]

    def test_list_targets_only_my_targets(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        client.post(
            "/api/v1/targets",
            json={"name": "My Target", "description": "mine", "target_type": "other"},
            headers=headers,
        )

        other_user = {
            "email": "other@example.com",
            "nickname": "otheruser",
            "password": "securepassword123",
        }
        other_register = client.post("/api/v1/auth/register", json=other_user)
        other_headers = {"Authorization": f"Bearer {other_register.json()['access_token']}"}
        client.post(
            "/api/v1/targets",
            json={"name": "Other Target", "description": "other", "target_type": "other"},
            headers=other_headers,
        )

        response = client.get("/api/v1/targets", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "My Target"


class TestTargetMedia:
    """TargetMedia API 테스트"""

    @pytest.fixture
    def user_and_target(self, client):
        user_data = {
            "email": "mediauser@example.com",
            "nickname": "mediauser",
            "password": "securepassword123",
        }
        register = client.post("/api/v1/auth/register", json=user_data)
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        target = client.post(
            "/api/v1/targets",
            json={"name": "Media Target", "description": "for media", "target_type": "other"},
            headers=headers,
        )
        return {"token": token, "headers": headers, "target_id": target.json()["id"]}

    def test_upload_list_delete_image_media(self, client, user_and_target):
        target_id = user_and_target["target_id"]
        headers = user_and_target["headers"]

        upload = client.post(
            f"/api/v1/targets/{target_id}/media",
            data={"media_type": "image"},
            files={"file": ("photo.jpg", b"fake-image-data", "image/jpeg")},
            headers=headers,
        )
        assert upload.status_code == 201
        payload = upload.json()
        media_id = payload["file_id"]
        rel_path = payload["file_path"]

        backend_root = Path(__file__).resolve().parents[1]
        assert (backend_root / rel_path).exists()

        media_list = client.get(f"/api/v1/targets/{target_id}/media", headers=headers)
        assert media_list.status_code == 200
        assert len(media_list.json()) == 1

        delete_response = client.delete(f"/api/v1/media/{media_id}", headers=headers)
        assert delete_response.status_code == 200
        assert not (backend_root / rel_path).exists()

    def test_media_permission_denied_for_other_user(self, client, user_and_target):
        target_id = user_and_target["target_id"]

        other_user = client.post(
            "/api/v1/auth/register",
            json={
                "email": "othermedia@example.com",
                "nickname": "othermedia",
                "password": "securepassword123",
            },
        )
        other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}

        upload = client.post(
            f"/api/v1/targets/{target_id}/media",
            data={"media_type": "voice"},
            files={"file": ("voice.wav", b"fake-audio-data", "audio/wav")},
            headers=other_headers,
        )
        assert upload.status_code == 403


class TestPersona:
    """Persona API tests."""

    @pytest.fixture
    def user_and_target(self, client):
        user_data = {
            "email": "personauser@example.com",
            "nickname": "personauser",
            "password": "securepassword123",
        }
        register = client.post("/api/v1/auth/register", json=user_data)
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        target = client.post(
            "/api/v1/targets",
            json={"name": "Grandma", "description": "Loves family stories", "target_type": "grandparent"},
            headers=headers,
        )
        target_id = target.json()["id"]

        client.post(
            f"/api/v1/targets/{target_id}/media",
            data={"media_type": "image"},
            files={"file": ("photo.jpg", b"fake-image-data", "image/jpeg")},
            headers=headers,
        )
        client.post(
            f"/api/v1/targets/{target_id}/media",
            data={"media_type": "voice"},
            files={"file": ("voice.wav", b"fake-audio-data", "audio/wav")},
            headers=headers,
        )
        return {"headers": headers, "target_id": target_id}

    def test_create_get_and_status_persona(self, client, user_and_target):
        headers = user_and_target["headers"]
        target_id = user_and_target["target_id"]

        create_response = client.post(f"/api/v1/targets/{target_id}/persona", headers=headers)
        assert create_response.status_code == 201
        persona = create_response.json()
        assert persona["target_id"] == target_id
        assert persona["status"] == "READY"
        assert persona["persona_name"] == "Grandma Persona"
        assert "1 uploaded photo" in persona["memory_summary"]
        assert persona["is_voice_profile_created"] is True
        assert persona["voice_profile"]["metadata"]["voice_media_count"] == 1

        persona_id = persona["id"]
        detail_response = client.get(f"/api/v1/personas/{persona_id}", headers=headers)
        assert detail_response.status_code == 200
        assert detail_response.json()["id"] == persona_id

        status_response = client.get(f"/api/v1/personas/{persona_id}/status", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json() == {
            "persona_id": persona_id,
            "target_id": target_id,
            "status": "READY",
        }

    def test_create_persona_denied_for_other_user_target(self, client, user_and_target):
        target_id = user_and_target["target_id"]
        other_user = client.post(
            "/api/v1/auth/register",
            json={
                "email": "otherpersona@example.com",
                "nickname": "otherpersona",
                "password": "securepassword123",
            },
        )
        other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}

        response = client.post(f"/api/v1/targets/{target_id}/persona", headers=other_headers)
        assert response.status_code == 403


class TestPersonaChat:
    """PersonaChat and PersonaMessage API tests."""

    @pytest.fixture
    def persona_context(self, client):
        user_data = {
            "email": "chatuser@example.com",
            "nickname": "chatuser",
            "password": "securepassword123",
        }
        register = client.post("/api/v1/auth/register", json=user_data)
        headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

        target = client.post(
            "/api/v1/targets",
            json={"name": "Dad", "description": "Enjoys practical advice", "target_type": "parent"},
            headers=headers,
        )
        persona = client.post(
            f"/api/v1/targets/{target.json()['id']}/persona",
            headers=headers,
        )
        return {"headers": headers, "persona_id": persona.json()["id"]}

    def test_create_list_chat_and_messages(self, client, persona_context):
        headers = persona_context["headers"]
        persona_id = persona_context["persona_id"]

        chat_response = client.post(
            f"/api/v1/personas/{persona_id}/chats",
            json={"title": "First chat"},
            headers=headers,
        )
        assert chat_response.status_code == 201
        chat = chat_response.json()
        assert chat["persona_id"] == persona_id
        assert chat["title"] == "First chat"
        assert chat["deleted_at"] is None

        chats = client.get(f"/api/v1/personas/{persona_id}/chats", headers=headers)
        assert chats.status_code == 200
        assert len(chats.json()) == 1

        message_response = client.post(
            f"/api/v1/chats/{chat['id']}/messages",
            json={"message_type": "TEXT", "content": "How should I remember this day?"},
            headers=headers,
        )
        assert message_response.status_code == 201
        payload = message_response.json()
        assert payload["user_message"]["sender_type"] == "USER"
        assert payload["user_message"]["is_ai_generated"] is False
        assert payload["persona_message"]["sender_type"] == "PERSONA"
        assert payload["persona_message"]["is_ai_generated"] is True

        messages = client.get(f"/api/v1/chats/{chat['id']}/messages", headers=headers)
        assert messages.status_code == 200
        message_list = messages.json()
        assert [message["sender_type"] for message in message_list] == ["USER", "PERSONA"]
        assert message_list[0]["created_at"] <= message_list[1]["created_at"]

    def test_other_user_cannot_access_persona_chat(self, client, persona_context):
        persona_id = persona_context["persona_id"]
        other_user = client.post(
            "/api/v1/auth/register",
            json={
                "email": "otherchat@example.com",
                "nickname": "otherchat",
                "password": "securepassword123",
            },
        )
        other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}

        chat_response = client.post(
            f"/api/v1/personas/{persona_id}/chats",
            json={"title": "Blocked"},
            headers=other_headers,
        )
        assert chat_response.status_code == 403

        owner_chat = client.post(
            f"/api/v1/personas/{persona_id}/chats",
            json={"title": "Owner chat"},
            headers=persona_context["headers"],
        )
        message_response = client.post(
            f"/api/v1/chats/{owner_chat.json()['id']}/messages",
            json={"message_type": "TEXT", "content": "hello"},
            headers=other_headers,
        )
        assert message_response.status_code == 403

