from typing import Annotated

from fastapi import APIRouter, Depends

from services.auth_service import get_current_user
from src.models import User
from src.schemas.user_schemas import UserDetailsResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/me")
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserDetailsResponse:
    return UserDetailsResponse(name=current_user.name, id=current_user.id)
