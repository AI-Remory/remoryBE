def test_create_and_get_target(client, auth_headers, created_target):
    response = client.get(f"/api/v1/targets/{created_target['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_target["id"]
    assert response.json()["name"] == created_target["name"]


def test_list_targets(client, auth_headers, created_target):
    response = client.get("/api/v1/targets", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == created_target["id"]


def test_other_user_cannot_access_target(client, created_target, second_user_headers):
    response = client.get(f"/api/v1/targets/{created_target['id']}", headers=second_user_headers)
    assert response.status_code in (403, 404)
