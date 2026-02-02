"""AI-powered features for reading sessions."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.application.reading.services import ReadingSessionAISummaryService
from src.database import DatabaseSession
from src.domain.identity.entities.user import User
from src.exceptions import ReadingSessionNotFoundError, ValidationError
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.identity.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reading_sessions", tags=["reading_sessions", "ai"])


@router.get(
    "/{reading_session_id}/ai_summary",
    response_model=schemas.ReadingSessionAISummaryResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def get_reading_session_ai_summary(
    reading_session_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.ReadingSessionAISummaryResponse:
    """
    Get AI-generated summary for a reading session.

    Returns cached summary if available, otherwise generates new summary
    from the read content and caches it.

    Args:
        reading_session_id: ID of the reading session
        db: Database session
        current_user: Authenticated user

    Returns:
        ReadingSessionAISummaryResponse with the AI summary

    Raises:
        HTTPException 404: If reading session not found or not owned by user
        HTTPException 400: If session has no position data or PDF not supported
        HTTPException 500: For unexpected errors
    """

    try:
        service = ReadingSessionAISummaryService(db)
        summary = await service.get_or_generate_summary(reading_session_id, current_user.id.value)
        return schemas.ReadingSessionAISummaryResponse(summary=summary)
    except ReadingSessionNotFoundError as e:
        logger.warning(
            f"Reading session {reading_session_id} not found for user {current_user.id.value}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ValidationError as e:
        logger.warning(f"Validation error for AI summary (session {reading_session_id}): {e!s}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            f"Failed to get AI summary for reading session: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
