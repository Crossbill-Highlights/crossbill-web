"""Application configuration."""

import logging
import os
import sys
from collections.abc import Callable
from functools import lru_cache
from typing import Any, ClassVar, Literal

import structlog
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://crossbill:crossbill_dev_password@localhost:5432/crossbill",
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "")

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "crossbill API"
    VERSION: str = "0.1.0"

    # Environment
    ENVIRONMENT: Literal["development", "production", "test"] = os.getenv(
        "ENVIRONMENT", "development"
    )  # type: ignore[assignment]

    # CORS
    CORS_ORIGINS: ClassVar[list[str]] = (
        os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") != "*" else ["*"]
    )

    # Admin setup (for first-time initialization)
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin").strip()

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    REFRESH_TOKEN_SECRET_KEY: str = os.getenv("REFRESH_TOKEN_SECRET_KEY", "")
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"

    # Registration
    ALLOW_USER_REGISTRATIONS: bool = os.getenv("ALLOW_USER_REGISTRATIONS", "true").lower() in (
        "true",
        "1",
        "yes",
    )


def configure_logging(environment: str = "development") -> None:
    """Configure structured logging with structlog."""
    # Determine if we should use JSON output (production) or console output (dev)
    use_json = environment == "production"

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog
    processors: list[Callable[..., Any]] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if use_json:
        # Production: JSON output
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: Console output with colors
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
