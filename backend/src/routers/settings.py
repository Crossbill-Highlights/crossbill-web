from fastapi import APIRouter

from src.config import get_settings
from src.schemas.settings_schemas import AppSettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_app_settings() -> AppSettingsResponse:
    """
    Get public application settings.

    Returns non-user-specific settings that affect application behavior.
    This is a public endpoint that doesn't require authentication.
    """
    settings = get_settings()

    return AppSettingsResponse(allow_user_registrations=settings.ALLOW_USER_REGISTRATIONS)
