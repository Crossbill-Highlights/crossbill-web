"""API routes for reading sessions management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.application.reading.services import (
    ReadingSessionUploadData,
    ReadingSessionUploadService,
)
from src.database import DatabaseSession
from src.domain.identity.entities.user import User
from src.infrastructure.identity.dependencies import get_current_user

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
        service = ReadingSessionUploadService(db)

        # Convert Pydantic schemas to DTOs
        upload_data = [
            ReadingSessionUploadData(
                start_time=s.start_time,
                end_time=s.end_time,
                start_xpoint=s.start_xpoint,
                end_xpoint=s.end_xpoint,
                start_page=s.start_page,
                end_page=s.end_page,
                device_id=s.device_id,
            )
            for s in request.sessions
        ]

        # Call service
        result = service.upload_reading_sessions(
            client_book_id=request.client_book_id,
            sessions=upload_data,
            user_id=current_user.id.value,
        )

        # Build Pydantic response
        message_parts = []
        if result.created_count > 0:
            message_parts.append(
                f"Created {result.created_count} session{'s' if result.created_count != 1 else ''}"
            )
        if result.skipped_duplicate_count > 0:
            message_parts.append(f"{result.skipped_duplicate_count} skipped (duplicate)")

        message = ". ".join(message_parts) + "." if message_parts else "No sessions to process"

        return schemas.ReadingSessionUploadResponse(
            success=True,
            message=message,
            book_id=result.book_id.value,  # Extract .value from BookId
            created_count=result.created_count,
            skipped_duplicate_count=result.skipped_duplicate_count,
        )
    except Exception as e:
        logger.error(f"Failed to upload reading sessions: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
