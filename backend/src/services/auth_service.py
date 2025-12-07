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
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class Token(BaseModel):
    access_token: str
    token_type: str


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
        return None
    if not user.hashed_password or not _verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict[str, str], expires_delta: timedelta | None = None) -> str:
    to_encode: dict[str, str | datetime] = dict(data)
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DatabaseSession
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
