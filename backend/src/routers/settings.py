from fastapi import APIRouter

from src.feature_flags import get_feature_flags
from src.schemas.settings_schemas import AppSettingsResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_app_settings() -> AppSettingsResponse:
    """
    Get public application settings.

    Returns non-user-specific settings that affect application behavior.
    This is a public endpoint that doesn't require authentication.
    """
    return AppSettingsResponse(feature_flags=get_feature_flags())
