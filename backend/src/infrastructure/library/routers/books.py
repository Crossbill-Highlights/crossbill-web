import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from starlette.responses import FileResponse

from src import schemas
from src.application.library.services import BookManagementService, GetBooksWithCountsService
from src.application.library.services.book_cover_service import BookCoverService
from src.application.library.services.get_recently_viewed_books_service import (
    GetRecentlyViewedBooksService,
)
from src.database import DatabaseSession
from src.domain.common import DomainError
from src.domain.identity import User
from src.domain.library.services.book_details_aggregator import BookDetailsAggregation
from src.domain.reading.services import ChapterWithHighlights
from src.exceptions import CrossbillError
from src.infrastructure.identity import get_current_user

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
            schemas.HighlightTagGroupInBook(
                id=group.id.value,
                name=group.name,
            )
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
        service = GetBooksWithCountsService(db)
        results, total = service.get_books_with_counts(
            current_user.id.value, offset, limit, only_with_flashcards, search
        )

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

        return schemas.BooksListResponse(books=books_list, total=total, offset=offset, limit=limit)
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
        results = service.get_recently_viewed(current_user.id.value, limit)

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
        agg = service.get_book_details(book_id, current_user.id.value)
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
            book_id, request, current_user.id.value
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
        service.delete_book(book_id, current_user.id.value)
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
    cover_path = service.get_cover_path(book_id, current_user.id.value)
    return FileResponse(cover_path, media_type="image/jpeg")
