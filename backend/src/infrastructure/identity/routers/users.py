import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.application.identity.services.user_profile_service import UserProfileService
from src.application.identity.services.user_registration_service import UserRegistrationService
from src.database import DatabaseSession
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import (
    EmailAlreadyExistsError,
    PasswordVerificationError,
    RegistrationDisabledError,
)
from src.exceptions import CrossbillError
from src.infrastructure.identity.auth.token_service import TokenWithRefresh
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.identity.routers.auth import set_refresh_cookie
from src.infrastructure.identity.schemas import (
    UserDetailsResponse,
    UserRegisterRequest,
    UserUpdateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register")
@limiter.limit("5/minute")  # type: ignore[misc]
async def register(
    request: Request, response: Response, register_data: UserRegisterRequest, db: DatabaseSession
) -> TokenWithRefresh:
    """
    Register a new user account.

    Creates a new user with the provided email and password.
    Returns token pair for immediate login after registration.
    """
    try:
        service = UserRegistrationService(db)
        _, token_pair = service.register_user(register_data.email, register_data.password)
        set_refresh_cookie(response, token_pair.refresh_token)
        return token_pair
    except RegistrationDisabledError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User registration is currently disabled",
        ) from None
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        ) from None
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        logger.error(f"Failed to register user: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get("/me")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserDetailsResponse:
    """Get the current user's profile information."""
    return UserDetailsResponse(email=current_user.email, id=current_user.id.value)


@router.post("/me")
async def update_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: DatabaseSession,
    update_data: UserUpdateRequest,
) -> UserDetailsResponse:
    """
    Update the current user's profile.

    - To change email: provide `email` field
    - To change password: provide both `current_password` and `new_password` fields
    """
    try:
        service = UserProfileService(db)
        user = service.update_user(
            user_id=current_user.id.value,
            email=update_data.email,
            current_password=update_data.current_password,
            new_password=update_data.new_password,
        )
        return UserDetailsResponse(email=user.email, id=user.id.value)
    except PasswordVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        ) from None
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        logger.error(f"Failed to update user {current_user.id.value}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
