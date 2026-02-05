"""FastAPI dependencies for identity and authentication."""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.core import container
from src.database import DatabaseSession
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import UserNotFoundError
from src.exceptions import CredentialsException
from src.infrastructure.identity.services.token_service import verify_access_token

if TYPE_CHECKING:
    pass

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

    container.db.override(db)
    use_case = container.authentication_use_case()

    try:
        return use_case.get_user_by_id(user_id)
    except UserNotFoundError:
        raise CredentialsException from None
