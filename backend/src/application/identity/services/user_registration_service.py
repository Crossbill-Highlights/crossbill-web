"""Application service for user registration."""

import structlog
from sqlalchemy.orm import Session

from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import RegistrationDisabledError
from src.feature_flags import is_user_registrations_enabled
from src.infrastructure.identity.auth.password_service import hash_password
from src.infrastructure.identity.auth.token_service import TokenWithRefresh, create_token_pair
from src.infrastructure.identity.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class UserRegistrationService:
    """Application service for user registration operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.user_repository = UserRepository(db)

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
        # Check feature flag
        if not is_user_registrations_enabled():
            raise RegistrationDisabledError

        # Hash password
        hashed_password = hash_password(password)

        # Create user entity
        user = User.create(email=email, hashed_password=hashed_password)

        # Save user (will raise EmailAlreadyExistsError if email exists)
        user = self.user_repository.save(user)
        self.db.commit()

        # Create token pair for automatic login
        token_pair = create_token_pair(user.id.value)

        logger.info("user_registered", user_id=user.id.value, email=email)

        return user, token_pair
