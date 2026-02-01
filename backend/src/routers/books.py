"""API routes for books management."""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from src import schemas
from src.application.learning.services.flashcard_service import FlashcardService
from src.application.library.services.book_cover_service import BookCoverService
from src.application.library.services.book_management_service import BookManagementService
from src.application.library.services.get_recently_viewed_books_service import (
    GetRecentlyViewedBooksService,
)
from src.application.reading.services.book_highlight_deletion_service import (
    BookHighlightDeletionService,
)
from src.application.reading.services.book_highlight_search_service import (
    BookHighlightSearchService,
)
from src.application.reading.services.bookmark_service import BookmarkService
from src.application.reading.services.highlight_tag_association_service import (
    HighlightTagAssociationService,
)
from src.application.reading.services.highlight_tag_group_service import (
    HighlightTagGroupService,
)
from src.application.reading.services.highlight_tag_service import HighlightTagService
from src.database import DatabaseSession
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import HighlightId, HighlightTagId, UserId
from src.domain.library.services.book_details_aggregator import BookDetailsAggregation
from src.domain.reading.services.highlight_grouping_service import ChapterWithHighlights
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.reading.repositories.highlight_repository import (
    HighlightRepository,
)
from src.infrastructure.reading.repositories.highlight_tag_repository import (
    HighlightTagRepository,
)
from src.models import User
from src.services.auth_service import get_current_user
from src.services.highlight_service import HighlightService
from src.services.reading_session_service import ReadingSessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


