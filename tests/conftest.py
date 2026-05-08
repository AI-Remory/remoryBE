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

    for relative_dir in ("images", "voices", "photo_memories"):
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
def created_target(client, auth_headers):
    response = client.post(
        "/api/v1/targets",
        json={"name": "Mom", "description": "Warm and thoughtful", "target_type": "parent"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def uploaded_media(client, auth_headers, created_target):
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
def created_persona(client, auth_headers, created_target, uploaded_media):
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
