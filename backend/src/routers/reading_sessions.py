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
    Upload reading sessions from KOReader for a single book.

    All sessions in a request must be for the same book.

    Args:
        request: Upload request containing book metadata and reading sessions

    Returns:
        ReadingSessionUploadResponse with upload statistics
    """
    try:
        service = ReadingSessionService(db)
        return service.upload_reading_sessions(
            client_book_id=request.client_book_id,
            sessions=request.sessions,
            user_id=current_user.id,
        )
    except Exception as e:
        logger.error(f"Failed to upload reading sessions: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
