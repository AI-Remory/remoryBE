def _create_consent(client, headers, target_id, consent_type, is_agreed=True):
    response = client.post(
        "/api/v1/consents",
        json={
            "target_id": target_id,
            "consent_type": consent_type,
            "consent_version": "2026-05-12",
            "consent_text_snapshot": f"{consent_type} snapshot",
            "is_agreed": is_agreed,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_create_granular_consent_success(client, auth_headers, created_target):
    payload = _create_consent(
        client,
        auth_headers,
        created_target["id"],
        "ai_persona_creation_consent",
    )

    assert payload["target_id"] == created_target["id"]
    assert payload["consent_type"] == "ai_persona_creation_consent"
    assert payload["consent_version"] == "2026-05-12"
    assert payload["is_agreed"] is True
    assert payload["is_consented"] is True
    assert payload["agreed_at"] is not None
    assert payload["revoked_at"] is None


def test_other_user_cannot_create_target_consent(client, created_target, second_user_headers):
    response = client.post(
        "/api/v1/consents",
        json={
            "target_id": created_target["id"],
            "consent_type": "ai_persona_creation_consent",
            "is_agreed": True,
        },
        headers=second_user_headers,
    )

    assert response.status_code in (403, 404)


def test_revoke_consent_success(client, auth_headers, created_target):
    consent = _create_consent(
        client,
        auth_headers,
        created_target["id"],
        "ai_response_notice_consent",
    )

    response = client.patch(f"/api/v1/consents/{consent['id']}/revoke", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == consent["id"]
    assert payload["is_agreed"] is False
    assert payload["is_consented"] is False
    assert payload["revoked_at"] is not None


def test_revoked_consent_is_not_valid_for_persona_creation(
    client,
    auth_headers,
    created_target,
    target_verification,
):
    persona_consent = _create_consent(
        client,
        auth_headers,
        created_target["id"],
        "ai_persona_creation_consent",
    )
    _create_consent(
        client,
        auth_headers,
        created_target["id"],
        "ai_response_notice_consent",
    )
    revoke = client.patch(f"/api/v1/consents/{persona_consent['id']}/revoke", headers=auth_headers)
    assert revoke.status_code == 200

    response = client.post(f"/api/v1/targets/{created_target['id']}/persona", headers=auth_headers)

    assert response.status_code == 403


def test_revoked_voice_cloning_consent_is_not_valid_for_voice_profile(
    client,
    auth_headers,
    created_target,
    target_verification,
):
    target_id = created_target["id"]
    _create_consent(client, auth_headers, target_id, "voice_upload_consent")
    voice_clone = _create_consent(client, auth_headers, target_id, "voice_cloning_consent")

    upload = client.post(
        f"/api/v1/targets/{target_id}/media",
        data={"media_type": "voice"},
        files={"file": ("voice.mp3", b"fake audio content", "audio/mpeg")},
        headers=auth_headers,
    )
    assert upload.status_code == 201

    _create_consent(client, auth_headers, target_id, "ai_persona_creation_consent")
    _create_consent(client, auth_headers, target_id, "ai_response_notice_consent")
    revoke = client.patch(f"/api/v1/consents/{voice_clone['id']}/revoke", headers=auth_headers)
    assert revoke.status_code == 200

    response = client.post(f"/api/v1/targets/{target_id}/persona", headers=auth_headers)

    assert response.status_code == 403


def test_duplicate_consent_latest_state_is_used(client, auth_headers, created_target):
    target_id = created_target["id"]
    _create_consent(client, auth_headers, target_id, "ai_response_notice_consent", is_agreed=True)
    latest = _create_consent(client, auth_headers, target_id, "ai_response_notice_consent", is_agreed=False)

    listed = client.get(f"/api/v1/targets/{target_id}/consents", headers=auth_headers)

    assert listed.status_code == 200
    assert listed.json()[0]["id"] == latest["id"]
    assert listed.json()[0]["is_agreed"] is False
