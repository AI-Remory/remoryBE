from pathlib import Path


def test_delete_photo_memory_removes_file(client, auth_headers, created_photo_memory):
    backend_root = Path(__file__).resolve().parents[1]
    photo_path = backend_root / created_photo_memory["file_path"]
    assert photo_path.exists()

    response = client.post(
        "/api/v1/deletion-requests",
        json={"target_type": "PHOTO_MEMORY", "target_id": created_photo_memory["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "COMPLETED"
    assert not photo_path.exists()


def test_delete_target_media_removes_file(client, auth_headers, uploaded_media):
    backend_root = Path(__file__).resolve().parents[1]
    media = uploaded_media["image"]
    media_path = backend_root / media["file_path"]
    assert media_path.exists()

    response = client.post(
        "/api/v1/deletion-requests",
        json={"target_type": "TARGET_MEDIA", "target_id": media["file_id"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "COMPLETED"
    assert not media_path.exists()


def test_delete_storybook_blocks_share_link(client, auth_headers, created_storybook, storybook_share_consent):
    share_link = client.post(
        f"/api/v1/storybooks/{created_storybook['id']}/share-links",
        json={},
        headers=auth_headers,
    ).json()
    response = client.post(
        "/api/v1/deletion-requests",
        json={"target_type": "STORYBOOK", "target_id": created_storybook["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "COMPLETED"

    blocked = client.get(f"/api/v1/share/{share_link['token']}")
    assert blocked.status_code in (403, 404)


def test_list_and_get_deletion_requests(client, auth_headers, created_target):
    created = client.post(
        "/api/v1/deletion-requests",
        json={"target_type": "TARGET", "target_id": created_target["id"], "reason": "cleanup"},
        headers=auth_headers,
    )
    assert created.status_code == 201

    list_response = client.get("/api/v1/deletion-requests", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == created.json()["id"]

    detail_response = client.get(f"/api/v1/deletion-requests/{created.json()['id']}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["reason"] == "cleanup"


def test_other_user_cannot_create_deletion_request(client, created_target, second_user_headers):
    response = client.post(
        "/api/v1/deletion-requests",
        json={"target_type": "TARGET", "target_id": created_target["id"]},
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)
