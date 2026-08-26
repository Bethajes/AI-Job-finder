from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Ethiopian Job Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email
    EMAIL_FROM: str
    RESEND_API_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8081"]

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Local file storage fallback (used when Cloudinary is not configured)
    UPLOAD_DIR: str = "uploads"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    # Force-enable rate limiting outside production (auto-enabled in prod).
    ENABLE_RATE_LIMIT: bool = False

    # Sentry
    SENTRY_DSN: str = ""

    # Firebase Cloud Messaging (empty string disables push notifications)
    FIREBASE_CREDENTIALS_PATH: str = ""

    # Week 8: admin
    # Emails allowed to use super-admin-only operations (require_super_admin).
    SUPER_ADMIN_EMAILS: List[str] = []
    # Dashboard-stats Redis cache TTL in seconds (spec: 5-15 minutes).
    STATS_CACHE_TTL: int = 300

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
