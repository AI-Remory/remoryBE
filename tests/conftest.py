"""Shared pytest fixtures for API integration tests."""

from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base


TEST_SQLALCHEMY_DB_URL = "sqlite://"

engine = create_engine(
    TEST_SQLALCHEMY_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _cleanup_uploads() -> None:
    uploads_root = _backend_root() / "uploads"
    if not uploads_root.exists():
        return

    for relative_dir in ("images", "voices", "photo_memories", "verifications"):
        target_dir = uploads_root / relative_dir
        if not target_dir.exists():
            continue
        for child in target_dir.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


@pytest.fixture(autouse=True)
def cleanup_uploaded_files():
    _cleanup_uploads()
    yield
    _cleanup_uploads()


@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def _create_consent(client, auth_headers, target_id, consent_type, is_consented=True, details=None):
    payload = {
        "target_id": target_id,
        "consent_type": consent_type,
        "is_consented": is_consented,
    }
    if details is not None:
        payload["details"] = details

    response = client.post("/api/v1/consents", json=payload, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_user_data():
    return {
        "email": "testuser@example.com",
        "nickname": "testuser",
        "password": "securepassword123",
    }


@pytest.fixture
def auth_token(client, test_user_data):
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def second_user(client):
    data = {
        "email": "seconduser@example.com",
        "nickname": "seconduser",
        "password": "securepassword123",
    }
    response = client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def second_user_headers(second_user):
    return {"Authorization": f"Bearer {second_user['access_token']}"}


@pytest.fixture
def admin_user(client):
    """관리자 사용자 생성"""
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    db = TestingSessionLocal()
    try:
        admin = User(
            email="admin@example.com",
            nickname="admin",
            password_hash=hash_password("adminpassword123"),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    finally:
        db.close()


@pytest.fixture
def admin_token(client, admin_user):
    """관리자 토큰"""
    from app.core.security import create_access_token
    from app.core.settings import settings

    token = create_access_token(
        subject=str(admin_user.id),
        expires_delta=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return token


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def created_target(client, auth_headers):
    response = client.post(
        "/api/v1/targets",
        json={"name": "Mom", "description": "Warm and thoughtful", "target_type": "parent"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def target_media_consents(client, auth_headers, created_target):
    target_id = created_target["id"]
    return {
        "photo": _create_consent(
            client,
            auth_headers,
            target_id,
            "photo_collection",
            details="photo upload consent",
        ),
        "voice": _create_consent(
            client,
            auth_headers,
            target_id,
            "voice_collection",
            details="voice upload consent",
        ),
    }


@pytest.fixture
def uploaded_media(client, auth_headers, created_target, target_media_consents):
    target_id = created_target["id"]
    image = client.post(
        f"/api/v1/targets/{target_id}/media",
        data={"media_type": "image"},
        files={"file": ("photo.jpg", b"fake image content", "image/jpeg")},
        headers=auth_headers,
    )
    assert image.status_code == 201

    voice = client.post(
        f"/api/v1/targets/{target_id}/media",
        data={"media_type": "voice"},
        files={"file": ("voice.mp3", b"fake audio content", "audio/mpeg")},
        headers=auth_headers,
    )
    assert voice.status_code == 201
    return {"image": image.json(), "voice": voice.json()}


@pytest.fixture
def target_persona_consent(client, auth_headers, created_target, target_media_consents):
    return _create_consent(
        client,
        auth_headers,
        created_target["id"],
        "persona_creation",
        details="persona generation consent",
    )


@pytest.fixture
def created_persona(client, auth_headers, created_target, uploaded_media, target_persona_consent, target_verification):
    response = client.post(f"/api/v1/targets/{created_target['id']}/persona", headers=auth_headers)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_chat(client, auth_headers, created_persona):
    response = client.post(
        f"/api/v1/personas/{created_persona['id']}/chats",
        json={"title": "First chat"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_interview(client, auth_headers):
    session = client.post(
        "/api/v1/interviews",
        json={"session_type": "SELF_STORY", "title": "Self story interview"},
        headers=auth_headers,
    )
    assert session.status_code == 201
    session_payload = session.json()

    question = client.post(
        f"/api/v1/interviews/{session_payload['id']}/questions",
        json={"question_type": "memory"},
        headers=auth_headers,
    )
    assert question.status_code == 201
    question_payload = question.json()

    answer = client.post(
        f"/api/v1/interviews/{session_payload['id']}/answers",
        json={"question_id": question_payload["id"], "answer_text": "A memory worth preserving."},
        headers=auth_headers,
    )
    assert answer.status_code == 201
    return {"session": session_payload, "question": question_payload, "answer": answer.json()}


@pytest.fixture
def created_photo_memory(client, auth_headers):
    response = client.post(
        "/api/v1/photo-memories",
        data={"title": "Birthday", "description": "A family birthday photo"},
        files={"file": ("birthday.jpg", b"fake image content", "image/jpeg")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_storybook(client, auth_headers, created_interview):
    response = client.post(
        "/api/v1/storybooks",
        json={"title": "My Story", "interview_session_id": created_interview["session"]["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def storybook_share_consent(client, auth_headers, created_storybook):
     return _create_consent(
         client,
         auth_headers,
         created_storybook["id"],
         "storybook_share",
         details="storybook share consent",
     )


@pytest.fixture
def target_verification(client, auth_headers, created_target):
    """Create an approved target verification for testing."""
    from app.models.target_verification import TargetVerificationRequest, VerificationStatus, VerificationType
    from datetime import datetime, UTC

    db = TestingSessionLocal()
    try:
        # Get current user ID from token
        user_response = client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = user_response.json()["id"]

        verification = TargetVerificationRequest(
            user_id=user_id,
            target_id=created_target["id"],
            verification_type=VerificationType.SELF_DECLARATION,
            status=VerificationStatus.APPROVED,
            document_file_path="test/verification.pdf",
            original_filename="verification.pdf",
            stored_filename="test_verification.pdf",
            mime_type="application/pdf",
            file_size=1024,
            submitted_at=datetime.now(UTC).replace(tzinfo=None),
            reviewed_at=datetime.now(UTC).replace(tzinfo=None),
            reviewed_by=user_id,
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        return verification
    finally:
        db.close()



