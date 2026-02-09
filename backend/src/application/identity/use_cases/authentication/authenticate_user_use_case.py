"""Use case for authenticating a user with email and password."""

import structlog

from src.application.identity.protocols.password_service import PasswordServiceProtocol
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError
from src.infrastructure.identity.services.token_service import TokenWithRefresh

logger = structlog.get_logger(__name__)


class AuthenticateUserUseCase:
    """Use case for authenticating a user with email and password."""

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

    def authenticate(self, email: str, password: str) -> tuple[User, TokenWithRefresh]:
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
