"""Application configuration."""

import os
from functools import lru_cache
from typing import ClassVar, Literal


class Settings:
    """Application settings."""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./inkwell.db")

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Inkwell API"
    VERSION: str = "0.1.0"

    # Environment
    ENVIRONMENT: Literal["development", "production", "test"] = os.getenv(
        "ENVIRONMENT", "development"
    )  # type: ignore[assignment]

    # CORS
    CORS_ORIGINS: ClassVar[list[str]] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
