"""pytest 설정 및 공통 fixture"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# 테스트 DB (SQLite 인메모리)
TEST_SQLALCHEMY_DB_URL = "sqlite:///:memory:"

from app.models import Base
from app.core.database import get_db
from app.main import app

# 테스트 DB 엔진
engine = create_engine(
    TEST_SQLALCHEMY_DB_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """DB 의존성 재정의"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """테스트 DB fixture"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """테스트 클라이언트 fixture"""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

