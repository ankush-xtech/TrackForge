"""
Application configuration using Pydantic Settings.
All environment variables are validated at startup.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──
    APP_NAME: str = "WebWork Clone"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "1998"
    POSTGRES_DB: str = "webwork"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Sync URL for Alembic migrations."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ──
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── JWT Auth ──
    JWT_SECRET_KEY: str = "CHANGE-THIS-IN-PRODUCTION-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── MinIO (S3-compatible storage) ──
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_SCREENSHOTS: str = "screenshots"
    MINIO_BUCKET_AVATARS: str = "avatars"
    MINIO_BUCKET_INVOICES: str = "invoices"
    MINIO_USE_SSL: bool = False

    # ── Celery ──
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Screenshot Settings ──
    SCREENSHOT_INTERVAL_SECONDS: int = 300  # 5 minutes default
    SCREENSHOT_QUALITY: int = 70  # JPEG quality
    SCREENSHOT_MAX_WIDTH: int = 1920
    SCREENSHOT_RETENTION_DAYS: int = 90

    # ── Activity Tracking ──
    ACTIVITY_LOG_INTERVAL_SECONDS: int = 60  # Log activity every minute
    IDLE_THRESHOLD_SECONDS: int = 300  # 5 min of no input = idle

    # ── Email (SMTP) ──
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@webwork.local"
    SMTP_FROM_NAME: str = "WebWork"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
