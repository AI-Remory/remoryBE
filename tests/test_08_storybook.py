def test_create_and_get_storybook(client, auth_headers, created_storybook):
    response = client.get(f"/api/v1/storybooks/{created_storybook['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_storybook["id"]
    assert response.json()["status"] == "GENERATED"
    assert len(response.json()["chapters"]) >= 1


def test_list_storybooks(client, auth_headers, created_storybook):
    response = client.get("/api/v1/storybooks", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_storybook_chapters(client, auth_headers, created_storybook):
    response = client.get(f"/api/v1/storybooks/{created_storybook['id']}/chapters", headers=auth_headers)
    assert response.status_code == 200
    assert [chapter["order_index"] for chapter in response.json()] == [1]


def test_regenerate_storybook(client, auth_headers, created_storybook):
    response = client.post(f"/api/v1/storybooks/{created_storybook['id']}/regenerate", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_storybook["id"]


def test_other_user_cannot_access_storybook(client, created_storybook, second_user_headers):
    response = client.get(f"/api/v1/storybooks/{created_storybook['id']}", headers=second_user_headers)
    assert response.status_code in (403, 404)
