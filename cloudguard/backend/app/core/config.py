from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cloudguard.db"

    # Security
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "change-me"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Detection & Response
    AUTOMATED_RESPONSE_ENABLED: bool = False
    DEMO_MODE_ENABLED: bool = True

    # Telemetry
    USE_SIMULATED_TELEMETRY: bool = True
    TELEMETRY_INTERVAL_SECONDS: int = 5

    # Application metadata
    APP_NAME: str = "CloudGuard"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
