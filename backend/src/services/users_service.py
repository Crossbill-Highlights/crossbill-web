"""Service layer for user-related business logic."""

import logging
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src import schemas
from src.config import get_settings
from src.models import User
from src.repositories import UserRepository
from src.services.auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    create_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)


class UserService:
    """Service for handling user-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)

    def register_user(self, register_data: schemas.UserRegisterRequest) -> Token:
        """
        Register a new user account.

        Creates a new user with the provided email and password.
        Returns an access token for immediate login after registration.

        Args:
            register_data: User registration request containing email and password

        Returns:
            Token with access token for authentication

        Raises:
            HTTPException: If registration is disabled or email already exists
        """
        settings = get_settings()

        # Check if user registration is enabled
        if not settings.ALLOW_USER_REGISTRATIONS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User registration is currently disabled",
            )

        # Check if email already exists
        existing_user = self.user_repo.get_by_email(register_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash the password and create the user
        hashed_password = hash_password(register_data.password)
        user = self.user_repo.create_with_password(
            email=register_data.email, hashed_password=hashed_password
        )

        self.db.commit()

        # Create access token for automatic login
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        logger.info(f"Successfully registered user with email: {register_data.email}")

        return Token(access_token=access_token, token_type="bearer")  # noqa: S106

    def update_user(
        self, current_user: User, update_data: schemas.UserUpdateRequest
    ) -> schemas.UserDetailsResponse:
        """
        Update the current user's profile.

        - To change email: provide `email` field
        - To change password: provide both `current_password` and `new_password` fields

        Args:
            current_user: The currently authenticated user
            update_data: User update request containing optional email and password changes

        Returns:
            Updated user details

        Raises:
            HTTPException: If password validation fails
        """
        # Validate password change request
        if update_data.new_password is not None:
            if update_data.current_password is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required when changing password",
                )
            # Verify current password
            if not current_user.hashed_password or not verify_password(
                update_data.current_password, current_user.hashed_password
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect",
                )

        # Update email if provided
        if update_data.email is not None:
            current_user.email = update_data.email

        # Update password if provided
        if update_data.new_password is not None:
            current_user.hashed_password = hash_password(update_data.new_password)

        self.db.commit()
        self.db.refresh(current_user)

        logger.info(f"Successfully updated user {current_user.id}")

        return schemas.UserDetailsResponse(email=current_user.email, id=current_user.id)
