"""API routes for highlights management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src import schemas
from src.database import DatabaseSession
from src.exceptions import CrossbillError
from src.models import User
from src.services import FlashcardService, HighlightService, HighlightTagService
from src.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/highlights", tags=["highlights"])


@router.post(
    "/upload",
    response_model=schemas.HighlightUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_highlights(
    request: schemas.HighlightUploadRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightUploadResponse:
    """
    Upload highlights from KOReader.

    Creates or updates book record and adds highlights with automatic deduplication.
    Duplicates are identified by the combination of book, text, and datetime.

    Args:
        request: Highlight upload request containing book metadata and highlights
        db: Database session

    Returns:
        HighlightUploadResponse with upload statistics

    Raises:
        HTTPException: If upload fails due to server error
    """
    try:
        service = HighlightService(db)
        return service.upload_highlights(request, current_user.id)
    except Exception as e:
        logger.error(f"Failed to upload highlights: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/search",
    response_model=schemas.HighlightSearchResponse,
    status_code=status.HTTP_200_OK,
)
def search_highlights(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
    search_text: str = Query(
        ...,
        alias="searchText",
        min_length=1,
        description="Text to search for in highlights",
    ),
    book_id: int | None = Query(
        None, alias="bookId", ge=1, description="Optional book ID to filter results"
    ),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results to return"),
) -> schemas.HighlightSearchResponse:
    """
    Search for highlights using full-text search.

    Searches across all highlight text using PostgreSQL full-text search.
    Results are ranked by relevance and excludes soft-deleted highlights.

    Args:
        db: Database session
        search_text: Text to search for
        book_id: Optional book ID to filter by specific book
        limit: Maximum number of results to return

    Returns:
        HighlightSearchResponse with matching highlights and their book/chapter data

    Raises:
        HTTPException: If search fails due to server error
    """
    try:
        service = HighlightService(db)
        return service.search_highlights(search_text, current_user.id, book_id, limit)
    except Exception as e:
        logger.error(f"Failed to search highlights: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/{highlight_id}/note",
    response_model=schemas.HighlightNoteUpdateResponse,
    status_code=status.HTTP_200_OK,
)
def update_highlight_note(
    highlight_id: int,
    request: schemas.HighlightNoteUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightNoteUpdateResponse:
    """
    Update the note field of a highlight.

    Args:
        highlight_id: ID of the highlight to update
        request: Note update request
        db: Database session

    Returns:
        HighlightNoteUpdateResponse with the updated highlight

    Raises:
        HTTPException: If highlight not found or update fails
    """
    try:
        service = HighlightService(db)
        highlight = service.update_highlight_note(highlight_id, current_user.id, request)

        if highlight is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Highlight with id {highlight_id} not found",
            )

        return schemas.HighlightNoteUpdateResponse(
            success=True,
            message="Note updated successfully",
            highlight=highlight,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update highlight note: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/tag_group",
    response_model=schemas.HighlightTagGroup,
    status_code=status.HTTP_200_OK,
)
def create_or_update_tag_group(
    request: schemas.HighlightTagGroupCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightTagGroup:
    """
    Create a new tag group or update an existing one.

    Args:
        request: Tag group creation/update request
        db: Database session

    Returns:
        Created or updated HighlightTagGroup

    Raises:
        HTTPException: If creation/update fails
    """
    try:
        service = HighlightTagService(db)
        tag_group = service.upsert_tag_group(
            book_id=request.book_id,
            name=request.name,
            user_id=current_user.id,
            tag_group_id=request.id,
        )
        return schemas.HighlightTagGroup.model_validate(tag_group)
    except ValueError as e:
        # Check if it's a "not found" error or a validation error
        error_msg = str(e)
        if "not found" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=error_msg,
        ) from e
    except CrossbillError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to create/update tag group: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.delete(
    "/tag_group/{tag_group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tag_group(
    tag_group_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete a tag group.

    Args:
        tag_group_id: ID of the tag group to delete
        db: Database session

    Raises:
        HTTPException: If tag group not found or deletion fails
    """
    try:
        service = HighlightTagService(db)
        success = service.delete_tag_group(tag_group_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag group with id {tag_group_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete tag group: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/{highlight_id}/flashcards",
    response_model=schemas.FlashcardCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_flashcard_for_highlight(
    highlight_id: int,
    request: schemas.FlashcardCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.FlashcardCreateResponse:
    """
    Create a flashcard for a highlight.

    Creates a flashcard that is associated with a specific highlight.
    The flashcard will also be linked to the highlight's book.

    Args:
        highlight_id: ID of the highlight
        request: Request containing question and answer
        db: Database session

    Returns:
        Created flashcard

    Raises:
        HTTPException: If highlight not found or creation fails
    """
    try:
        service = FlashcardService(db)
        flashcard = service.create_flashcard_for_highlight(
            highlight_id=highlight_id,
            user_id=current_user.id,
            question=request.question,
            answer=request.answer,
        )
        return schemas.FlashcardCreateResponse(
            success=True,
            message="Flashcard created successfully",
            flashcard=flashcard,
        )
    except CrossbillError:
        raise
    except Exception as e:
        logger.error(
            f"Failed to create flashcard for highlight {highlight_id}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
