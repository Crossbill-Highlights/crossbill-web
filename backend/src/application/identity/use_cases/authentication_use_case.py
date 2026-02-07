"""Use case for authentication operations."""

import structlog

from src.application.identity.protocols.password_service import PasswordServiceProtocol
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError, UserNotFoundError
from src.infrastructure.identity.services.token_service import TokenWithRefresh

logger = structlog.get_logger(__name__)


class AuthenticationUseCase:
    """Use case for authentication operations."""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        password_service: PasswordServiceProtocol,
        token_service: TokenServiceProtocol,
    ) -> None:
        """Initialize use case with dependencies."""
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service

    def authenticate_user(self, email: str, password: str) -> tuple[User, TokenWithRefresh]:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address
            password: User's plain text password

        Returns:
            Tuple of (authenticated user, token pair)

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        user = self.user_repository.find_by_email(email)

        # Use constant-time comparison to prevent timing attacks
        if not user:
            self.password_service.verify_password(password, self.password_service.get_dummy_hash())
            raise InvalidCredentialsError

        if not user.hashed_password or not self.password_service.verify_password(
            password, user.hashed_password
        ):
            raise InvalidCredentialsError

        token_pair = self.token_service.create_token_pair(user.id.value)

        logger.info("user_authenticated", user_id=user.id.value, email=email)

        return user, token_pair

    def refresh_access_token(self, refresh_token: str) -> tuple[User, TokenWithRefresh]:
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

    def get_user_by_id(self, user_id: int) -> User:
        """
        Get a user by ID (used internally by dependency injection).

        Args:
            user_id: User's ID

        Returns:
            User entity

        Raises:
            UserNotFoundError: If user is not found
        """
        user = self.user_repository.find_by_id(UserId(user_id))
        if not user:
            raise UserNotFoundError(user_id)
        return user
