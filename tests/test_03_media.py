from pathlib import Path


def test_upload_target_media_image_and_voice(uploaded_media):
    image = uploaded_media["image"]
    voice = uploaded_media["voice"]
    assert image["media_type"] == "image"
    assert voice["media_type"] == "voice"

    backend_root = Path(__file__).resolve().parents[1]
    assert (backend_root / image["file_path"]).exists()
    assert (backend_root / voice["file_path"]).exists()


def test_list_target_media(client, auth_headers, created_target, uploaded_media):
    response = client.get(f"/api/v1/targets/{created_target['id']}/media", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_upload_target_media_requires_consent(client, auth_headers, created_target):
    target_id = created_target["id"]

    image = client.post(
        f"/api/v1/targets/{target_id}/media",
        data={"media_type": "image"},
        files={"file": ("photo.jpg", b"fake image content", "image/jpeg")},
        headers=auth_headers,
    )
    assert image.status_code == 403

    voice = client.post(
        f"/api/v1/targets/{target_id}/media",
        data={"media_type": "voice"},
        files={"file": ("voice.mp3", b"fake audio content", "audio/mpeg")},
        headers=auth_headers,
    )
    assert voice.status_code == 403


def test_other_user_cannot_upload_media(client, created_target, second_user_headers):
    response = client.post(
        f"/api/v1/targets/{created_target['id']}/media",
        data={"media_type": "image"},
        files={"file": ("photo.jpg", b"fake image content", "image/jpeg")},
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)
