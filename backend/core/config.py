"""Application configuration - Pydantic Settings pattern from CompareGPT."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    APP_NAME: str = "Intelligence Orchestrator - Targeting System"
    APP_VERSION: str = "0.1.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./backend/data/targeting.db"

    SSO_VALIDATE_URL: str = "https://comparegpt.io/api/sso/validate"
    SSO_LOGIN_URL: str = "https://comparegpt.io/sso/login"
    SSO_LOGOUT_URL: str = "https://comparegpt.io/sso/logout"

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://orche.platformai.org",
    ]

    DOMAIN: str = "orche.platformai.org"
    SERVER_IP: str = "34.63.169.185"

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    MAINTENANCE_MODE: bool = False
    MAINTENANCE_MESSAGE: str = "System under maintenance. Please try again later."

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
