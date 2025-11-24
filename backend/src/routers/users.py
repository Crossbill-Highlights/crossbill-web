from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.database import DatabaseSession
from src.models import User
from src.repositories import UserRepository
from src.schemas.user_schemas import UserDetailsResponse, UserRegisterRequest, UserUpdateRequest
from src.services.auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/users", tags=["users"])


# TODO: Refactor registration and login to use a service layer and some shared logic with auth.py
@router.post("/register")
async def register(register_data: UserRegisterRequest, db: DatabaseSession) -> Token:
    """
    Register a new user account.

    Creates a new user with the provided username and password.
    Returns an access token for immediate login after registration.
    """
    user_repository = UserRepository(db)

    # Check if username already exists
    existing_user = user_repository.get_by_name(register_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Hash the password and create the user
    hashed_password = hash_password(register_data.password)
    user = user_repository.create_with_password(
        name=register_data.username, hashed_password=hashed_password
    )

    db.commit()

    # Create access token for automatic login
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")  # noqa: S106


@router.get("/me")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserDetailsResponse:
    """Get the current user's profile information."""
    return UserDetailsResponse(name=current_user.name, id=current_user.id)


@router.post("/me")
async def update_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DatabaseSession,
    update_data: UserUpdateRequest,
) -> UserDetailsResponse:
    """
    Update the current user's profile.

    - To change name: provide `name` field
    - To change password: provide both `current_password` and `new_password` fields
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

    # Update name if provided
    if update_data.name is not None:
        current_user.name = update_data.name

    # Update password if provided
    if update_data.new_password is not None:
        current_user.hashed_password = hash_password(update_data.new_password)

    db.commit()
    db.refresh(current_user)

    return UserDetailsResponse(name=current_user.name, id=current_user.id)
