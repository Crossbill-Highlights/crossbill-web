"""Token creation and verification service."""

from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError
from pydantic import BaseModel

from src.config import get_settings

settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY or SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


class TokenWithRefresh(BaseModel):
    """DTO for token pair with access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


def create_access_token(user_id: int) -> str:
    """Create an access token for a user."""
    expire = datetime.now(UTC) + timedelta(days=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a refresh token for a user."""
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> int | None:
    """Verify an access token and return the user_id if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Reject refresh tokens - they should only be used at the /refresh endpoint
        if payload.get("type") == "refresh":
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (InvalidTokenError, ValueError):
        return None


def verify_refresh_token(token: str) -> int | None:
    """Verify a refresh token and return the user_id if valid."""
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (InvalidTokenError, ValueError):
        return None


def create_token_pair(user_id: int) -> TokenWithRefresh:
    """Create a token pair (access + refresh) for a user."""
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return TokenWithRefresh(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",  # noqa: S106
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )
