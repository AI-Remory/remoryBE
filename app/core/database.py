from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.settings import settings

# SQLAlchemy 2.x 스타일
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # 연결 풀 연결 상태 확인
    pool_size=10,
    max_overflow=20,
    connect_args={"charset": "utf8mb4"},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """의존성: DB 세션 제공"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

