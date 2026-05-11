def test_create_target_consent_and_list(client, auth_headers, created_target):
    target_id = created_target["id"]

    created = client.post(
        "/api/v1/consents",
        json={
            "target_id": target_id,
            "consent_type": "photo_collection",
            "is_consented": True,
            "details": "photo upload consent",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["target_id"] == target_id
    assert payload["consent_type"] == "photo_collection"
    assert payload["is_consented"] is True

    listed = client.get("/api/v1/consents", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == payload["id"]


def test_create_global_storybook_share_consent_without_target(client, auth_headers):
    response = client.post(
        "/api/v1/consents",
        json={
            "target_id": None,
            "consent_type": "storybook_share",
            "is_consented": True,
            "details": "storybook share consent",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["target_id"] is None
    assert payload["consent_type"] == "storybook_share"


def test_other_user_cannot_create_consent_for_target(client, created_target, second_user_headers):
    response = client.post(
        "/api/v1/consents",
        json={
            "target_id": created_target["id"],
            "consent_type": "persona_creation",
            "is_consented": True,
        },
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)


