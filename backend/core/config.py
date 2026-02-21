"""Application configuration — Pydantic Settings pattern from CompareGPT."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    APP_NAME: str = "Intelligence Orchestrator - Targeting System"
    APP_VERSION: str = "0.2.0"
    APP_PORT: int = 8000
    DEBUG: bool = False

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./backend/data/targeting.db"

    SSO_VALIDATE_URL: str = "https://auth.comparegpt.io/sso/validate"

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://orche.platformai.org",
    ]

    DOMAIN: str = "orche.platformai.org"
    SERVER_IP: str = "34.63.169.185"

    LOG_LEVEL: str = "INFO"

    MAINTENANCE_MODE: bool = False
    MAINTENANCE_MESSAGE: str = "System under maintenance."

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
