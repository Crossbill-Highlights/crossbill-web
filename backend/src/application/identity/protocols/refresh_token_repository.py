"""Protocol for refresh token repository."""

from typing import Protocol

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.refresh_token import RefreshToken


class RefreshTokenRepositoryProtocol(Protocol):
    async def save(self, token: RefreshToken) -> RefreshToken: ...

    async def find_by_token_hash(self, token_hash: str) -> RefreshToken | None: ...

    async def revoke_family(self, family_id: str) -> None:
        """Revoke all tokens in a family (used on reuse detection or logout)."""
        ...

    async def revoke_all_for_user(self, user_id: UserId) -> None:
        """Revoke all refresh tokens for a user (used on logout / password change)."""
        ...

    async def delete_expired(self) -> int:
        """Delete expired tokens. Returns count of deleted rows."""
        ...
