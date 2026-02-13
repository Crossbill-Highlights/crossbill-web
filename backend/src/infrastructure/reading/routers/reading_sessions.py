"""API routes for reading sessions management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.reading.use_cases.reading_sessions.reading_session_ai_summary_use_case import (
    ReadingSessionAISummaryUseCase,
)
from src.application.reading.use_cases.reading_sessions.reading_session_query_use_case import (
    ReadingSessionQueryUseCase,
)
from src.application.reading.use_cases.reading_sessions.reading_session_upload_use_case import (
    ReadingSessionUploadData,
    ReadingSessionUploadUseCase,
)
from src.core import container
from src.domain.identity.entities.user import User
from src.exceptions import CrossbillError, ReadingSessionNotFoundError, ValidationError
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.reading.schemas import (
    Highlight,
    ReadingSession,
    ReadingSessionAISummaryResponse,
    ReadingSessionsResponse,
    ReadingSessionUploadRequest,
    ReadingSessionUploadResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["reading_sessions"])


@router.post(
    "/reading_sessions/upload",
    response_model=ReadingSessionUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_reading_sessions(
    request: ReadingSessionUploadRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: ReadingSessionUploadUseCase = Depends(
        inject_use_case(container.reading_session_upload_use_case)
    ),
) -> ReadingSessionUploadResponse:
    """
    Upload reading sessions from KOReader for a single book.

    All sessions in a request must be for the same book.

    Args:
        request: Upload request containing book metadata and reading sessions

    Returns:
        ReadingSessionUploadResponse with upload statistics
    """
    try:
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

        # Call use case
        result = use_case.upload_reading_sessions(
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

        return ReadingSessionUploadResponse(
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


@router.get(
    "/books/{book_id}/reading_sessions",
    response_model=ReadingSessionsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_book_reading_sessions(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(30, ge=1, le=1000, description="Maximum sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    use_case: ReadingSessionQueryUseCase = Depends(
        inject_use_case(container.reading_session_query_use_case)
    ),
) -> ReadingSessionsResponse:
    """
    Get reading sessions for a specific book.

    Returns reading sessions ordered by start time (newest first).

    Args:
        book_id: ID of the book
        limit: Maximum number of sessions
        offset: Pagination offset

    Returns:
        ReadingSessionsResponse with sessions list
    """
    try:
        # Call use case
        result = use_case.get_sessions_for_book(
            book_id=book_id,
            user_id=current_user.id.value,
            limit=limit,
            offset=offset,
            include_content=True,
        )

        # Manually construct Pydantic schemas
        sessions_schemas = []
        for session_with_highlights in result.sessions_with_highlights:
            session = session_with_highlights.session

            # Convert highlights to schemas
            # Note: We don't have chapter/tags/flashcards loaded, so use minimal schema
            highlight_schemas = []
            for highlight in session_with_highlights.highlights:
                # Construct Highlight schema directly with named parameters
                highlight_schemas.append(
                    Highlight(
                        id=highlight.id.value,
                        book_id=highlight.book_id.value,
                        chapter_id=highlight.chapter_id.value if highlight.chapter_id else None,
                        text=highlight.text,
                        page=highlight.page,
                        note=highlight.note,
                        datetime=highlight.datetime,
                        created_at=highlight.created_at,
                        updated_at=highlight.updated_at,
                        chapter=None,  # Not loaded in this context
                        chapter_number=None,  # Not loaded in this context
                        highlight_tags=[],  # Not loaded in this context
                        flashcards=[],  # Not loaded in this context
                    )
                )

            # Build ReadingSession schema
            # Assert created_at is not None (always present for persisted entities)
            assert session.created_at is not None, "Persisted session must have created_at"

            sessions_schemas.append(
                ReadingSession(
                    id=session.id.value,
                    book_id=session.book_id.value,
                    device_id=session.device_id,
                    content_hash=session.content_hash.value,
                    start_time=session.start_time,
                    end_time=session.end_time,
                    start_page=session.start_page,
                    end_page=session.end_page,
                    content=session_with_highlights.extracted_content,
                    ai_summary=session.ai_summary,
                    created_at=session.created_at,
                    highlights=highlight_schemas,
                )
            )

        return ReadingSessionsResponse(
            sessions=sessions_schemas,
            total=result.total,
            offset=result.offset,
            limit=result.limit,
        )
    except CrossbillError:
        raise
    except Exception as e:
        logger.error(f"Failed to get reading sessions for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/{reading_session_id}/ai_summary",
    response_model=ReadingSessionAISummaryResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def get_reading_session_ai_summary(
    reading_session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: ReadingSessionAISummaryUseCase = Depends(
        inject_use_case(container.reading_session_ai_summary_use_case)
    ),
) -> ReadingSessionAISummaryResponse:
    """
    Get AI-generated summary for a reading session.

    Returns cached summary if available, otherwise generates new summary
    from the read content and caches it.

    Args:
        reading_session_id: ID of the reading session
        current_user: Authenticated user

    Returns:
        ReadingSessionAISummaryResponse with the AI summary

    Raises:
        HTTPException 404: If reading session not found or not owned by user
        HTTPException 400: If session has no position data or PDF not supported
        HTTPException 500: For unexpected errors
    """

    try:
        summary = await use_case.get_or_generate_summary(reading_session_id, current_user.id.value)
        return ReadingSessionAISummaryResponse(summary=summary)
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
