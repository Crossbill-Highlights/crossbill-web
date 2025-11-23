from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status

from src.constants import DEFAULT_USER_ID
from src.database import DatabaseSession
from src.models import User
from src.repositories import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(_token: Annotated[str, Depends(oauth2_scheme)], db: DatabaseSession) -> User:
    # TODO: Fetch and return the user based on the provided token
    print("Authenticating user with token:", _token)
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(DEFAULT_USER_ID)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
