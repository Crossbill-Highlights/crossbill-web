"""Use case for refreshing access token with rotation and reuse detection."""

import structlog

from src.application.identity.protocols.refresh_token_repository import (
    RefreshTokenRepositoryProtocol,
)
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError, RefreshTokenReuseError
from src.infrastructure.identity.services.token_service import TokenWithRefresh

logger = structlog.get_logger(__name__)


class RefreshAccessTokenUseCase:
    """Use case for refreshing access token with token rotation."""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        token_service: TokenServiceProtocol,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def refresh_token(self, raw_refresh_token: str) -> tuple[User, TokenWithRefresh]:
        """
        Refresh access token using a refresh token.

        Implements token rotation: the old refresh token is revoked and a new
        one is issued in the same family. If a revoked token is presented,
        the entire family is revoked (reuse detection).

        Raises:
            InvalidCredentialsError: If token is invalid or user not found
            RefreshTokenReuseError: If a revoked token is replayed
        """
        # 1. Verify JWT signature and expiry
        user_id = self.token_service.verify_refresh_token(raw_refresh_token)
        if user_id is None:
            raise InvalidCredentialsError

        # 2. Look up server-side record by token hash
        token_hash = self.token_service.hash_token(raw_refresh_token)
        record = await self.refresh_token_repository.find_by_token_hash(token_hash)

        if record is None:
            raise InvalidCredentialsError

        # 3. Reuse detection: if this token was already revoked, someone is
        #    replaying a stolen token — revoke the entire family
        if record.is_revoked:
            await self.refresh_token_repository.revoke_family(record.family_id)
            logger.warning(
                "refresh_token_reuse_detected",
                user_id=user_id,
                family_id=record.family_id,
            )
            raise RefreshTokenReuseError(record.family_id)

        # 4. Revoke the current token (it's being rotated out)
        await self.refresh_token_repository.revoke_family(record.family_id)

        # 5. Verify user still exists
        user = await self.user_repository.find_by_id(UserId(user_id))
        if not user:
            raise InvalidCredentialsError

        # 6. Issue new token pair in the same family
        token_pair = self.token_service.create_token_pair(user.id.value)
        new_hash = self.token_service.hash_token(token_pair.refresh_token)

        new_record = RefreshToken.create(
            user_id=user.id,
            token_hash=new_hash,
            family_id=record.family_id,
            expires_at=self.token_service.get_refresh_token_expiry(),
        )
        await self.refresh_token_repository.save(new_record)

        logger.info("access_token_refreshed", user_id=user.id.value, family_id=record.family_id)

        return user, token_pair
