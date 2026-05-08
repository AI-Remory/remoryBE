"""API 테스트"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


class TestAuth:
    """인증 API 테스트"""

    def test_signup(self):
        """회원가입 테스트"""
        user_data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "securepassword123"
        }
        response = client.post("/api/v1/auth/sign-up", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["access_token"]
        assert data["user"]["email"] == user_data["email"]

    def test_signup_duplicate_email(self):
        """중복 이메일 회원가입 테스트"""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "full_name": "User One",
            "password": "securepassword123"
        }
        # 첫 번째 가입
        client.post("/api/v1/auth/sign-up", json=user_data)

        # 중복 가입 시도
        user_data["username"] = "user2"
        response = client.post("/api/v1/auth/sign-up", json=user_data)
        assert response.status_code == 400

    def test_login(self):
        """로그인 테스트"""
        # 사용자 생성
        user_data = {
            "email": "logintest@example.com",
            "username": "loginuser",
            "full_name": "Login Test",
            "password": "securepassword123"
        }
        client.post("/api/v1/auth/sign-up", json=user_data)

        # 로그인
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["user"]["email"] == user_data["email"]

    def test_login_invalid_password(self):
        """잘못된 비밀번호 로그인 테스트"""
        # 사용자 생성
        user_data = {
            "email": "wrongpass@example.com",
            "username": "wrongpassuser",
            "full_name": "Wrong Pass",
            "password": "securepassword123"
        }
        client.post("/api/v1/auth/sign-up", json=user_data)

        # 잘못된 비밀번호로 로그인
        login_data = {
            "email": user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 400


class TestTarget:
    """Target API 테스트"""

    @pytest.fixture
    def auth_token(self):
        """인증 토큰 fixture"""
        user_data = {
            "email": "targettest@example.com",
            "username": "targetuser",
            "full_name": "Target Test",
            "password": "securepassword123"
        }
        response = client.post("/api/v1/auth/sign-up", json=user_data)
        return response.json()["access_token"]

    def test_create_target(self, auth_token):
        """Target 생성 테스트"""
        target_data = {
            "name": "Mom",
            "description": "My beloved mother",
            "target_type": "parent"
        }
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/targets",
            json=target_data,
            headers=headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == target_data["name"]
        assert data["id"]

    def test_list_targets(self, auth_token):
        """Target 목록 조회 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 여러 target 생성
        for i in range(3):
            target_data = {
                "name": f"Target {i+1}",
                "description": f"Description {i+1}",
                "target_type": "other"
            }
            client.post("/api/v1/targets", json=target_data, headers=headers)

        # 목록 조회
        response = client.get("/api/v1/targets", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

    def test_get_target(self, auth_token):
        """Target 상세 조회 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Target 생성
        target_data = {
            "name": "Dad",
            "description": "My beloved dad",
            "target_type": "parent"
        }
        create_response = client.post(
            "/api/v1/targets",
            json=target_data,
            headers=headers
        )
        target_id = create_response.json()["id"]

        # 조회
        response = client.get(f"/api/v1/targets/{target_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == target_data["name"]
        assert data["id"] == target_id

    def test_update_target(self, auth_token):
        """Target 수정 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Target 생성
        target_data = {
            "name": "Sister",
            "description": "Original description",
            "target_type": "other"
        }
        create_response = client.post(
            "/api/v1/targets",
            json=target_data,
            headers=headers
        )
        target_id = create_response.json()["id"]

        # 수정
        update_data = {
            "name": "Sister Updated",
            "description": "Updated description"
        }
        response = client.put(
            f"/api/v1/targets/{target_id}",
            json=update_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    def test_delete_target(self, auth_token):
        """Target 삭제 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Target 생성
        target_data = {
            "name": "To Delete",
            "description": "This will be deleted",
            "target_type": "other"
        }
        create_response = client.post(
            "/api/v1/targets",
            json=target_data,
            headers=headers
        )
        target_id = create_response.json()["id"]

        # 삭제
        response = client.delete(
            f"/api/v1/targets/{target_id}",
            headers=headers
        )
        assert response.status_code == 204

