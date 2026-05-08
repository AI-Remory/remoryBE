"""API 테스트"""
from datetime import UTC, datetime, timedelta
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


class TestAIInterview:
    """AI interview session API tests."""

    @pytest.fixture
    def interview_context(self, client):
        user_data = {
            "email": "interviewuser@example.com",
            "nickname": "interviewuser",
            "password": "securepassword123",
        }
        register = client.post("/api/v1/auth/register", json=user_data)
        headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

        target = client.post(
            "/api/v1/targets",
            json={"name": "Aunt", "description": "Kind storyteller", "target_type": "other"},
            headers=headers,
        )
        return {"headers": headers, "target_id": target.json()["id"]}

    def test_create_question_answer_and_get_detail(self, client, interview_context):
        headers = interview_context["headers"]
        target_id = interview_context["target_id"]

        session_response = client.post(
            "/api/v1/interviews",
            json={
                "session_type": "TARGET_PROFILE",
                "target_id": target_id,
                "title": "Profile interview",
            },
            headers=headers,
        )
        assert session_response.status_code == 201
        session = session_response.json()
        assert session["session_type"] == "TARGET_PROFILE"
        assert session["status"] == "IN_PROGRESS"
        assert session["deleted_at"] is None

        question_response = client.post(
            f"/api/v1/interviews/{session['id']}/questions",
            json={"question_type": "speaking_style"},
            headers=headers,
        )
        assert question_response.status_code == 201
        question = question_response.json()
        assert question["question_text"] == "이 사람이 평소 자주 하던 말은 무엇인가요?"
        assert question["order_index"] == 1

        answer_response = client.post(
            f"/api/v1/interviews/{session['id']}/answers",
            json={"question_id": question["id"], "answer_text": "늘 괜찮다고 말해줬어요."},
            headers=headers,
        )
        assert answer_response.status_code == 201
        assert answer_response.json()["question_id"] == question["id"]

        detail_response = client.get(f"/api/v1/interviews/{session['id']}", headers=headers)
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert len(detail["questions"]) == 1
        assert len(detail["questions"][0]["answers"]) == 1
        assert detail["questions"][0]["answers"][0]["answer_text"] == "늘 괜찮다고 말해줬어요."

    def test_self_story_session_can_be_created_without_target(self, client, interview_context):
        response = client.post(
            "/api/v1/interviews",
            json={"session_type": "SELF_STORY", "title": "My story"},
            headers=interview_context["headers"],
        )
        assert response.status_code == 201
        assert response.json()["target_id"] is None

    def test_target_profile_requires_target_id(self, client, interview_context):
        response = client.post(
            "/api/v1/interviews",
            json={"session_type": "TARGET_PROFILE"},
            headers=interview_context["headers"],
        )
        assert response.status_code == 422

    def test_other_user_cannot_access_session(self, client, interview_context):
        session_response = client.post(
            "/api/v1/interviews",
            json={"session_type": "SELF_STORY"},
            headers=interview_context["headers"],
        )
        session_id = session_response.json()["id"]

        other_user = client.post(
            "/api/v1/auth/register",
            json={
                "email": "otherinterview@example.com",
                "nickname": "otherinterview",
                "password": "securepassword123",
            },
        )
        other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}

        response = client.get(f"/api/v1/interviews/{session_id}", headers=other_headers)
        assert response.status_code == 403


