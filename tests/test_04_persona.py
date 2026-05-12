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


def test_create_and_get_persona_voice_profile(client, auth_headers, created_persona):
    create_response = client.post(
        f"/api/v1/personas/{created_persona['id']}/voice-profile",
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["persona_id"] == created_persona["id"]
    assert payload["target_id"] == created_persona["target_id"]
    assert payload["provider"] == "mock"
    assert payload["status"] in {"PENDING", "NEEDS_MORE_SAMPLES"}
    assert payload["review_status"] == "NOT_REVIEWED"
    assert payload["reference_audio_count"] >= 1

    evaluate_response = client.post(
        f"/api/v1/personas/{created_persona['id']}/voice-profile/evaluate",
        headers=auth_headers,
    )
    assert evaluate_response.status_code == 200
    evaluated = evaluate_response.json()
    assert evaluated["status"] in {"READY", "NEEDS_MORE_SAMPLES", "FAILED"}

    get_response = client.get(
        f"/api/v1/personas/{created_persona['id']}/voice-profile",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == payload["id"]


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


def test_create_persona_fails_with_revoked_verification(
    client,
    auth_headers,
    admin_headers,
    created_target,
    uploaded_media,
    target_persona_consent,
    target_verification,
):
    revoke_response = client.patch(
        f"/api/v1/admin/verification-requests/{target_verification.id}/revoke",
        json={"admin_note": "revoked for test"},
        headers=admin_headers,
    )
    assert revoke_response.status_code == 200

    response = client.post(f"/api/v1/targets/{created_target['id']}/persona", headers=auth_headers)
    assert response.status_code == 403


def test_create_persona_fails_with_expired_verification(
    client,
    auth_headers,
    created_target,
    uploaded_media,
    target_persona_consent,
    target_verification,
):
    from datetime import UTC, datetime, timedelta

    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        verification = db.merge(target_verification)
        verification.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    response = client.post(f"/api/v1/targets/{created_target['id']}/persona", headers=auth_headers)
    assert response.status_code == 403


def test_create_persona_requires_consent(client, auth_headers, uploaded_media, target_verification):
    target_id = uploaded_media["image"]["target_id"]
    response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)
    assert response.status_code == 403


def test_create_voice_profile_requires_reference_audio(client, auth_headers, created_target, target_persona_consent, target_verification):
    persona_response = client.post(f"/api/v1/targets/{created_target['id']}/persona", headers=auth_headers)
    assert persona_response.status_code == 201

    response = client.post(
        f"/api/v1/personas/{persona_response.json()['id']}/voice-profile",
        headers=auth_headers,
    )

    assert response.status_code == 400


def test_user_can_confirm_ready_voice_profile(client, auth_headers, created_persona):
    create_response = client.post(
        f"/api/v1/personas/{created_persona['id']}/voice-profile",
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    evaluate_response = client.post(
        f"/api/v1/personas/{created_persona['id']}/voice-profile/evaluate",
        headers=auth_headers,
    )
    assert evaluate_response.status_code == 200
    assert evaluate_response.json()["status"] == "READY"

    confirm_response = client.patch(
        f"/api/v1/personas/{created_persona['id']}/voice-profile/user-confirm",
        headers=auth_headers,
        json={"review_note": "looks good"},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["review_status"] == "USER_CONFIRMED"


def test_other_user_cannot_access_persona(client, created_persona, second_user_headers):
    response = client.get(f"/api/v1/personas/{created_persona['id']}", headers=second_user_headers)
    assert response.status_code in (403, 404)


def test_other_user_cannot_access_voice_profile(client, created_persona, second_user_headers):
    response = client.post(
        f"/api/v1/personas/{created_persona['id']}/voice-profile",
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)
