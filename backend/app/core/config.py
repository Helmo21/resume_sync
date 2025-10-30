from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ResumeSync API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # LinkedIn OAuth (deprecated - no longer used)
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: Optional[str] = None

    # Apify (LinkedIn Profile Scraper)
    APIFY_API_TOKEN: Optional[str] = None

    # OpenRouter (AI Model Provider)
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "resumesync-pdfs"

    # Frontend & Backend URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
