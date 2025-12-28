import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette import status

from src.config import get_settings
from src.database import DatabaseSession
from src.repositories import UserRepository
from src.services.auth_service import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    TokenWithRefresh,
    authenticate_user,
    create_token_pair,
    verify_refresh_token,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()


class RefreshTokenRequest(BaseModel):
    """Request body for refresh token (used by plugins)."""

    refresh_token: str | None = None


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an httpOnly cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path="/api/v1/auth",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert days to seconds
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path="/api/v1/auth",
    )


@router.post("/login")
@limiter.limit("5/minute")  # type: ignore[misc]
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DatabaseSession,
) -> TokenWithRefresh:
    # OAuth2PasswordRequestForm uses 'username' field, but we use it for email
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_pair = create_token_pair(user.id)
    set_refresh_cookie(response, token_pair.refresh_token)
    return token_pair


@router.post("/refresh")
@limiter.limit("10/minute")  # type: ignore[misc]
async def refresh(
    request: Request,
    response: Response,
    db: DatabaseSession,
    body: RefreshTokenRequest | None = None,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> TokenWithRefresh:
    """
    Refresh the access token using a refresh token.

    The refresh token can be provided either:
    - In an httpOnly cookie (for web clients)
    - In the request body (for plugin clients)
    """
    # Try cookie first, then body
    token = refresh_token
    if not token and body and body.refresh_token:
        token = body.refresh_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    user_id = verify_refresh_token(token)
    if user_id is None:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify user still exists
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    token_pair = create_token_pair(user.id)
    set_refresh_cookie(response, token_pair.refresh_token)
    return token_pair


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """
    Log out by clearing the refresh token cookie.

    Note: This only clears the cookie. The access token will remain valid
    until it expires. For immediate invalidation, consider implementing
    a token blacklist.
    """
    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}
