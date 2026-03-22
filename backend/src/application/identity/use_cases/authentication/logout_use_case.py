"""Use case for logging out by revoking refresh token family."""

import structlog

from src.application.identity.protocols.refresh_token_repository import (
    RefreshTokenRepositoryProtocol,
)
from src.application.identity.protocols.token_service import TokenServiceProtocol

logger = structlog.get_logger(__name__)


class LogoutUseCase:
    """Use case for revoking refresh tokens on logout."""

    def __init__(
        self,
        token_service: TokenServiceProtocol,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def logout(self, raw_refresh_token: str) -> None:
        """Revoke the token family associated with the given refresh token."""
        user_id = self.token_service.verify_refresh_token(raw_refresh_token)
        if user_id is None:
            return

        token_hash = self.token_service.hash_token(raw_refresh_token)
        record = await self.refresh_token_repository.find_by_token_hash(token_hash)
        if record:
            await self.refresh_token_repository.revoke_family(record.family_id)
            logger.info("logout_tokens_revoked", user_id=user_id, family_id=record.family_id)
