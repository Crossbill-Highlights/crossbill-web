"""API routes for highlights management."""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.learning.services.flashcard_service import FlashcardService
from src.application.reading.services.highlight_tag_association_service import (
    HighlightTagAssociationService,
)
from src.application.reading.services.highlight_tag_group_service import (
    HighlightTagGroupService,
)
from src.application.reading.services.highlight_tag_service import HighlightTagService
from src.application.reading.services.highlight_upload_service import (
    HighlightService as DomainHighlightService,
)
from src.application.reading.services.highlight_upload_service import HighlightUploadData
from src.application.reading.services.update_highlight_note_service import (
    UpdateHighlightNoteService,
)
from src.application.reading.use_cases.highlight_delete_use_case import (
    HighlightDeleteUseCase,
)
from src.application.reading.use_cases.highlight_search_use_case import HighlightSearchUseCase
from src.core import container
from src.database import DatabaseSession
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects import HighlightId, HighlightTagId, UserId
from src.domain.identity.entities.user import User
from src.domain.reading.exceptions import BookNotFoundError
from src.domain.reading.services.highlight_grouping_service import (
    ChapterWithHighlights as ChapterWithHighlightsDomain,
)
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.learning.schemas import (
    Flashcard,
    FlashcardCreateRequest,
    FlashcardCreateResponse,
)
from src.infrastructure.reading.repositories import HighlightRepository, HighlightTagRepository
from src.infrastructure.reading.schemas import (
    BookHighlightSearchResponse,
    ChapterWithHighlights,
    Highlight,
    HighlightDeleteRequest,
    HighlightDeleteResponse,
    HighlightNoteUpdate,
    HighlightNoteUpdateResponse,
    HighlightTag,
    HighlightTagAssociationRequest,
    HighlightTagCreateRequest,
    HighlightTagGroup,
    HighlightTagGroupCreateRequest,
    HighlightTagInBook,
    HighlightTagsResponse,
    HighlightTagUpdateRequest,
    HighlightUploadRequest,
    HighlightUploadResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["highlights"])


