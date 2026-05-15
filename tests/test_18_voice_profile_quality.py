def _create_profile_and_evaluate(client, auth_headers, persona_id):
    create_response = client.post(f"/api/v1/personas/{persona_id}/voice-profile", headers=auth_headers)
    assert create_response.status_code == 201

    evaluate_response = client.post(
        f"/api/v1/personas/{persona_id}/voice-profile/evaluate",
        headers=auth_headers,
    )
    assert evaluate_response.status_code == 200
    return create_response.json(), evaluate_response.json()


def test_voice_profile_create_fails_without_voice_samples(
    client,
    auth_headers,
    created_target,
    target_persona_consent,
    target_verification,
):
    persona_response = client.post(f"/api/v1/targets/{created_target['id']}/persona", headers=auth_headers)
    assert persona_response.status_code == 201

    response = client.post(
        f"/api/v1/personas/{persona_response.json()['id']}/voice-profile",
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_voice_profile_create_fails_without_voice_cloning_consent(
    client,
    auth_headers,
    created_target,
    target_media_consents,
    target_verification,
):
    # Persona creation does not require voice cloning consent while there is no voice media.
    client.post(
        "/api/v1/consents",
        headers=auth_headers,
        json={
            "target_id": created_target["id"],
            "consent_type": "ai_persona_creation_consent",
            "is_agreed": True,
        },
    )
    client.post(
        "/api/v1/consents",
        headers=auth_headers,
        json={
            "target_id": created_target["id"],
            "consent_type": "ai_response_notice_consent",
            "is_agreed": True,
        },
    )

    persona_response = client.post(f"/api/v1/targets/{created_target['id']}/persona", headers=auth_headers)
    assert persona_response.status_code == 201

    upload_response = client.post(
        f"/api/v1/targets/{created_target['id']}/media",
        data={"media_type": "voice"},
        files={"file": ("voice.mp3", b"a" * 100000, "audio/mpeg")},
        headers=auth_headers,
    )
    assert upload_response.status_code == 201

    response = client.post(
        f"/api/v1/personas/{persona_response.json()['id']}/voice-profile",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_voice_profile_create_fails_when_verification_not_approved(
    client,
    auth_headers,
    admin_headers,
    created_persona,
    target_verification,
):
    revoke_response = client.patch(
        f"/api/v1/admin/verification-requests/{target_verification.id}/revoke",
        headers=admin_headers,
        json={"admin_note": "revoked for voice test"},
    )
    assert revoke_response.status_code == 200

    response = client.post(
        f"/api/v1/personas/{created_persona['id']}/voice-profile",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_voice_profile_needs_more_samples_when_duration_too_short(
    client,
    auth_headers,
    created_target,
    target_persona_consent,
    target_verification,
):
    persona_response = client.post(f"/api/v1/targets/{created_target['id']}/persona", headers=auth_headers)
    assert persona_response.status_code == 201

    # 2KB passes minimum file size but estimated duration stays below threshold.
    upload_response = client.post(
        f"/api/v1/targets/{created_target['id']}/media",
        data={"media_type": "voice"},
        files={"file": ("tiny.mp3", b"a" * 2000, "audio/mpeg")},
        headers=auth_headers,
    )
    assert upload_response.status_code == 201

    create_response = client.post(
        f"/api/v1/personas/{persona_response.json()['id']}/voice-profile",
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["status"] == "NEEDS_MORE_SAMPLES"


def test_voice_profile_evaluate_success_returns_ready_or_processing(client, auth_headers, created_persona):
    _, evaluate_payload = _create_profile_and_evaluate(client, auth_headers, created_persona["id"])
    assert evaluate_payload["status"] in {"READY", "PROCESSING"}


def test_user_can_confirm_voice_profile(client, auth_headers, created_persona):
    _, evaluate_payload = _create_profile_and_evaluate(client, auth_headers, created_persona["id"])
    assert evaluate_payload["status"] == "READY"

    confirm_response = client.patch(
        f"/api/v1/personas/{created_persona['id']}/voice-profile/user-confirm",
        headers=auth_headers,
        json={"review_note": "voice sounds accurate"},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["review_status"] == "USER_CONFIRMED"


def test_admin_can_approve_reject_revoke_voice_profile(
    client,
    auth_headers,
    admin_headers,
    created_persona,
):
    create_payload, evaluate_payload = _create_profile_and_evaluate(client, auth_headers, created_persona["id"])
    assert evaluate_payload["status"] == "READY"
    profile_id = create_payload["id"]

    approve_response = client.patch(
        f"/api/v1/admin/voice-profiles/{profile_id}/approve",
        headers=admin_headers,
        json={"review_note": "approved"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["review_status"] == "ADMIN_APPROVED"

    reject_response = client.patch(
        f"/api/v1/admin/voice-profiles/{profile_id}/reject",
        headers=admin_headers,
        json={"review_note": "reject for test"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["review_status"] == "REJECTED"

    revoke_response = client.patch(
        f"/api/v1/admin/voice-profiles/{profile_id}/revoke",
        headers=admin_headers,
        json={"review_note": "revoke for test"},
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "REVOKED"


def test_voice_synthesis_blocked_when_profile_not_ready(client, auth_headers, created_chat):
    response = client.post(
        f"/api/v1/chats/{created_chat['id']}/messages",
        headers=auth_headers,
        json={
            "message_type": "TEXT",
            "content": "hello",
            "generate_audio": True,
        },
    )
    assert response.status_code == 403


def test_voice_profile_and_synthesis_audit_logs_created(
    client,
    auth_headers,
    admin_headers,
    created_chat,
):
    persona_id = created_chat["persona_id"]
    create_payload, evaluate_payload = _create_profile_and_evaluate(client, auth_headers, persona_id)
    assert evaluate_payload["status"] == "READY"

    confirm_response = client.patch(
        f"/api/v1/personas/{persona_id}/voice-profile/user-confirm",
        headers=auth_headers,
        json={"review_note": "confirmed"},
    )
    assert confirm_response.status_code == 200

    message_response = client.post(
        f"/api/v1/chats/{created_chat['id']}/messages",
        headers=auth_headers,
        json={
            "message_type": "TEXT",
            "content": "generate voice",
            "generate_audio": True,
        },
    )
    assert message_response.status_code == 201

    created_log = client.get(
        "/api/v1/admin/audit-logs?action=VOICE_PROFILE_CREATED",
        headers=admin_headers,
    )
    reviewed_log = client.get(
        "/api/v1/admin/audit-logs?action=VOICE_PROFILE_REVIEWED",
        headers=admin_headers,
    )
    synthesized_log = client.get(
        "/api/v1/admin/audit-logs?action=VOICE_SYNTHESIZED",
        headers=admin_headers,
    )

    assert created_log.status_code == 200
    assert reviewed_log.status_code == 200
    assert synthesized_log.status_code == 200
    assert created_log.json()["total"] >= 1
    assert reviewed_log.json()["total"] >= 1
    assert synthesized_log.json()["total"] >= 1


def test_voice_profile_evaluate_returns_failed_when_voice_clone_provider_fails(
    client,
    auth_headers,
    created_persona,
    monkeypatch,
):
    class _FailingVoiceCloneService:
        async def create_voice_profile(self, persona_id: int, reference_audio_paths: list[str]) -> dict:
            return {
                "persona_id": persona_id,
                "provider": "openvoice",
                "model_name": "openvoice-v2",
                "status": "FAILED",
                "voice_profile_path": None,
                "error_message": "openvoice missing checkpoint",
            }

        async def synthesize_with_cloned_voice(self, text: str, voice_profile: dict, output_path: str):
            raise RuntimeError("not used in this test")

    monkeypatch.setattr(
        "app.services.persona_service.get_voice_clone_service",
        lambda: _FailingVoiceCloneService(),
    )

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
    payload = evaluate_response.json()
    assert payload["status"] == "FAILED"
    assert payload["error_message"] == "openvoice missing checkpoint"


