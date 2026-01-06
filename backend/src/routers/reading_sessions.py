"""API routes for reading sessions management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.database import DatabaseSession
from src.models import User
from src.services.auth_service import get_current_user
from src.services.reading_session_service import ReadingSessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reading_sessions", tags=["reading_sessions"])


@router.post(
    "/upload",
    response_model=schemas.ReadingSessionUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_reading_sessions(
    request: schemas.ReadingSessionUploadRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.ReadingSessionUploadResponse:
    """
    Upload reading sessions from KOReader with per-item error handling.

    Sessions are validated individually. Valid sessions are saved even if some
    fail validation. The response includes detailed statistics and information
    about any failures.

    Args:
        request: Upload request containing reading sessions

    Returns:
        ReadingSessionUploadResponse with upload statistics and failures
    """
    try:
        service = ReadingSessionService(db)
        return service.upload_reading_sessions(request.sessions, current_user.id)
    except Exception as e:
        logger.error(f"Failed to upload reading sessions: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
