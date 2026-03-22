"""Refresh token entity for token rotation."""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import RefreshTokenId, UserId


@dataclass
class RefreshToken(Entity[RefreshTokenId]):
    """
    Refresh token entity for tracking server-side refresh token state.

    Supports token rotation with reuse detection via token families.
    A token family groups all tokens in a rotation chain. When a revoked
    token is presented, the entire family is revoked to prevent stolen
    token replay attacks.
    """

    id: RefreshTokenId
    user_id: UserId
    token_hash: str
    family_id: str
    expires_at: datetime
    revoked_at: datetime | None = None
    created_at: datetime | None = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

    def revoke(self) -> None:
        """Mark this token as revoked."""
        self.revoked_at = datetime.now(UTC)

    @classmethod
    def create(
        cls,
        user_id: UserId,
        token_hash: str,
        family_id: str,
        expires_at: datetime,
    ) -> "RefreshToken":
        return cls(
            id=RefreshTokenId.generate(),
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
