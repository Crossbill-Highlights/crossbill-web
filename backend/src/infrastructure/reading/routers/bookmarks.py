import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.infrastructure.reading.schemas import Bookmark, BookmarkCreateRequest, BookmarksResponse
from src.application.reading.services import BookmarkService
from src.database import DatabaseSession
from src.domain.identity import User
from src.exceptions import CrossbillError
from src.infrastructure.identity import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["bookmarks"])


@router.post(
    "/{book_id}/bookmarks",
    response_model=Bookmark,
    status_code=status.HTTP_201_CREATED,
)
def create_bookmark(
    book_id: int,
    request: BookmarkCreateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Bookmark:
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
        bookmark = service.create_bookmark(book_id, request.highlight_id, current_user.id.value)

        # Manually construct schema from domain entity
        # created_at is always set for persisted bookmarks
        assert bookmark.created_at is not None
        return Bookmark(
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
        service.delete_bookmark(book_id, bookmark_id, current_user.id.value)
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
    response_model=BookmarksResponse,
    status_code=status.HTTP_200_OK,
)
def get_bookmarks(
    book_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> BookmarksResponse:
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
        bookmarks = service.get_bookmarks_by_book(book_id, current_user.id.value)

        # Manually construct schemas from domain entities
        # created_at is always set for persisted bookmarks
        bookmark_schemas = []
        for b in bookmarks:
            assert b.created_at is not None
            bookmark_schemas.append(
                Bookmark(
                    id=b.id.value,
                    book_id=b.book_id.value,
                    highlight_id=b.highlight_id.value,
                    created_at=b.created_at,
                )
            )
        return BookmarksResponse(bookmarks=bookmark_schemas)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to get bookmarks for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