class TestPhotoMemory:
    """PhotoMemory API tests."""

    @pytest.fixture
    def auth_headers(self, client):
        user_data = {
            "email": "photomemory@example.com",
            "nickname": "photomemory",
            "password": "securepassword123",
        }
        register = client.post("/api/v1/auth/register", json=user_data)
        return {"Authorization": f"Bearer {register.json()['access_token']}"}

    def test_create_list_get_and_delete_photo_memory(self, client, auth_headers):
        upload = client.post(
            "/api/v1/photo-memories",
            data={
                "title": "Birthday",
                "description": "Family birthday photo",
                "location": "Seoul",
            },
            files={"file": ("birthday.jpg", b"fake-image-data", "image/jpeg")},
            headers=auth_headers,
        )
        assert upload.status_code == 201
        payload = upload.json()
        photo_memory_id = payload["id"]
        rel_path = payload["file_path"]
        assert payload["title"] == "Birthday"
        assert payload["original_filename"] == "birthday.jpg"
        assert payload["stored_filename"] != "birthday.jpg"

        backend_root = Path(__file__).resolve().parents[1]
        assert (backend_root / rel_path).exists()

        photo_list = client.get("/api/v1/photo-memories", headers=auth_headers)
        assert photo_list.status_code == 200
        assert len(photo_list.json()) == 1

        detail = client.get(f"/api/v1/photo-memories/{photo_memory_id}", headers=auth_headers)
        assert detail.status_code == 200
        assert detail.json()["id"] == photo_memory_id

        delete_response = client.delete(f"/api/v1/photo-memories/{photo_memory_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        assert not (backend_root / rel_path).exists()

        after_delete = client.get("/api/v1/photo-memories", headers=auth_headers)
        assert after_delete.status_code == 200
        assert after_delete.json() == []

    def test_reject_non_image_photo_memory_upload(self, client, auth_headers):
        response = client.post(
            "/api/v1/photo-memories",
            data={"title": "Not image"},
            files={"file": ("note.txt", b"text", "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_other_user_cannot_access_photo_memory(self, client, auth_headers):
        upload = client.post(
            "/api/v1/photo-memories",
            data={"title": "Private"},
            files={"file": ("private.jpg", b"fake-image-data", "image/jpeg")},
            headers=auth_headers,
        )
        photo_memory_id = upload.json()["id"]

        other_user = client.post(
            "/api/v1/auth/register",
            json={
                "email": "otherphoto@example.com",
                "nickname": "otherphoto",
                "password": "securepassword123",
            },
        )
        other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}

        response = client.get(f"/api/v1/photo-memories/{photo_memory_id}", headers=other_headers)
        assert response.status_code == 403

    def test_photo_memory_can_be_linked_to_photo_interview(self, client, auth_headers):
        upload = client.post(
            "/api/v1/photo-memories",
            data={"title": "Trip"},
            files={"file": ("trip.jpg", b"fake-image-data", "image/jpeg")},
            headers=auth_headers,
        )
        photo_memory_id = upload.json()["id"]

        session = client.post(
            "/api/v1/interviews",
            json={"session_type": "PHOTO_MEMORY", "photo_memory_id": photo_memory_id},
            headers=auth_headers,
        )
        assert session.status_code == 201
        assert session.json()["photo_memory_id"] == photo_memory_id


class TestStoryBook:
    """StoryBook and StoryChapter API tests."""

    @pytest.fixture
    def story_context(self, client):
        user_data = {
            "email": "storybook@example.com",
            "nickname": "storybook",
            "password": "securepassword123",
        }
        register = client.post("/api/v1/auth/register", json=user_data)
        headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

        session = client.post(
            "/api/v1/interviews",
            json={"session_type": "SELF_STORY", "title": "Self story interview"},
            headers=headers,
        ).json()
        question = client.post(
            f"/api/v1/interviews/{session['id']}/questions",
            json={"question_type": "memory"},
            headers=headers,
        ).json()
        client.post(
            f"/api/v1/interviews/{session['id']}/answers",
            json={"question_id": question["id"], "answer_text": "A quiet morning changed how I saw my family."},
            headers=headers,
        )

        photo = client.post(
            "/api/v1/photo-memories",
            data={"title": "Picnic", "description": "A sunny picnic near the river"},
            files={"file": ("picnic.jpg", b"fake-image-data", "image/jpeg")},
            headers=headers,
        ).json()
        return {"headers": headers, "session_id": session["id"], "photo_memory_id": photo["id"]}

    def test_create_list_get_chapters_and_regenerate_from_interview(self, client, story_context):
        headers = story_context["headers"]
        create_response = client.post(
            "/api/v1/storybooks",
            json={
                "title": "My Story",
                "interview_session_id": story_context["session_id"],
            },
            headers=headers,
        )
        assert create_response.status_code == 201
        storybook = create_response.json()
        assert storybook["source_type"] == "SELF_STORY"
        assert storybook["status"] == "GENERATED"
        assert storybook["visibility"] == "PRIVATE"
        assert len(storybook["chapters"]) == 1
        assert "A quiet morning" in storybook["chapters"][0]["content"]

        storybook_id = storybook["id"]
        storybooks = client.get("/api/v1/storybooks", headers=headers)
        assert storybooks.status_code == 200
        assert len(storybooks.json()) == 1

        detail = client.get(f"/api/v1/storybooks/{storybook_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["id"] == storybook_id

        chapters = client.get(f"/api/v1/storybooks/{storybook_id}/chapters", headers=headers)
        assert chapters.status_code == 200
        assert [chapter["order_index"] for chapter in chapters.json()] == [1]

        regenerated = client.post(f"/api/v1/storybooks/{storybook_id}/regenerate", headers=headers)
        assert regenerated.status_code == 200
        assert regenerated.json()["id"] == storybook_id
        assert len(regenerated.json()["chapters"]) == 1

    def test_create_storybook_from_photo_memory(self, client, story_context):
        response = client.post(
            "/api/v1/storybooks",
            json={
                "title": "Photo Story",
                "photo_memory_id": story_context["photo_memory_id"],
                "visibility": "LINK",
            },
            headers=story_context["headers"],
        )
        assert response.status_code == 201
        payload = response.json()
        assert payload["source_type"] == "PHOTO_MEMORY"
        assert payload["visibility"] == "LINK"
        assert "sunny picnic" in payload["chapters"][0]["content"]

    def test_storybook_requires_source(self, client, story_context):
        response = client.post(
            "/api/v1/storybooks",
            json={"title": "Missing source"},
            headers=story_context["headers"],
        )
        assert response.status_code == 422

    def test_other_user_cannot_access_storybook(self, client, story_context):
        storybook = client.post(
            "/api/v1/storybooks",
            json={"title": "Private Story", "interview_session_id": story_context["session_id"]},
            headers=story_context["headers"],
        ).json()

        other_user = client.post(
            "/api/v1/auth/register",
            json={
                "email": "otherstorybook@example.com",
                "nickname": "otherstorybook",
                "password": "securepassword123",
            },
        )
        other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}

        response = client.get(f"/api/v1/storybooks/{storybook['id']}", headers=other_headers)
        assert response.status_code == 403


class TestShareLink:
    """ShareLink API tests."""

    @pytest.fixture
    def share_context(self, client):
        user_data = {
            "email": "shareuser@example.com",
            "nickname": "shareuser",
            "password": "securepassword123",
        }
        register = client.post("/api/v1/auth/register", json=user_data)
        headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

        session = client.post(
            "/api/v1/interviews",
            json={"session_type": "SELF_STORY", "title": "Share interview"},
            headers=headers,
        ).json()
        question = client.post(
            f"/api/v1/interviews/{session['id']}/questions",
            json={},
            headers=headers,
        ).json()
        client.post(
            f"/api/v1/interviews/{session['id']}/answers",
            json={"question_id": question["id"], "answer_text": "A memory worth sharing."},
            headers=headers,
        )
        storybook = client.post(
            "/api/v1/storybooks",
            json={"title": "Shared Story", "interview_session_id": session["id"]},
            headers=headers,
        ).json()
        return {"headers": headers, "storybook_id": storybook["id"]}

    def test_create_list_public_read_and_disable_share_link(self, client, share_context):
        headers = share_context["headers"]
        storybook_id = share_context["storybook_id"]

        create_response = client.post(
            f"/api/v1/storybooks/{storybook_id}/share-links",
            json={},
            headers=headers,
        )
        assert create_response.status_code == 201
        share_link = create_response.json()
        assert share_link["storybook_id"] == storybook_id
        assert share_link["is_active"] is True
        assert share_link["share_url"] == f"/api/v1/share/{share_link['token']}"

        storybook_detail = client.get(f"/api/v1/storybooks/{storybook_id}", headers=headers)
        assert storybook_detail.status_code == 200
        assert storybook_detail.json()["visibility"] == "LINK"

        links = client.get(f"/api/v1/storybooks/{storybook_id}/share-links", headers=headers)
        assert links.status_code == 200
        assert len(links.json()) == 1

        public_response = client.get(f"/api/v1/share/{share_link['token']}")
        assert public_response.status_code == 200
        public_payload = public_response.json()
        assert public_payload["title"] == "Shared Story"
        assert public_payload["visibility"] == "LINK"
        assert "owner_id" not in public_payload
        assert "file_path" not in public_payload
        assert len(public_payload["chapters"]) == 1

        disable_response = client.patch(
            f"/api/v1/share-links/{share_link['id']}/disable",
            headers=headers,
        )
        assert disable_response.status_code == 200
        assert disable_response.json()["is_active"] is False

        blocked_response = client.get(f"/api/v1/share/{share_link['token']}")
        assert blocked_response.status_code == 403

    def test_other_user_cannot_create_or_disable_share_link(self, client, share_context):
        other_user = client.post(
            "/api/v1/auth/register",
            json={
                "email": "othershare@example.com",
                "nickname": "othershare",
                "password": "securepassword123",
            },
        )
        other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}
        storybook_id = share_context["storybook_id"]

        denied_create = client.post(
            f"/api/v1/storybooks/{storybook_id}/share-links",
            json={},
            headers=other_headers,
        )
        assert denied_create.status_code == 403

        share_link = client.post(
            f"/api/v1/storybooks/{storybook_id}/share-links",
            json={},
            headers=share_context["headers"],
        ).json()
        denied_disable = client.patch(
            f"/api/v1/share-links/{share_link['id']}/disable",
            headers=other_headers,
        )
        assert denied_disable.status_code == 403

    def test_expired_share_link_is_blocked(self, client, share_context):
        expires_at = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        share_link = client.post(
            f"/api/v1/storybooks/{share_context['storybook_id']}/share-links",
            json={"expires_at": expires_at},
            headers=share_context["headers"],
        ).json()

        response = client.get(f"/api/v1/share/{share_link['token']}")
        assert response.status_code == 403

