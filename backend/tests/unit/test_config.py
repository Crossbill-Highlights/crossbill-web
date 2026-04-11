"""Tests for Settings configuration validation."""

import pytest

from src.config import Settings


def _build_settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "SECRET_KEY": "test-secret",
        "REFRESH_TOKEN_SECRET_KEY": "test-refresh-secret",
        "ADMIN_PASSWORD": "test-admin-password",
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


class TestCorsOriginsValidation:
    def test_development_empty_origins_ok(self) -> None:
        settings = _build_settings(ENVIRONMENT="development", CORS_ORIGINS=[])
        assert settings.CORS_ORIGINS == []

    def test_development_wildcard_ok(self) -> None:
        settings = _build_settings(ENVIRONMENT="development", CORS_ORIGINS=["*"])
        assert settings.CORS_ORIGINS == ["*"]

    def test_development_default_contains_localhost(self) -> None:
        settings = _build_settings(ENVIRONMENT="development")
        assert "http://localhost:5173" in settings.CORS_ORIGINS
        assert "*" not in settings.CORS_ORIGINS

    def test_production_empty_origins_rejected(self) -> None:
        with pytest.raises(ValueError, match="CORS_ORIGINS must be set"):
            _build_settings(ENVIRONMENT="production", CORS_ORIGINS=[])

    def test_production_wildcard_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not contain wildcard"):
            _build_settings(ENVIRONMENT="production", CORS_ORIGINS=["*"])

    def test_production_wildcard_mixed_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not contain wildcard"):
            _build_settings(
                ENVIRONMENT="production",
                CORS_ORIGINS=["https://example.com", "*"],
            )

    def test_production_explicit_origins_ok(self) -> None:
        settings = _build_settings(
            ENVIRONMENT="production",
            CORS_ORIGINS=["https://example.com"],
        )
        assert settings.CORS_ORIGINS == ["https://example.com"]