def _map_chapters_to_schemas(
    chapters_grouped: list[ChapterWithHighlights],
) -> list[schemas.ChapterWithHighlights]:
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

            highlight_schema = schemas.Highlight(
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
                    schemas.Flashcard(
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
                    schemas.HighlightTagInBook(
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

        chapter_with_highlights = schemas.ChapterWithHighlights(
            id=chapter_group.chapter_id,
            name=chapter_group.chapter_name or "",
            chapter_number=chapter_group.chapter_number,
            highlights=highlight_schemas,
            created_at=first_chapter.created_at if first_chapter else datetime.now(UTC),
            updated_at=first_chapter.created_at if first_chapter else datetime.now(UTC),
        )
        chapters_with_highlights.append(chapter_with_highlights)

    return chapters_with_highlights


def _build_book_details_schema(agg: BookDetailsAggregation) -> schemas.BookDetails:
    """
    Build BookDetails Pydantic schema from BookDetailsAggregation.

    Args:
        agg: BookDetailsAggregation domain dataclass

    Returns:
        BookDetails Pydantic schema
    """
    return schemas.BookDetails(
        id=agg.book.id.value,
        client_book_id=agg.book.client_book_id,
        title=agg.book.title,
        author=agg.book.author,
        isbn=agg.book.isbn,
        cover=agg.book.cover,
        description=agg.book.description,
        language=agg.book.language,
        page_count=agg.book.page_count,
        tags=[schemas.TagInBook(id=tag.id.value, name=tag.name) for tag in agg.tags],
        highlight_tags=[
            schemas.HighlightTagInBook(
                id=tag.id.value,
                name=tag.name,
                tag_group_id=tag.tag_group_id,
            )
            for tag in agg.highlight_tags
        ],
        highlight_tag_groups=[
            schemas.HighlightTagGroupInBook.model_validate(group)
            for group in agg.highlight_tag_groups
        ],
        bookmarks=[
            schemas.Bookmark(
                id=b.id.value,
                book_id=b.book_id.value,
                highlight_id=b.highlight_id.value,
                created_at=b.created_at,
            )
            for b in agg.bookmarks
        ],
        chapters=_map_chapters_to_schemas(agg.chapters_with_highlights),
        created_at=agg.book.created_at,
        updated_at=agg.book.updated_at,
        last_viewed=agg.book.last_viewed,
    )


@router.get("/", response_model=schemas.BooksListResponse, status_code=status.HTTP_200_OK)
def get_books(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
    offset: int = Query(0, ge=0, description="Number of books to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of books to return"),
    only_with_flashcards: bool = Query(False, description="Return only books with flashcards"),
    search: str | None = Query(None, description="Search text to filter books by title or author"),
) -> schemas.BooksListResponse:
    """
    Get all books with their highlight counts, sorted alphabetically by title.

    Args:
        db: Database session
        offset: Number of books to skip (for pagination)
        limit: Maximum number of books to return (for pagination)
        search: Optional search text to filter books by title or author

    Returns:
        BooksListResponse with list of books and pagination info

    Raises:
        HTTPException: If fetching books fails due to server error
    """
    try:
        service = HighlightService(db)
        return service.get_books_with_counts(
            current_user.id, offset, limit, only_with_flashcards, search
        )
    except Exception as e:
        logger.error(f"Failed to fetch books: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/recently-viewed",
    response_model=schemas.RecentlyViewedBooksResponse,
    status_code=status.HTTP_200_OK,
)
def get_recently_viewed_books(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(10, ge=1, le=50, description="Maximum number of books to return"),
) -> schemas.RecentlyViewedBooksResponse:
    """
    Get recently viewed books with their highlight counts.

    Returns books that have been viewed at least once, ordered by most recently viewed.

    Args:
        db: Database session
        limit: Maximum number of books to return (default: 10, max: 50)

    Returns:
        RecentlyViewedBooksResponse with list of recently viewed books

    Raises:
        HTTPException: If fetching books fails due to server error
    """
    try:
        service = GetRecentlyViewedBooksService(db)
        results = service.get_recently_viewed(current_user.id, limit)

        books_list = [
            schemas.BookWithHighlightCount(
                id=book.id.value,
                client_book_id=book.client_book_id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                cover=book.cover,
                description=book.description,
                language=book.language,
                page_count=book.page_count,
                highlight_count=highlight_count,
                flashcard_count=flashcard_count,
                tags=[schemas.TagInBook(id=tag.id.value, name=tag.name) for tag in tags],
                created_at=book.created_at,
                updated_at=book.updated_at,
                last_viewed=book.last_viewed,
            )
            for book, highlight_count, flashcard_count, tags in results
        ]

        return schemas.RecentlyViewedBooksResponse(books=books_list)
    except Exception as e:
        logger.error(f"Failed to fetch recently viewed books: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get("/{book_id}", response_model=schemas.BookDetails, status_code=status.HTTP_200_OK)
def get_book_details(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.BookDetails:
    """
    Get detailed information about a book including its chapters and highlights.

    Args:
        book_id: ID of the book to retrieve
        db: Database session

    Returns:
        BookDetails with chapters and their highlights

    Raises:
        HTTPException: If book is not found or fetching fails
    """
    try:
        service = BookManagementService(db)
        agg = service.get_book_details(book_id, current_user.id)
        db.commit()
        return _build_book_details_schema(agg)
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


@router.get(
    "/{book_id}/highlights",
    response_model=schemas.BookHighlightSearchResponse,
    status_code=status.HTTP_200_OK,
)
def search_book_highlights(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
    search_text: str = Query(
        ...,
        alias="searchText",
        min_length=1,
        description="Text to search for in highlights",
    ),
) -> schemas.BookHighlightSearchResponse:
    """
    Search for highlights in book using full-text search.

    Searches across all highlight text using PostgreSQL full-text search.
    Results are ranked by relevance and excludes soft-deleted highlights.
    """
    try:
        service = BookHighlightSearchService(db)
        chapters_grouped, total = service.search_book_highlights(
            book_id, current_user.id, search_text
        )
        return schemas.BookHighlightSearchResponse(
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


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete a book and all its contents (hard delete).

    This will permanently delete the book, all its chapters, and all its highlights.
    If the user syncs highlights from the book again, it will recreate the book,
    chapters, and highlights.

    Args:
        book_id: ID of the book to delete
        db: Database session

    Raises:
        HTTPException: If book is not found or deletion fails
    """
    try:
        service = BookManagementService(db)
        service.delete_book(book_id, current_user.id)
        db.commit()
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to delete book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.delete(
    "/{book_id}/highlight",
    response_model=schemas.HighlightDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_highlights(
    book_id: int,
    request: schemas.HighlightDeleteRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightDeleteResponse:
    """
    Soft delete highlights from a book.

    This performs a soft delete by marking the highlights as deleted.
    When syncing highlights, deleted highlights will not be recreated,
    ensuring that user deletions persist across syncs.

    Args:
        book_id: ID of the book
        request: Request containing list of highlight IDs to delete
        db: Database session

    Returns:
        HighlightDeleteResponse with deletion status and count

    Raises:
        HTTPException: If book is not found or deletion fails
    """
    try:
        service = BookHighlightDeletionService(db)
        deleted_count = service.delete_highlights(book_id, request.highlight_ids, current_user.id)
        db.commit()
        return schemas.HighlightDeleteResponse(
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


@router.post(
    "/{book_id}/metadata/cover",
    response_model=schemas.CoverUploadResponse,
    status_code=status.HTTP_200_OK,
)
def upload_book_cover(
    book_id: int,
    cover: Annotated[UploadFile, File(...)],
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.CoverUploadResponse:
    """
    Upload a book cover image.

    This endpoint accepts an uploaded image file and saves it as the book's cover.
    The cover is saved to the covers directory with the filename {book_id}.jpg
    and the book's cover field is updated in the database.

    Args:
        book_id: ID of the book
        cover: Uploaded image file (JPEG, PNG, etc.)
        db: Database session

    Returns:
        Success message with the cover URL

    Raises:
        HTTPException: If book is not found or upload fails
    """
    try:
        service = BookCoverService(db)
        cover_url = service.upload_cover(book_id, cover, current_user.id)
        db.commit()
        return schemas.CoverUploadResponse(
            success=True,
            message="Cover uploaded successfully",
            cover_url=cover_url,
        )
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to upload cover for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get("/{book_id}/cover", status_code=status.HTTP_200_OK)
def get_book_cover(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    """
    Get the cover image for a book.

    This endpoint serves the book cover image with user ownership verification.
    Only users who own the book can access its cover.

    Args:
        book_id: ID of the book
        db: Database session
        current_user: Authenticated user

    Returns:
        FileResponse with the book cover image

    Raises:
        HTTPException: If book is not found, user doesn't own it, or cover doesn't exist
    """
    service = BookCoverService(db)
    cover_path = service.get_cover_path(book_id, current_user.id)
    return FileResponse(cover_path, media_type="image/jpeg")


@router.post(
    "/{book_id}",
    response_model=schemas.BookWithHighlightCount,
    status_code=status.HTTP_200_OK,
)
def update_book(
    book_id: int,
    request: schemas.BookUpdateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.BookWithHighlightCount:
    """
    Update book information.

    Currently supports updating tags only. The tags will be replaced with the provided list.

    Args:
        book_id: ID of the book to update
        request: Book update request containing tags
        db: Database session

    Returns:
        Updated book with highlight count and tags

    Raises:
        HTTPException: If book is not found or update fails
    """
    try:
        service = BookManagementService(db)
        book, highlight_count, flashcard_count, tags = service.update_book(
            book_id, request, current_user.id
        )
        db.commit()
        return schemas.BookWithHighlightCount(
            id=book.id.value,
            client_book_id=book.client_book_id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            cover=book.cover,
            description=book.description,
            language=book.language,
            page_count=book.page_count,
            highlight_count=highlight_count,
            flashcard_count=flashcard_count,
            tags=[schemas.TagInBook(id=tag.id.value, name=tag.name) for tag in tags],
            created_at=book.created_at,
            updated_at=book.updated_at,
            last_viewed=book.last_viewed,
        )
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to update book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/{book_id}/highlight_tags",
    response_model=schemas.HighlightTagsResponse,
    status_code=status.HTTP_200_OK,
)
def get_highlight_tags(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightTagsResponse:
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
        tags = service.get_tags_for_book(book_id, current_user.id)
        return schemas.HighlightTagsResponse(
            tags=[
                schemas.HighlightTag(
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
    "/{book_id}/highlight_tag",
    response_model=schemas.HighlightTag,
    status_code=status.HTTP_201_CREATED,
)
def create_highlight_tag(
    book_id: int,
    request: schemas.HighlightTagCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightTag:
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
        tag = service.create_tag(book_id, request.name, user_id=current_user.id)
        return schemas.HighlightTag(
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
    "/{book_id}/highlight_tag/{tag_id}",
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
        deleted = service.delete_tag(book_id, tag_id, current_user.id)
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
    "/{book_id}/highlight_tag/{tag_id}",
    response_model=schemas.HighlightTag,
    status_code=status.HTTP_200_OK,
)
def update_highlight_tag(
    book_id: int,
    tag_id: int,
    request: schemas.HighlightTagUpdateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightTag:
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
                user_id=current_user.id,
            )
        else:
            # Load tag for group update
            tag_repo = HighlightTagRepository(db)
            tag = tag_repo.find_by_id(HighlightTagId(tag_id), UserId(current_user.id))
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
                user_id=current_user.id,
            )

        return schemas.HighlightTag(
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
    "/{book_id}/highlight/{highlight_id}/tag",
    response_model=schemas.Highlight,
    status_code=status.HTTP_200_OK,
)
def add_tag_to_highlight(
    book_id: int,
    highlight_id: int,
    request: schemas.HighlightTagAssociationRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.Highlight:
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
            service.add_tag_by_id(highlight_id, request.tag_id, current_user.id)
        elif request.name is not None:
            service.add_tag_by_name(book_id, highlight_id, request.name, current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either tag_id or name must be provided",
            )

        # Reload highlight with relations to get updated tags
        highlight_repo = HighlightRepository(db)
        result = highlight_repo.find_by_id_with_relations(
            HighlightId(highlight_id), UserId(current_user.id)
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Highlight with id {highlight_id} not found",
            )

        highlight, flashcards, highlight_tags = result

        # Manually construct schema from domain entities
        return schemas.Highlight(
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
                schemas.HighlightTagInBook(
                    id=tag.id.value,
                    name=tag.name,
                    tag_group_id=tag.tag_group_id,
                )
                for tag in highlight_tags
            ],
            flashcards=[
                schemas.Flashcard(
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
    "/{book_id}/highlight/{highlight_id}/tag/{tag_id}",
    response_model=schemas.Highlight,
    status_code=status.HTTP_200_OK,
)
def remove_tag_from_highlight(
    book_id: int,
    highlight_id: int,
    tag_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.Highlight:
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
        service.remove_tag(highlight_id, tag_id, current_user.id)

        # Reload highlight with relations to get updated tags
        highlight_repo = HighlightRepository(db)
        result = highlight_repo.find_by_id_with_relations(
            HighlightId(highlight_id), UserId(current_user.id)
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Highlight with id {highlight_id} not found",
            )

        highlight, flashcards, highlight_tags = result

        # Manually construct schema from domain entities
        return schemas.Highlight(
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
                schemas.HighlightTagInBook(
                    id=tag.id.value,
                    name=tag.name,
                    tag_group_id=tag.tag_group_id,
                )
                for tag in highlight_tags
            ],
            flashcards=[
                schemas.Flashcard(
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


@router.post(
    "/{book_id}/bookmarks",
    response_model=schemas.Bookmark,
    status_code=status.HTTP_201_CREATED,
)
def create_bookmark(
    book_id: int,
    request: schemas.BookmarkCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.Bookmark:
    """
    Create a bookmark for a highlight in a book.

    Bookmarks allow users to track their reading progress by marking specific
    highlights they want to return to later.

    Args:
        book_id: ID of the book
        request: Request containing the highlight_id to bookmark
        db: Database session

    Returns:
        Created Bookmark

    Raises:
        HTTPException: If book or highlight not found, or creation fails
    """
    try:
        service = BookmarkService(db)
        bookmark = service.create_bookmark(book_id, request.highlight_id, current_user.id)

        # Manually construct schema from domain entity
        # created_at is always set for persisted bookmarks
        assert bookmark.created_at is not None
        return schemas.Bookmark(
            id=bookmark.id.value,
            book_id=bookmark.book_id.value,
            highlight_id=bookmark.highlight_id.value,
            created_at=bookmark.created_at,
        )
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to create bookmark for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.delete(
    "/{book_id}/bookmarks/{bookmark_id}",
    status_code=status.HTTP_200_OK,
)
def delete_bookmark(
    book_id: int,
    bookmark_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete a bookmark from a book.

    This operation is idempotent - calling it on a non-existent bookmark
    will succeed and return 200 without error.

    Args:
        book_id: ID of the book
        bookmark_id: ID of the bookmark to delete
        db: Database session

    Raises:
        HTTPException: If book not found or deletion fails
    """
    try:
        service = BookmarkService(db)
        service.delete_bookmark(book_id, bookmark_id, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete bookmark {bookmark_id} for book {book_id}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/{book_id}/bookmarks",
    response_model=schemas.BookmarksResponse,
    status_code=status.HTTP_200_OK,
)
def get_bookmarks(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.BookmarksResponse:
    """
    Get all bookmarks for a book.

    Returns all bookmarks ordered by creation date (newest first).

    Args:
        book_id: ID of the book
        db: Database session

    Returns:
        List of bookmarks for the book

    Raises:
        HTTPException: If book not found or fetching fails
    """
    try:
        service = BookmarkService(db)
        bookmarks = service.get_bookmarks_by_book(book_id, current_user.id)

        # Manually construct schemas from domain entities
        # created_at is always set for persisted bookmarks
        bookmark_schemas = []
        for b in bookmarks:
            assert b.created_at is not None
            bookmark_schemas.append(
                schemas.Bookmark(
                    id=b.id.value,
                    book_id=b.book_id.value,
                    highlight_id=b.highlight_id.value,
                    created_at=b.created_at,
                )
            )
        return schemas.BookmarksResponse(bookmarks=bookmark_schemas)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to get bookmarks for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/{book_id}/flashcards",
    response_model=schemas.FlashcardCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_flashcard_for_book(
    book_id: int,
    request: schemas.FlashcardCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.FlashcardCreateResponse:
    """
    Create a standalone flashcard for a book (without a highlight).

    This creates a flashcard that is associated with a book but not tied
    to any specific highlight.

    Args:
        book_id: ID of the book
        request: Request containing question and answer
        db: Database session

    Returns:
        Created flashcard

    Raises:
        HTTPException: If book not found or creation fails
    """
    try:
        service = FlashcardService(db)
        flashcard_entity = service.create_flashcard_for_book(
            book_id=book_id,
            user_id=current_user.id,
            question=request.question,
            answer=request.answer,
        )
        # Manually construct Pydantic schema from domain entity
        flashcard = schemas.Flashcard(
            id=flashcard_entity.id.value,
            user_id=flashcard_entity.user_id.value,
            book_id=flashcard_entity.book_id.value,
            highlight_id=flashcard_entity.highlight_id.value
            if flashcard_entity.highlight_id
            else None,
            question=flashcard_entity.question,
            answer=flashcard_entity.answer,
        )
        return schemas.FlashcardCreateResponse(
            success=True,
            message="Flashcard created successfully",
            flashcard=flashcard,
        )
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to create flashcard for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/{book_id}/flashcards",
    response_model=schemas.FlashcardsWithHighlightsResponse,
    status_code=status.HTTP_200_OK,
)
def get_flashcards_for_book(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.FlashcardsWithHighlightsResponse:
    """
    Get all flashcards for a book with embedded highlight data.

    Returns all flashcards ordered by creation date (newest first).

    Args:
        book_id: ID of the book
        db: Database session

    Returns:
        List of flashcards with highlight data for the book

    Raises:
        HTTPException: If book not found or fetching fails
    """
    try:
        # Get flashcards with highlights from service (returns DTOs)
        service = FlashcardService(db)
        flashcards_with_highlights = service.get_flashcards_by_book(book_id, current_user.id)

        # Convert DTOs to Pydantic schemas
        flashcards = []
        for dto in flashcards_with_highlights:
            fc = dto.flashcard
            highlight = dto.highlight
            chapter = dto.chapter
            tags = dto.highlight_tags

            # Convert highlight to Pydantic schema if present
            highlight_schema = None
            if highlight:
                # Extract xpoint strings
                start_xpoint = str(highlight.xpoints.start) if highlight.xpoints else None
                end_xpoint = str(highlight.xpoints.end) if highlight.xpoints else None

                # Manually construct highlight schema
                highlight_schema = schemas.HighlightResponseBase(
                    id=highlight.id.value,
                    book_id=highlight.book_id.value,
                    chapter_id=highlight.chapter_id.value if highlight.chapter_id else None,
                    text=highlight.text,
                    note=highlight.note,
                    page=highlight.page,
                    start_xpoint=start_xpoint,
                    end_xpoint=end_xpoint,
                    datetime=highlight.datetime,
                    chapter=chapter.name if chapter else None,
                    chapter_number=chapter.chapter_number if chapter else None,
                    created_at=highlight.created_at,
                    updated_at=highlight.updated_at,
                    highlight_tags=[
                        schemas.HighlightTagInBook(
                            id=tag.id.value,
                            name=tag.name,
                            tag_group_id=tag.tag_group_id,
                        )
                        for tag in tags
                    ],
                )

            # Construct flashcard schema with highlight
            flashcard_schema = schemas.FlashcardWithHighlight(
                id=fc.id.value,
                user_id=fc.user_id.value,
                book_id=fc.book_id.value,
                highlight_id=fc.highlight_id.value if fc.highlight_id else None,
                question=fc.question,
                answer=fc.answer,
                highlight=highlight_schema,
            )
            flashcards.append(flashcard_schema)

        return schemas.FlashcardsWithHighlightsResponse(flashcards=flashcards)
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to get flashcards for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/{book_id}/reading_sessions",
    response_model=schemas.ReadingSessionsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_book_reading_sessions(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(30, ge=1, le=1000, description="Maximum sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
) -> schemas.ReadingSessionsResponse:
    """
    Get reading sessions for a specific book.

    Returns reading sessions ordered by start time (newest first).

    Args:
        book_id: ID of the book
        db: Database session
        limit: Maximum number of sessions
        offset: Pagination offset

    Returns:
        ReadingSessionsResponse with sessions list
    """
    try:
        service = ReadingSessionService(db)
        return await service.get_reading_sessions_for_book(book_id, current_user.id, limit, offset)
    except CrossbillError:
        raise
    except Exception as e:
        logger.error(f"Failed to get reading sessions for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
