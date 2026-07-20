"""Common infrastructure schemas."""

from src.infrastructure.common.schemas.response_wrappers import (
    CollectionResponse,
    PaginatedResponse,
    SuccessResponse,
)
from src.infrastructure.common.schemas.settings_schemas import AppSettingsResponse

__all__ = [
    "AppSettingsResponse",
    "CollectionResponse",
    "PaginatedResponse",
    "SuccessResponse",
]
