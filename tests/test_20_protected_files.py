from pathlib import Path

from app.main import app
from app.models.chat import MessageType
from app.models.interview import PhotoMemory
from tests.conftest import TestingSessionLocal


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _create_photo_memory(client, headers):
    response = client.post(
        "/api/v1/photo-memories",
        data={"title": "Protected photo"},
        files={"file": ("photo.jpg", b"fake image content", "image/jpeg")},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_owner_can_access_photo_memory_image(client, auth_headers):
    photo = _create_photo_memory(client, auth_headers)

    response = client.get(f"/api/v1/photo-memories/{photo['id']}/image", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")
    assert response.content == b"fake image content"


def test_other_user_cannot_access_photo_memory_image(client, auth_headers, second_user_headers):
    photo = _create_photo_memory(client, auth_headers)

    response = client.get(f"/api/v1/photo-memories/{photo['id']}/image", headers=second_user_headers)

    assert response.status_code == 403


def test_photo_memory_image_missing_file_returns_404(client, auth_headers):
    photo = _create_photo_memory(client, auth_headers)

    db = TestingSessionLocal()
    try:
        photo_memory = db.get(PhotoMemory, photo["id"])
        (_backend_root() / photo_memory.file_path).unlink()
        db.commit()
    finally:
        db.close()

    response = client.get(f"/api/v1/photo-memories/{photo['id']}/image", headers=auth_headers)

    assert response.status_code == 404


def test_uploads_outside_path_is_blocked(client, auth_headers):
    photo = _create_photo_memory(client, auth_headers)

    db = TestingSessionLocal()
    try:
        photo_memory = db.get(PhotoMemory, photo["id"])
        photo_memory.file_path = "../outside.jpg"
        db.commit()
    finally:
        db.close()

    response = client.get(f"/api/v1/photo-memories/{photo['id']}/image", headers=auth_headers)

    assert response.status_code == 403


def test_owner_can_access_target_media_file(client, auth_headers, created_target, target_media_consents):
    response = client.post(
        f"/api/v1/targets/{created_target['id']}/media",
        data={"media_type": "image"},
        files={"file": ("target.png", b"target image", "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    media = response.json()

    file_response = client.get(
        f"/api/v1/targets/{created_target['id']}/media/{media['file_id']}/file",
        headers=auth_headers,
    )

    assert file_response.status_code == 200
    assert file_response.headers["content-type"].startswith("image/png")
    assert file_response.content == b"target image"


def test_admin_only_verification_file_access(client, auth_headers, admin_headers, target_verification):
    file_path = _backend_root() / target_verification.submitted_file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"verification document")

    user_response = client.get(
        f"/api/v1/admin/verification-requests/{target_verification.id}/file",
        headers=auth_headers,
    )
    admin_response = client.get(
        f"/api/v1/admin/verification-requests/{target_verification.id}/file",
        headers=admin_headers,
    )

    assert user_response.status_code == 403
    assert admin_response.status_code == 200
    assert admin_response.content == b"verification document"


def test_chat_owner_can_access_message_audio(client, auth_headers, created_chat):
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/audio",
        data={"generate_audio": "false"},
        files={"file": ("voice.webm", b"fake audio content", "audio/webm")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    message = response.json()["user_message"]
    assert message["message_type"] == MessageType.AUDIO.value
    assert message["audio_api_url"] == f"/api/v1/chats/{created_chat['id']}/messages/{message['id']}/audio"

    audio = client.get(message["audio_api_url"], headers=auth_headers)

    assert audio.status_code == 200
    assert audio.headers["content-type"].startswith("audio/webm")
    assert audio.content == b"fake audio content"


def test_other_user_cannot_access_message_audio(client, auth_headers, second_user_headers, created_chat):
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/audio",
        data={"generate_audio": "false"},
        files={"file": ("voice.webm", b"fake audio content", "audio/webm")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    message = response.json()["user_message"]

    audio = client.get(message["audio_api_url"], headers=second_user_headers)

    assert audio.status_code == 403


def test_public_uploads_route_is_not_mounted_by_default():
    assert all(getattr(route, "path", None) != "/uploads" for route in app.routes)
