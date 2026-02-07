"""Use case for user registration."""

import structlog

from src.application.identity.protocols.password_service import PasswordServiceProtocol
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import RegistrationDisabledError
from src.feature_flags import is_user_registrations_enabled
from src.infrastructure.identity.services.token_service import TokenWithRefresh

logger = structlog.get_logger(__name__)


class RegisterUserUseCase:
    """Use case for user registration operations."""

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

    def register_user(self, email: str, password: str) -> tuple[User, TokenWithRefresh]:
        """
        Register a new user account.

        Args:
            email: User's email address
            password: User's plain text password (will be hashed)

        Returns:
            Tuple of (created user, token pair for immediate login)

        Raises:
            RegistrationDisabledError: If registration is disabled via feature flag
            EmailAlreadyExistsError: If email is already registered
        """
        if not is_user_registrations_enabled():
            raise RegistrationDisabledError

        hashed_password = self.password_service.hash_password(password)

        user = User.create(email=email, hashed_password=hashed_password)
        user = self.user_repository.save(user)
        token_pair = self.token_service.create_token_pair(user.id.value)

        logger.info("user_registered", user_id=user.id.value, email=email)

        return user, token_pair
