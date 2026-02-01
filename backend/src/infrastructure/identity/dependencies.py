"""FastAPI dependencies for identity and authentication."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.database import DatabaseSession
from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.exceptions import CredentialsException
from src.infrastructure.identity.auth.token_service import verify_access_token
from src.infrastructure.identity.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DatabaseSession
) -> User:
    """
    Get the current authenticated user from the access token.

    Args:
        token: JWT access token from Authorization header
        db: Database session

    Returns:
        User domain entity

    Raises:
        CredentialsException: If token is invalid or user not found
    """
    user_id = verify_access_token(token)
    if user_id is None:
        raise CredentialsException

    user_repository = UserRepository(db)
    user = user_repository.find_by_id(UserId(user_id))
    if user is None:
        raise CredentialsException

    return user
