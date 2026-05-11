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


def test_create_persona_requires_verification(client, auth_headers, created_target, uploaded_media, target_persona_consent):
    """Test that persona creation fails without target verification."""
    target_id = created_target["id"]
    response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)
    assert response.status_code == 403
    assert "Target verification approval is required" in response.json()["detail"]


def test_create_persona_with_verification(client, auth_headers, created_target, uploaded_media, target_persona_consent, target_verification):
    """Test that persona creation succeeds with approved target verification."""
    target_id = created_target["id"]
    response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["status"] == "READY"


def test_create_persona_requires_consent(client, auth_headers, uploaded_media, target_verification):
    target_id = uploaded_media["image"]["target_id"]
    response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)
    assert response.status_code == 403


def test_other_user_cannot_access_persona(client, created_persona, second_user_headers):
    response = client.get(f"/api/v1/personas/{created_persona['id']}", headers=second_user_headers)
    assert response.status_code in (403, 404)


