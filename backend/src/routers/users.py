import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database import DatabaseSession
from src.exceptions import CrossbillError
from src.models import User
from src.routers.auth import _set_refresh_cookie
from src.schemas.user_schemas import UserDetailsResponse, UserRegisterRequest, UserUpdateRequest
from src.services.auth_service import TokenWithRefresh, get_current_user
from src.services.users_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register")
@limiter.limit("5/minute")
async def register(
    request: Request, response: Response, register_data: UserRegisterRequest, db: DatabaseSession
) -> TokenWithRefresh:
    """
    Register a new user account.

    Creates a new user with the provided email and password.
    Returns token pair for immediate login after registration.
    """
    try:
        service = UserService(db)
        token_pair = service.register_user(register_data)
        _set_refresh_cookie(response, token_pair.refresh_token)
        return token_pair
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
    return UserDetailsResponse(email=current_user.email, id=current_user.id)


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
        service = UserService(db)
        return service.update_user(current_user, update_data)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        logger.error(f"Failed to update user {current_user.id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
