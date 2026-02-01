"""Application service for user profile management."""

import structlog
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import PasswordVerificationError, UserNotFoundError
from src.infrastructure.identity.auth.password_service import hash_password, verify_password
from src.infrastructure.identity.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class UserProfileService:
    """Application service for user profile operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.user_repository = UserRepository(db)

    def update_user(
        self,
        user_id: int,
        email: str | None = None,
        current_password: str | None = None,
        new_password: str | None = None,
    ) -> User:
        """
        Update the user's profile.

        Args:
            user_id: ID of the user to update
            email: New email address (optional)
            current_password: Current password for verification (required if changing password)
            new_password: New password (optional)

        Returns:
            Updated user entity

        Raises:
            UserNotFoundError: If user is not found
            PasswordVerificationError: If current_password is incorrect
            ValidationError: If email is invalid or current_password not provided when required
        """
        # Load user
        user = self.user_repository.find_by_id(UserId(user_id))
        if not user:
            raise UserNotFoundError(user_id)

        # Update email if provided
        if email is not None:
            user.update_email(email)

        # Update password if provided
        if new_password is not None:
            # Validate current password is provided
            if current_password is None:
                raise PasswordVerificationError

            # Verify current password
            if not user.hashed_password or not verify_password(
                current_password, user.hashed_password
            ):
                raise PasswordVerificationError

            # Hash and update password
            hashed_password = hash_password(new_password)
            user.update_password(hashed_password)

        # Save user
        user = self.user_repository.save(user)
        self.db.commit()

        logger.info("user_profile_updated", user_id=user_id)

        return user
