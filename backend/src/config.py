"""Application configuration."""

import logging
import sys
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import structlog
from pydantic import computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Path constants - calculated once at module load
BACKEND_ROOT = Path(__file__).parent.parent.resolve()
BOOK_FILES_DIR = BACKEND_ROOT / "book-files"
BOOK_COVERS_DIR = BOOK_FILES_DIR / "book-covers"
EPUBS_DIR = BOOK_FILES_DIR / "epubs"
PDFS_DIR = BOOK_FILES_DIR / "pdfs"


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql://crossbill:crossbill_dev_password@localhost:5432/crossbill"

    SECRET_KEY: str = ""

    # API (constants, not from env)
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "crossbill API"
    VERSION: str = "0.1.0"

    # Environment
    ENVIRONMENT: Literal["development", "production", "test"] = "development"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Admin setup (for first-time initialization)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"  # noqa: S105

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_TOKEN_SECRET_KEY: str = ""
    COOKIE_SECURE: bool = True
    PASSWORD_PEPPER: str = ""

    # Registration
    ALLOW_USER_REGISTRATIONS: bool = True

    # Reading sessions
    MINIMUM_READING_SESSION_DURATION: int = 120

    # AI configuration
    AI_PROVIDER: (
        Literal["ollama"] | Literal["openai"] | Literal["anthropic"] | Literal["google"] | None
    ) = None
    AI_MODEL_NAME: str | None = None

    # ollama
    OPENAI_BASE_URL: str | None = None
    # openai
    OPENAI_API_KEY: str | None = None
    # anthropic
    ANTHROPIC_API_KEY: str | None = None
    # google
    GEMINI_API_KEY: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ai_enabled(self) -> bool:
        """Whether AI features are enabled."""
        return self.AI_PROVIDER is not None

    @field_validator("ADMIN_PASSWORD", mode="after")
    @classmethod
    def strip_admin_password(cls, value: str) -> str:
        """Strip whitespace from admin password."""
        return value.strip()

    @model_validator(mode="after")
    def validate_ai_provider_config(self) -> "Settings":
        """Validate AI provider configuration."""
        if self.AI_PROVIDER is not None and self.AI_MODEL_NAME is None:
            msg = "AI_MODEL_NAME is required when AI_PROVIDER is 'openai'"
            raise ValueError(msg)

        if self.AI_PROVIDER == "ollama" and not self.OPENAI_BASE_URL:
            msg = "OPENAI_BASE_URL is required when AI_PROVIDER is 'ollama'"
            raise ValueError(msg)
        if self.AI_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            msg = "OPENAI_API_KEY is required when AI_PROVIDER is 'openai'"
            raise ValueError(msg)
        if self.AI_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            msg = "ANTHROPIC_API_KEY is required when AI_PROVIDER is 'anthropic'"
            raise ValueError(msg)
        if self.AI_PROVIDER == "google" and not self.GEMINI_API_KEY:
            msg = "GEMINI_API_KEY is required when AI_PROVIDER is 'google'"
            raise ValueError(msg)
        return self


def configure_logging(environment: str = "development") -> None:
    """Configure structured logging with structlog."""
    # Determine if we should use JSON output (production) or console output (dev)
    use_json = environment == "production"

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if environment == "development" else logging.INFO,
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
