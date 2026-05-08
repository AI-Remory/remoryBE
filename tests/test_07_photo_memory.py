from pathlib import Path


def test_upload_list_get_photo_memory(client, auth_headers, created_photo_memory):
    backend_root = Path(__file__).resolve().parents[1]
    assert (backend_root / created_photo_memory["file_path"]).exists()

    list_response = client.get("/api/v1/photo-memories", headers=auth_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(
        f"/api/v1/photo-memories/{created_photo_memory['id']}",
        headers=auth_headers,
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == created_photo_memory["title"]


def test_reject_non_image_photo_memory(client, auth_headers):
    response = client.post(
        "/api/v1/photo-memories",
        data={"title": "Not image"},
        files={"file": ("note.txt", b"not image", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_other_user_cannot_access_photo_memory(client, created_photo_memory, second_user_headers):
    response = client.get(
        f"/api/v1/photo-memories/{created_photo_memory['id']}",
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)
