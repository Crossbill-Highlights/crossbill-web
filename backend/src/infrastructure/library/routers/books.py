import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from starlette.responses import FileResponse

from src.application.library.use_cases.book_files.book_cover_use_case import BookCoverUseCase
from src.application.library.use_cases.book_management.delete_book_use_case import (
    DeleteBookUseCase,
)
from src.application.library.use_cases.book_management.get_book_details_use_case import (
    GetBookDetailsUseCase,
)
from src.application.library.use_cases.book_management.update_book_use_case import (
    UpdateBookUseCase,
)
from src.application.library.use_cases.book_queries.get_books_with_counts_use_case import (
    GetBooksWithCountsUseCase,
)
from src.application.library.use_cases.book_queries.get_recently_viewed_books_use_case import (
    GetRecentlyViewedBooksUseCase,
)
from src.core import container
from src.domain.common import DomainError
from src.domain.identity import User
from src.domain.library.services.book_details_aggregator import BookDetailsAggregation
from src.domain.reading.services import ChapterWithHighlights as DomainChapterWithHighlights
from src.exceptions import CrossbillError
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.learning.schemas import Flashcard
from src.infrastructure.library.schemas import (
    BooksListResponse,
    BookUpdateRequest,
    BookWithHighlightCount,
    RecentlyViewedBooksResponse,
    TagInBook,
)
from src.infrastructure.reading.schemas import (
    BookDetails,
    Bookmark,
    Highlight,
    HighlightTagGroupInBook,
    HighlightTagInBook,
)
from src.infrastructure.reading.schemas import (
    ChapterWithHighlights as ChapterWithHighlightsSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


def _map_chapters_to_schemas(
    chapters_grouped: list[DomainChapterWithHighlights],
) -> list[ChapterWithHighlightsSchema]:
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
                created_at=h.created_at,
                updated_at=h.updated_at,
            )
            highlight_schemas.append(highlight_schema)

        # Get chapter info from first highlight's chapter
        first_chapter = chapter_group.highlights[0].chapter if chapter_group.highlights else None

        chapter_with_highlights = ChapterWithHighlightsSchema(
            id=chapter_group.chapter_id,
            name=chapter_group.chapter_name or "",
            chapter_number=chapter_group.chapter_number,
            parent_id=chapter_group.parent_id,
            highlights=highlight_schemas,
            created_at=first_chapter.created_at if first_chapter else datetime.now(UTC),
            updated_at=first_chapter.created_at if first_chapter else datetime.now(UTC),
        )
        chapters_with_highlights.append(chapter_with_highlights)

    return chapters_with_highlights


def _build_book_details_schema(agg: BookDetailsAggregation) -> BookDetails:
    """
    Build BookDetails Pydantic schema from BookDetailsAggregation.

    Args:
        agg: BookDetailsAggregation domain dataclass

    Returns:
        BookDetails Pydantic schema
    """
    return BookDetails(
        id=agg.book.id.value,
        client_book_id=agg.book.client_book_id,
        title=agg.book.title,
        author=agg.book.author,
        isbn=agg.book.isbn,
        cover=agg.book.cover,
        description=agg.book.description,
        language=agg.book.language,
        page_count=agg.book.page_count,
        tags=[TagInBook(id=tag.id.value, name=tag.name) for tag in agg.tags],
        highlight_tags=[
            HighlightTagInBook(
                id=tag.id.value,
                name=tag.name,
                tag_group_id=tag.tag_group_id,
            )
            for tag in agg.highlight_tags
        ],
        highlight_tag_groups=[
            HighlightTagGroupInBook(
                id=group.id.value,
                name=group.name,
            )
            for group in agg.highlight_tag_groups
        ],
        bookmarks=[
            Bookmark(
                id=b.id.value,
                book_id=b.book_id.value,
                highlight_id=b.highlight_id.value,
                created_at=b.created_at,
            )
            for b in agg.bookmarks
        ],
        book_flashcards=[
            Flashcard(
                id=f.id.value,
                user_id=f.user_id.value,
                book_id=f.book_id.value,
                highlight_id=None,
                question=f.question,
                answer=f.answer,
            )
            for f in agg.book_flashcards
        ],
        chapters=_map_chapters_to_schemas(agg.chapters_with_highlights),
        created_at=agg.book.created_at,
        updated_at=agg.book.updated_at,
        last_viewed=agg.book.last_viewed,
    )


