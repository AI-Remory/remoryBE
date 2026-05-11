def test_create_share_link_and_public_read(client, auth_headers, created_storybook, storybook_share_consent):
    response = client.post(
        f"/api/v1/storybooks/{created_storybook['id']}/share-links",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 201
    share_link = response.json()
    assert share_link["is_active"] is True

    public_response = client.get(f"/api/v1/share/{share_link['token']}")
    assert public_response.status_code == 200
    payload = public_response.json()
    assert payload["title"] == created_storybook["title"]
    assert "owner_id" not in payload
    assert "file_path" not in payload


def test_disable_share_link_blocks_public_read(client, auth_headers, created_storybook, storybook_share_consent):
    share_link = client.post(
        f"/api/v1/storybooks/{created_storybook['id']}/share-links",
        json={},
        headers=auth_headers,
    ).json()
    response = client.patch(f"/api/v1/share-links/{share_link['id']}/disable", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    blocked = client.get(f"/api/v1/share/{share_link['token']}")
    assert blocked.status_code == 403


def test_create_group_add_member_and_share_storybook(
    client,
    auth_headers,
    second_user,
    second_user_headers,
    created_storybook,
    storybook_share_consent,
):
    group_response = client.post(
        "/api/v1/groups",
        json={"name": "Family", "description": "Family memories"},
        headers=auth_headers,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    member_response = client.post(
        f"/api/v1/groups/{group['id']}/members",
        json={"user_id": second_user["user"]["id"], "role": "MEMBER"},
        headers=auth_headers,
    )
    assert member_response.status_code == 201
    assert member_response.json()["role"] == "MEMBER"

    share_response = client.post(
        f"/api/v1/groups/{group['id']}/storybooks/{created_storybook['id']}",
        headers=auth_headers,
    )
    assert share_response.status_code == 201

    group_storybooks = client.get(f"/api/v1/groups/{group['id']}/storybooks", headers=second_user_headers)
    assert group_storybooks.status_code == 200
    assert group_storybooks.json()[0]["title"] == created_storybook["title"]
    assert "file_path" not in group_storybooks.json()[0]


def test_share_link_requires_consent(client, created_storybook, auth_headers):
    response = client.post(
        f"/api/v1/storybooks/{created_storybook['id']}/share-links",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_group_share_requires_consent(client, auth_headers, created_storybook):
    group_response = client.post(
        "/api/v1/groups",
        json={"name": "Family", "description": "Family memories"},
        headers=auth_headers,
    )
    assert group_response.status_code == 201
    group = group_response.json()

    response = client.post(
        f"/api/v1/groups/{group['id']}/storybooks/{created_storybook['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_other_user_cannot_create_share_link(client, created_storybook, second_user_headers):
    response = client.post(
        f"/api/v1/storybooks/{created_storybook['id']}/share-links",
        json={},
        headers=second_user_headers,
    )
    assert response.status_code in (403, 404)
