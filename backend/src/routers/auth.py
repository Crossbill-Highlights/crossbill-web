import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from src.database import DatabaseSession
from src.repositories import UserRepository
from src.schemas.auth_schemas import LoginResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DatabaseSession
) -> LoginResponse:
    # TODO: move to service
    user_repository = UserRepository(db)
    user = user_repository.get_by_name(form_data.username)

    if not user:
        logger.error("Login failed for user: %s", form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # TODO: HASH PASSWORD!
    hashed_password = form_data.password
    if hashed_password != user.hashed_password:
        logger.error("Invalid password for user: %s", form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    logger.info("User %s logged in successfully", form_data.username)
    # TODO: Generate unique token for this login
    return LoginResponse(access_token= user.name, token_type= "bearer")
