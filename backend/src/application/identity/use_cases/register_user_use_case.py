"""Use case for user registration."""

import uuid

import structlog

from src.application.identity.protocols.password_service import PasswordServiceProtocol
from src.application.identity.protocols.refresh_token_repository import (
    RefreshTokenRepositoryProtocol,
)
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.identity.entities.refresh_token import RefreshToken
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
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def register_user(self, email: str, password: str) -> tuple[User, TokenWithRefresh]:
        """
        Register a new user account.

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
        user = await self.user_repository.save(user)
        token_pair = self.token_service.create_token_pair(user.id.value)

        # Store refresh token record with a new family
        token_hash = self.token_service.hash_token(token_pair.refresh_token)
        record = RefreshToken.create(
            user_id=user.id,
            token_hash=token_hash,
            family_id=str(uuid.uuid4()),
            expires_at=self.token_service.get_refresh_token_expiry(),
        )
        await self.refresh_token_repository.save(record)

        logger.info("user_registered", user_id=user.id.value, email=email)

        return user, token_pair