@router.get("/", response_model=BooksListResponse, status_code=status.HTTP_200_OK)
def get_books(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetBooksWithCountsUseCase = Depends(
        inject_use_case(container.get_books_with_counts_use_case)
    ),
    offset: int = Query(0, ge=0, description="Number of books to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of books to return"),
    only_with_flashcards: bool = Query(False, description="Return only books with flashcards"),
    search: str | None = Query(None, description="Search text to filter books by title or author"),
) -> BooksListResponse:
    """
    Get all books with their highlight counts, sorted alphabetically by title.

    Args:
        offset: Number of books to skip (for pagination)
        limit: Maximum number of books to return (for pagination)
        search: Optional search text to filter books by title or author

    Returns:
        BooksListResponse with list of books and pagination info

    Raises:
        HTTPException: If fetching books fails due to server error
    """
    try:
        results, total = use_case.get_books_with_counts(
            current_user.id.value, offset, limit, only_with_flashcards, search
        )

        books_list = [
            BookWithHighlightCount(
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
                tags=[TagInBook(id=tag.id.value, name=tag.name) for tag in tags],
                created_at=book.created_at,
                updated_at=book.updated_at,
                last_viewed=book.last_viewed,
            )
            for book, highlight_count, flashcard_count, tags in results
        ]

        return BooksListResponse(books=books_list, total=total, offset=offset, limit=limit)
    except Exception as e:
        logger.error(f"Failed to fetch books: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/recently-viewed",
    response_model=RecentlyViewedBooksResponse,
    status_code=status.HTTP_200_OK,
)
def get_recently_viewed_books(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetRecentlyViewedBooksUseCase = Depends(
        inject_use_case(container.get_recently_viewed_books_use_case)
    ),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of books to return"),
) -> RecentlyViewedBooksResponse:
    """
    Get recently viewed books with their highlight counts.

    Returns books that have been viewed at least once, ordered by most recently viewed.

    Args:
        limit: Maximum number of books to return (default: 10, max: 50)

    Returns:
        RecentlyViewedBooksResponse with list of recently viewed books

    Raises:
        HTTPException: If fetching books fails due to server error
    """
    try:
        results = use_case.get_recently_viewed(current_user.id.value, limit)

        books_list = [
            BookWithHighlightCount(
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
                tags=[TagInBook(id=tag.id.value, name=tag.name) for tag in tags],
                created_at=book.created_at,
                updated_at=book.updated_at,
                last_viewed=book.last_viewed,
            )
            for book, highlight_count, flashcard_count, tags in results
        ]

        return RecentlyViewedBooksResponse(books=books_list)
    except Exception as e:
        logger.error(f"Failed to fetch recently viewed books: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get("/{book_id}", response_model=BookDetails, status_code=status.HTTP_200_OK)
def get_book_details(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetBookDetailsUseCase = Depends(inject_use_case(container.get_book_details_use_case)),
) -> BookDetails:
    """
    Get detailed information about a book including its chapters and highlights.

    Args:
        book_id: ID of the book to retrieve

    Returns:
        BookDetails with chapters and their highlights

    Raises:
        HTTPException: If book is not found or fetching fails
    """
    try:
        agg = use_case.get_book_details(book_id, current_user.id.value)
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
    response_model=BookWithHighlightCount,
    status_code=status.HTTP_200_OK,
)
def update_book(
    book_id: int,
    request: BookUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: UpdateBookUseCase = Depends(inject_use_case(container.update_book_use_case)),
) -> BookWithHighlightCount:
    """
    Update book information.

    Currently supports updating tags only. The tags will be replaced with the provided list.

    Args:
        book_id: ID of the book to update
        request: Book update request containing tags

    Returns:
        Updated book with highlight count and tags

    Raises:
        HTTPException: If book is not found or update fails
    """
    try:
        book, highlight_count, flashcard_count, tags = use_case.update_book(
            book_id, request, current_user.id.value
        )
        return BookWithHighlightCount(
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
            tags=[TagInBook(id=tag.id.value, name=tag.name) for tag in tags],
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
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: DeleteBookUseCase = Depends(inject_use_case(container.delete_book_use_case)),
) -> None:
    """
    Delete a book and all its contents (hard delete).

    This will permanently delete the book, all its chapters, and all its highlights.
    If the user syncs highlights from the book again, it will recreate the book,
    chapters, and highlights.

    Args:
        book_id: ID of the book to delete

    Raises:
        HTTPException: If book is not found or deletion fails
    """
    try:
        use_case.delete_book(book_id, current_user.id.value)
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
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: BookCoverUseCase = Depends(inject_use_case(container.book_cover_use_case)),
) -> FileResponse:
    """
    Get the cover image for a book.

    This endpoint serves the book cover image with user ownership verification.
    Only users who own the book can access its cover.

    Args:
        book_id: ID of the book
        current_user: Authenticated user

    Returns:
        FileResponse with the book cover image

    Raises:
        HTTPException: If book is not found, user doesn't own it, or cover doesn't exist
    """
    cover_path = use_case.get_cover_path(book_id, current_user.id.value)
    return FileResponse(cover_path, media_type="image/jpeg")
