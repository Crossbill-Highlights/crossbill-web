"""RefreshToken entity for token rotation tracking."""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import RefreshTokenId, UserId


@dataclass
class RefreshToken(Entity[RefreshTokenId]):
    """
    Tracks a refresh token for rotation and replay detection.

    Each token belongs to a family (one per login session).
    When rotated, the old token is revoked and a new one is created
    in the same family. Replaying a revoked token revokes the entire family.
    """

    id: RefreshTokenId
    jti: str
    user_id: UserId
    family_id: str
    revoked_at: datetime | None
    expires_at: datetime
    created_at: datetime | None = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return self.expires_at < datetime.now(UTC)

    def revoke(self) -> None:
        self.revoked_at = datetime.now(UTC)

    @classmethod
    def create(
        cls,
        jti: str,
        user_id: UserId,
        family_id: str,
        expires_at: datetime,
    ) -> "RefreshToken":
        return cls(
            id=RefreshTokenId.generate(),
            jti=jti,
            user_id=user_id,
            family_id=family_id,
            revoked_at=None,
            expires_at=expires_at,
        )

    @classmethod
    def create_with_id(
        cls,
        id: RefreshTokenId,
        jti: str,
        user_id: UserId,
        family_id: str,
        revoked_at: datetime | None,
        expires_at: datetime,
        created_at: datetime,
    ) -> "RefreshToken":
        return cls(
            id=id,
            jti=jti,
            user_id=user_id,
            family_id=family_id,
            revoked_at=revoked_at,
            expires_at=expires_at,
            created_at=created_at,
        )