@router.post(
    "/highlights/upload",
    response_model=HighlightUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_highlights(
    request: HighlightUploadRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HighlightUploadResponse:
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
        highlight_data_list = [
            HighlightUploadData(
                text=h.text,
                chapter_number=h.chapter_number,
                chapter=h.chapter,
                start_xpoint=h.start_xpoint,
                end_xpoint=h.end_xpoint,
                page=h.page,
                note=h.note,
            )
            for h in request.highlights
        ]

        service = DomainHighlightService(db)
        created, skipped = service.upload_highlights(
            client_book_id=request.client_book_id,
            highlight_data_list=highlight_data_list,
            user_id=current_user.id.value,
        )

        return HighlightUploadResponse(
            success=True,
            message="Successfully synced highlights",
            book_id=0,  # TODO: Return actual book_id from service if needed
            highlights_created=created,
            highlights_skipped=skipped,
        )
    except BookNotFoundError as e:
        logger.error(f"Failed to upload highlights for non existent book: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book could not be found",
        ) from e
    except Exception as e:
        logger.error(f"Failed to upload highlights: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/highlights/{highlight_id}/note",
    response_model=HighlightNoteUpdateResponse,
    status_code=status.HTTP_200_OK,
)
def update_highlight_note(
    highlight_id: int,
    request: HighlightNoteUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HighlightNoteUpdateResponse:
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
        service = UpdateHighlightNoteService(db)
        result = service.update_note(highlight_id, current_user.id.value, request.note)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Highlight with id {highlight_id} not found",
            )

        highlight, flashcards, highlight_tags = result

        # Commit the transaction
        db.commit()

        # Build response from domain entities
        highlight_schema = Highlight(
            id=highlight.id.value,
            book_id=highlight.book_id.value,
            chapter_id=highlight.chapter_id.value if highlight.chapter_id else None,
            text=highlight.text,
            chapter=None,  # We don't have chapter name loaded
            chapter_number=None,
            page=highlight.page,
            start_xpoint=highlight.xpoints.start.to_string() if highlight.xpoints else None,
            end_xpoint=highlight.xpoints.end.to_string() if highlight.xpoints else None,
            note=highlight.note,
            datetime=highlight.datetime,
            highlight_tags=[
                HighlightTagInBook(
                    id=tag.id.value,
                    name=tag.name,
                    tag_group_id=tag.tag_group_id,
                )
                for tag in highlight_tags
            ],
            flashcards=[
                Flashcard(
                    id=fc.id.value,
                    user_id=fc.user_id.value,
                    book_id=fc.book_id.value,
                    highlight_id=fc.highlight_id.value if fc.highlight_id else None,
                    question=fc.question,
                    answer=fc.answer,
                )
                for fc in flashcards
            ],
            created_at=highlight.created_at,
            updated_at=highlight.updated_at,
        )

        return HighlightNoteUpdateResponse(
            success=True,
            message="Note updated successfully",
            highlight=highlight_schema,
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
    "/highlights/tag_group",
    response_model=HighlightTagGroup,
    status_code=status.HTTP_200_OK,
)
def create_or_update_tag_group(
    request: HighlightTagGroupCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HighlightTagGroup:
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
        service = HighlightTagGroupService(db)

        # Create or update based on whether ID is provided
        if request.id is not None:
            # Update existing
            tag_group = service.update_group(
                group_id=request.id,
                book_id=request.book_id,
                new_name=request.name,
                user_id=current_user.id.value,
            )
        else:
            # Create new
            tag_group = service.create_group(
                book_id=request.book_id,
                name=request.name,
                user_id=current_user.id.value,
            )

        # Manually construct response to handle value objects
        return HighlightTagGroup(
            id=tag_group.id.value,
            book_id=tag_group.book_id.value,
            name=tag_group.name,
        )
    except (CrossbillError, DomainError) as e:
        if isinstance(e, CrossbillError):
            raise HTTPException(
                status_code=e.status_code,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
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
    except Exception as e:
        logger.error(f"Failed to create/update tag group: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.delete(
    "/highlights/tag_group/{tag_group_id}",
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
        service = HighlightTagGroupService(db)
        success = service.delete_group(tag_group_id, current_user.id.value)
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
    "/highlights/{highlight_id}/flashcards",
    response_model=FlashcardCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_flashcard_for_highlight(
    highlight_id: int,
    request: FlashcardCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FlashcardCreateResponse:
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
        flashcard_entity = service.create_flashcard_for_highlight(
            highlight_id=highlight_id,
            user_id=current_user.id.value,
            question=request.question,
            answer=request.answer,
        )
        # Manually construct Pydantic schema from domain entity
        flashcard = Flashcard(
            id=flashcard_entity.id.value,
            user_id=flashcard_entity.user_id.value,
            book_id=flashcard_entity.book_id.value,
            highlight_id=flashcard_entity.highlight_id.value
            if flashcard_entity.highlight_id
            else None,
            question=flashcard_entity.question,
            answer=flashcard_entity.answer,
        )
        return FlashcardCreateResponse(
            success=True,
            message="Flashcard created successfully",
            flashcard=flashcard,
        )
    except (CrossbillError, DomainError, ValidationError):
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


def _map_chapters_to_schemas(
    chapters_grouped: list[ChapterWithHighlightsDomain],
) -> list[ChapterWithHighlights]:
    """
    Map domain ChapterWithHighlights to Pydantic schemas.

    Args:
        chapters_grouped: List of ChapterWithHighlights domain dataclasses

    Returns:
        List of ChapterWithHighlights Pydantic schemas
    """
    chapters_with_highlights = []

    for chapter_group in chapters_grouped:
        highlight_schemas = []
        for hw in chapter_group.highlights:
            h = hw.highlight
            chapter = hw.chapter

            highlight_schema = Highlight(
                id=h.id.value,
                book_id=h.book_id.value,
                chapter_id=h.chapter_id.value if h.chapter_id else None,
                text=h.text,
                chapter=chapter.name if chapter else None,
                chapter_number=chapter.chapter_number if chapter else None,
                page=h.page,
                note=h.note,
                datetime=h.datetime,
                flashcards=[
                    Flashcard(
                        id=fc.id.value,
                        user_id=fc.user_id.value,
                        book_id=fc.book_id.value,
                        highlight_id=fc.highlight_id.value if fc.highlight_id else None,
                        question=fc.question,
                        answer=fc.answer,
                    )
                    for fc in hw.flashcards
                ],
                highlight_tags=[
                    HighlightTagInBook(
                        id=tag.id.value,
                        name=tag.name,
                        tag_group_id=tag.tag_group_id,
                    )
                    for tag in hw.tags
                ],
                start_xpoint=h.xpoints.start.to_string() if h.xpoints else None,
                end_xpoint=h.xpoints.end.to_string() if h.xpoints else None,
                created_at=h.created_at,
                updated_at=h.updated_at,
            )
            highlight_schemas.append(highlight_schema)

        # Get chapter info from first highlight's chapter
        first_chapter = chapter_group.highlights[0].chapter if chapter_group.highlights else None

        chapter_with_highlights = ChapterWithHighlights(
            id=chapter_group.chapter_id,
            name=chapter_group.chapter_name or "",
            chapter_number=chapter_group.chapter_number,
            highlights=highlight_schemas,
            created_at=first_chapter.created_at if first_chapter else datetime.now(UTC),
            updated_at=first_chapter.created_at if first_chapter else datetime.now(UTC),
        )
        chapters_with_highlights.append(chapter_with_highlights)

    return chapters_with_highlights


@router.get(
    "/books/{book_id}/highlights",
    response_model=BookHighlightSearchResponse,
    status_code=status.HTTP_200_OK,
)
def search_book_highlights(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    search_text: str = Query(
        ...,
        alias="searchText",
        min_length=1,
        description="Text to search for in highlights",
    ),
    use_case: HighlightSearchUseCase = Depends(
        inject_use_case(container.highlight_search_use_case)
    ),
) -> BookHighlightSearchResponse:
    """
    Search for highlights in book using full-text search.

    Searches across all highlight text using PostgreSQL full-text search.
    Results are ranked by relevance and excludes soft-deleted highlights.
    """
    try:
        chapters_grouped, total = use_case.search_book_highlights(
            book_id, current_user.id.value, search_text
        )
        return BookHighlightSearchResponse(
            chapters=_map_chapters_to_schemas(chapters_grouped),
            total=total,
        )
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to fetch book details for book_id={book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.delete(
    "/books/{book_id}/highlight",
    response_model=HighlightDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_highlights(
    book_id: int,
    request: HighlightDeleteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: HighlightDeleteUseCase = Depends(
        inject_use_case(container.highlight_delete_use_case)
    ),
) -> HighlightDeleteResponse:
    """
    Soft delete highlights from a book.

    This performs a soft delete by marking the highlights as deleted.
    When syncing highlights, deleted highlights will not be recreated,
    ensuring that user deletions persist across syncs.

    Args:
        book_id: ID of the book
        request: Request containing list of highlight IDs to delete

    Returns:
        HighlightDeleteResponse with deletion status and count

    Raises:
        HTTPException: If book is not found or deletion fails
        :param use_case:
    """
    try:
        deleted_count = use_case.delete_highlights(
            book_id, request.highlight_ids, current_user.id.value
        )
        return HighlightDeleteResponse(
            success=True,
            message=f"Successfully deleted {deleted_count} highlight(s)",
            deleted_count=deleted_count,
        )
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to delete highlights for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/books/{book_id}/highlight_tags",
    response_model=HighlightTagsResponse,
    status_code=status.HTTP_200_OK,
)
def get_highlight_tags(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HighlightTagsResponse:
    """
    Get all highlight tags for a book.

    Args:
        book_id: ID of the book
        db: Database session

    Returns:
        List of HighlightTags for the book

    Raises:
        HTTPException: If book is not found
    """
    try:
        service = HighlightTagService(db)
        tags = service.get_tags_for_book(book_id, current_user.id.value)
        return HighlightTagsResponse(
            tags=[
                HighlightTag(
                    id=tag.id.value,
                    book_id=tag.book_id.value,
                    name=tag.name,
                    tag_group_id=tag.tag_group_id,
                )
                for tag in tags
            ]
        )
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/books/{book_id}/highlight_tag",
    response_model=HighlightTag,
    status_code=status.HTTP_201_CREATED,
)
def create_highlight_tag(
    book_id: int,
    request: HighlightTagCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HighlightTag:
    """
    Create a new highlight tag for a book.

    Args:
        book_id: ID of the book
        request: Request containing tag name
        db: Database session

    Returns:
        Created HighlightTag

    Raises:
        HTTPException: If book is not found, tag already exists, or creation fails
    """
    try:
        service = HighlightTagService(db)
        tag = service.create_tag(book_id, request.name, user_id=current_user.id.value)
        return HighlightTag(
            id=tag.id.value,
            book_id=tag.book_id.value,
            name=tag.name,
            tag_group_id=tag.tag_group_id,
        )
    except (CrossbillError, DomainError):
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to create highlight tag for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.delete(
    "/books/{book_id}/highlight_tag/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_highlight_tag(
    book_id: int,
    tag_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete a highlight tag from a book.

    This will also remove the tag from all highlights it was associated with.

    Args:
        book_id: ID of the book
        tag_id: ID of the tag to delete
        db: Database session

    Raises:
        HTTPException: If tag is not found, doesn't belong to book, or deletion fails
    """
    try:
        service = HighlightTagService(db)
        deleted = service.delete_tag(book_id, tag_id, current_user.id.value)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Highlight tag {tag_id} not found",
            )
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete highlight tag {tag_id} for book {book_id}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/books/{book_id}/highlight_tag/{tag_id}",
    response_model=HighlightTag,
    status_code=status.HTTP_200_OK,
)
def update_highlight_tag(
    book_id: int,
    tag_id: int,
    request: HighlightTagUpdateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> HighlightTag:
    """
    Update a highlight tag's name and/or tag group association.

    Args:
        book_id: ID of the book
        tag_id: ID of the tag to update
        request: Request containing updated tag information
        db: Database session

    Returns:
        Updated HighlightTag

    Raises:
        HTTPException: If tag not found, doesn't belong to book, or update fails
    """
    try:
        tag_service = HighlightTagService(db)
        group_service = HighlightTagGroupService(db)

        # Update name if provided
        if request.name is not None:
            tag = tag_service.update_tag_name(
                book_id=book_id,
                tag_id=tag_id,
                new_name=request.name,
                user_id=current_user.id.value,
            )
        else:
            # Load tag for group update
            tag_repo = HighlightTagRepository(db)
            tag = tag_repo.find_by_id(HighlightTagId(tag_id), UserId(current_user.id.value))
            if not tag:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tag {tag_id} not found",
                )

        # Update group association if provided (including None to clear)
        if hasattr(request, "tag_group_id"):
            tag = group_service.update_tag_group_association(
                book_id=book_id,
                tag_id=tag_id,
                group_id=request.tag_group_id,
                user_id=current_user.id.value,
            )

        return HighlightTag(
            id=tag.id.value,
            book_id=tag.book_id.value,
            name=tag.name,
            tag_group_id=tag.tag_group_id,
        )
    except (CrossbillError, DomainError) as e:
        if isinstance(e, CrossbillError):
            raise HTTPException(
                status_code=e.status_code,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to update highlight tag {tag_id} for book {book_id}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/books/{book_id}/highlight/{highlight_id}/tag",
    response_model=Highlight,
    status_code=status.HTTP_200_OK,
)
def add_tag_to_highlight(
    book_id: int,
    highlight_id: int,
    request: HighlightTagAssociationRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Highlight:
    """
    Add a tag to a highlight.

    If a tag name is provided and doesn't exist, it will be created first.
    If a tag_id is provided, it will be used directly.

    Args:
        book_id: ID of the book
        highlight_id: ID of the highlight
        request: Request containing either tag name or tag_id
        db: Database session

    Returns:
        Updated Highlight with tags

    Raises:
        HTTPException: If highlight or tag not found, or association fails
    """
    try:
        service = HighlightTagAssociationService(db)

        # Add tag by ID or by name (with get_or_create)
        if request.tag_id is not None:
            service.add_tag_by_id(highlight_id, request.tag_id, current_user.id.value)
        elif request.name is not None:
            service.add_tag_by_name(book_id, highlight_id, request.name, current_user.id.value)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either tag_id or name must be provided",
            )

        # Reload highlight with relations to get updated tags
        highlight_repo = HighlightRepository(db)
        result = highlight_repo.find_by_id_with_relations(
            HighlightId(highlight_id), UserId(current_user.id.value)
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Highlight with id {highlight_id} not found",
            )

        highlight, flashcards, highlight_tags = result

        # Manually construct schema from domain entities
        return Highlight(
            id=highlight.id.value,
            book_id=highlight.book_id.value,
            chapter_id=highlight.chapter_id.value if highlight.chapter_id else None,
            text=highlight.text,
            chapter=None,
            chapter_number=None,
            page=highlight.page,
            start_xpoint=highlight.xpoints.start.to_string() if highlight.xpoints else None,
            end_xpoint=highlight.xpoints.end.to_string() if highlight.xpoints else None,
            note=highlight.note,
            datetime=highlight.datetime,
            highlight_tags=[
                HighlightTagInBook(
                    id=tag.id.value,
                    name=tag.name,
                    tag_group_id=tag.tag_group_id,
                )
                for tag in highlight_tags
            ],
            flashcards=[
                Flashcard(
                    id=fc.id.value,
                    user_id=fc.user_id.value,
                    book_id=fc.book_id.value,
                    highlight_id=fc.highlight_id.value if fc.highlight_id else None,
                    question=fc.question,
                    answer=fc.answer,
                )
                for fc in flashcards
            ],
            created_at=highlight.created_at,
            updated_at=highlight.updated_at,
        )
    except (CrossbillError, DomainError):
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        logger.error(f"Failed to add tag to highlight {highlight_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.delete(
    "/books/{book_id}/highlight/{highlight_id}/tag/{tag_id}",
    response_model=Highlight,
    status_code=status.HTTP_200_OK,
)
def remove_tag_from_highlight(
    book_id: int,
    highlight_id: int,
    tag_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Highlight:
    """
    Remove a tag from a highlight.

    Args:
        book_id: ID of the book
        highlight_id: ID of the highlight
        tag_id: ID of the tag to remove
        db: Database session

    Returns:
        Updated Highlight with tags

    Raises:
        HTTPException: If highlight not found or removal fails
    """
    try:
        service = HighlightTagAssociationService(db)
        service.remove_tag(highlight_id, tag_id, current_user.id.value)

        # Reload highlight with relations to get updated tags
        highlight_repo = HighlightRepository(db)
        result = highlight_repo.find_by_id_with_relations(
            HighlightId(highlight_id), UserId(current_user.id.value)
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Highlight with id {highlight_id} not found",
            )

        highlight, flashcards, highlight_tags = result

        # Manually construct schema from domain entities
        return Highlight(
            id=highlight.id.value,
            book_id=highlight.book_id.value,
            chapter_id=highlight.chapter_id.value if highlight.chapter_id else None,
            text=highlight.text,
            chapter=None,
            chapter_number=None,
            page=highlight.page,
            start_xpoint=highlight.xpoints.start.to_string() if highlight.xpoints else None,
            end_xpoint=highlight.xpoints.end.to_string() if highlight.xpoints else None,
            note=highlight.note,
            datetime=highlight.datetime,
            highlight_tags=[
                HighlightTagInBook(
                    id=tag.id.value,
                    name=tag.name,
                    tag_group_id=tag.tag_group_id,
                )
                for tag in highlight_tags
            ],
            flashcards=[
                Flashcard(
                    id=fc.id.value,
                    user_id=fc.user_id.value,
                    book_id=fc.book_id.value,
                    highlight_id=fc.highlight_id.value if fc.highlight_id else None,
                    question=fc.question,
                    answer=fc.answer,
                )
                for fc in flashcards
            ],
            created_at=highlight.created_at,
            updated_at=highlight.updated_at,
        )
    except (CrossbillError, DomainError):
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except HTTPException:
        # Re-raise HTTPException
        raise
    except Exception as e:
        logger.error(f"Failed to remove tag from highlight {highlight_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
