def test_register(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "register@example.com",
            "nickname": "registeruser",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["access_token"]
    assert payload["refresh_token"]
    assert payload["user"]["email"] == "register@example.com"
    assert payload["user"]["role"] == "USER"


def test_login(client, test_user_data):
    client.post("/api/v1/auth/register", json=test_user_data)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_me(client, auth_headers, test_user_data):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user_data["email"]
    assert response.json()["role"] == "USER"


def test_me_returns_admin_role(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"
