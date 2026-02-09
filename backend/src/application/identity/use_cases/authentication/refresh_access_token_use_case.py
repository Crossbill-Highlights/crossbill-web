"""Use case for refreshing access token using a refresh token."""

import structlog

from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError
from src.infrastructure.identity.services.token_service import TokenWithRefresh

logger = structlog.get_logger(__name__)


class RefreshAccessTokenUseCase:
    """Use case for refreshing access token using a refresh token."""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        token_service: TokenServiceProtocol,
    ) -> None:
        """Initialize use case with dependencies."""
        self.user_repository = user_repository
        self.token_service = token_service

    def refresh_token(self, refresh_token: str) -> tuple[User, TokenWithRefresh]:
        """
        Refresh access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (user, new token pair)

        Raises:
            InvalidCredentialsError: If refresh token is invalid or user not found
        """
        user_id = self.token_service.verify_refresh_token(refresh_token)
        if user_id is None:
            raise InvalidCredentialsError

        user = self.user_repository.find_by_id(UserId(user_id))
        if not user:
            raise InvalidCredentialsError

        token_pair = self.token_service.create_token_pair(user.id.value)

        logger.info("access_token_refreshed", user_id=user.id.value)

        return user, token_pair
