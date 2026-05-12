import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """프로젝트 전역 설정"""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # App
    APP_NAME: str = "Remory API"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database
    MYSQL_USER: str = "remory"
    MYSQL_PASSWORD: str = "password"
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "remory_db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Speech-to-Text
    STT_PROVIDER: str = "mock"
    WHISPER_MODEL_SIZE: str = "base"

    # Text-to-Speech
    TTS_PROVIDER: str = "mock"

    # Voice Cloning
    VOICE_CLONE_PROVIDER: str = "mock"
    OPENVOICE_CHECKPOINT_PATH: str = ""
    VOICE_SAMPLE_MIN_COUNT: int = 1
    VOICE_SAMPLE_MIN_TOTAL_DURATION_MS: int = 100
    VOICE_SAMPLE_MIN_FILE_SIZE_BYTES: int = 1024
    VOICE_PROFILE_MIN_QUALITY_SCORE: float = 0.5

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB

    # Rate Limiting & Usage Limits
    MONTHLY_USER_VOICE_GENERATION_LIMIT: int = 1000  # Voice synthesis calls per month
    MONTHLY_PERSONA_VOICE_GENERATION_LIMIT: int = 500  # Per persona per month
    MONTHLY_USER_STT_REQUEST_LIMIT: int = 500  # STT requests per month
    MONTHLY_USER_VOICE_CALL_SECONDS_LIMIT: int = 3600  # 1 hour per month
    RATE_LIMIT_REQUESTS_PER_MINUTE_DEFAULT: int = 60  # Default: 60 requests per minute
    RATE_LIMIT_REQUESTS_PER_MINUTE_VOICE: int = 10  # Voice endpoints: 10 per minute
    VOICE_WS_MAX_ACTIVE_CONNECTIONS_PER_USER: int = 2
    VOICE_WS_MAX_UTTERANCES_PER_MINUTE: int = 20
    VOICE_WS_MAX_CHUNK_BYTES: int = 262144
    VOICE_WS_MAX_CHUNKS_PER_UTTERANCE: int = 100

    @property
    def DATABASE_URL(self) -> str:
        """MySQL 연결 문자열 생성"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"


settings = Settings()
