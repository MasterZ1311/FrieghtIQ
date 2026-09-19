import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FREIGHT IQ — Maritime Freight Intelligence & Vessel Chartering Engine"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database configuration: defaults to SQLite for immediate zero-dependency portability,
    # and automatically supports PostgreSQL (psycopg2) when configured.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./freight_iq.db"
    )

    # CORS origins for frontend Next.js application
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # Secret key for tokens/sessions
    SECRET_KEY: str = os.getenv("SECRET_KEY", "freight_iq_secret_super_key_sih26006_sail_2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
