"""Tests for RefreshToken domain entity."""

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.common.value_objects.ids import RefreshTokenId, UserId
from src.domain.identity.entities.refresh_token import RefreshToken


def _create(**overrides):
    defaults = {
        "jti": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": UserId(1),
        "family_id": "660e8400-e29b-41d4-a716-446655440000",
        "expires_at": datetime.now(UTC) + timedelta(days=30),
    }
    defaults.update(overrides)
    return RefreshToken.create(**defaults)


class TestRefreshTokenCreate:
    def test_create_sets_fields(self) -> None:
        token = _create()
        assert token.id == RefreshTokenId(0)
        assert token.jti == "550e8400-e29b-41d4-a716-446655440000"
        assert token.user_id == UserId(1)
        assert token.family_id == "660e8400-e29b-41d4-a716-446655440000"
        assert token.revoked_at is None

    def test_create_with_id_reconstitutes(self) -> None:
        now = datetime.now(UTC)
        token = RefreshToken.create_with_id(
            id=RefreshTokenId(42),
            jti="abc",
            user_id=UserId(1),
            family_id="def",
            revoked_at=None,
            expires_at=now + timedelta(days=30),
            created_at=now,
        )
        assert token.id == RefreshTokenId(42)
        assert token.jti == "abc"
        assert token.created_at == now


class TestRefreshTokenRevoke:
    def test_revoke_sets_revoked_at(self) -> None:
        token = _create()
        assert token.revoked_at is None
        token.revoke()
        assert token.revoked_at is not None

    def test_is_revoked(self) -> None:
        token = _create()
        assert not token.is_revoked
        token.revoke()
        assert token.is_revoked

    def test_is_expired(self) -> None:
        token = _create(expires_at=datetime.now(UTC) - timedelta(hours=1))
        assert token.is_expired

    def test_is_not_expired(self) -> None:
        token = _create(expires_at=datetime.now(UTC) + timedelta(days=30))
        assert not token.is_expired
