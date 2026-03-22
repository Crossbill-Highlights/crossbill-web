"""Use case for authenticating a user with email and password."""

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
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def authenticate(self, email: str, password: str) -> tuple[User, TokenWithRefresh]:
        """
        Authenticate a user with email and password.

        Returns:
            Tuple of (authenticated user, token pair)

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        user = await self.user_repository.find_by_email(email)

        # Use constant-time comparison to prevent timing attacks
        if not user:
            self.password_service.verify_password(password, self.password_service.get_dummy_hash())
            raise InvalidCredentialsError

        if not user.hashed_password or not self.password_service.verify_password(
            password, user.hashed_password
        ):
            raise InvalidCredentialsError

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

        logger.info("user_authenticated", user_id=user.id.value, email=email)

        return user, token_pair
