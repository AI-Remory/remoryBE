def test_create_and_get_persona(client, auth_headers, created_persona):
    response = client.get(f"/api/v1/personas/{created_persona['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_persona["id"]
    assert response.json()["status"] == "READY"
    assert response.json()["persona_name"]


def test_persona_status(client, auth_headers, created_persona):
    response = client.get(f"/api/v1/personas/{created_persona['id']}/status", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "READY"


def test_create_persona_requires_consent(client, auth_headers, uploaded_media):
    target_id = uploaded_media["image"]["target_id"]
    response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)
    assert response.status_code == 403


def test_other_user_cannot_access_persona(client, created_persona, second_user_headers):
    response = client.get(f"/api/v1/personas/{created_persona['id']}", headers=second_user_headers)
    assert response.status_code in (403, 404)
