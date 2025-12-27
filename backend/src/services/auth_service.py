from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel

from src.config import get_settings
from src.database import DatabaseSession
from src.exceptions import CredentialsException
from src.models import User
from src.repositories import UserRepository

settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY or SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
DUMMY_HASH = "fasdflkdfjdlkfjlfdjsdlkasfsf"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenWithRefresh(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    user_id: str | None = None


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(plain_password: str) -> str:
    """Hash a plain password for storage."""
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return password_hash.verify(plain_password, hashed_password)


def _get_user_by_email(db: DatabaseSession, email: str) -> User | None:
    user_repository = UserRepository(db)
    return user_repository.get_by_email(email)


def _get_user_by_id(db: DatabaseSession, id: int) -> User | None:
    user_repository = UserRepository(db)
    return user_repository.get_by_id(id)


def authenticate_user(email: str, password: str, db: DatabaseSession) -> User | None:
    user = _get_user_by_email(db, email)
    if not user:
        _verify_password(password, DUMMY_HASH)  # Constant time to avoid timing difference
        return None
    if not user.hashed_password or not _verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(days=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)


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
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return TokenWithRefresh(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",  # noqa: S106
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DatabaseSession
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Reject refresh tokens - they should only be used at the /refresh endpoint
        if payload.get("type") == "refresh":
            raise CredentialsException
        user_id = payload.get("sub")
        if user_id is None:
            raise CredentialsException
        token_data = TokenData(user_id=user_id)
    except InvalidTokenError:
        raise CredentialsException from InvalidTokenError

    if token_data.user_id is None:
        raise CredentialsException
    user = _get_user_by_id(db, int(token_data.user_id))
    if user is None:
        raise CredentialsException
    return user
