"""Application service for authentication operations."""

import structlog
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError, UserNotFoundError
from src.infrastructure.identity.auth.password_service import get_dummy_hash, verify_password
from src.infrastructure.identity.auth.token_service import (
    TokenWithRefresh,
    create_token_pair,
    verify_refresh_token,
)
from src.infrastructure.identity.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class AuthenticationService:
    """Application service for authentication operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.user_repository = UserRepository(db)

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
        # Find user by email
        user = self.user_repository.find_by_email(email)

        # Use constant-time comparison to prevent timing attacks
        if not user:
            # Use dummy hash to make timing consistent
            verify_password(password, get_dummy_hash())
            raise InvalidCredentialsError

        # Verify password
        if not user.hashed_password or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError

        # Create token pair
        token_pair = create_token_pair(user.id.value)

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
        # Verify refresh token
        user_id = verify_refresh_token(refresh_token)
        if user_id is None:
            raise InvalidCredentialsError

        # Load user
        user = self.user_repository.find_by_id(UserId(user_id))
        if not user:
            raise InvalidCredentialsError

        # Create new token pair
        token_pair = create_token_pair(user.id.value)

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
