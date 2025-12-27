"""API routes for books management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from src import schemas
from src.database import DatabaseSession
from src.exceptions import CrossbillError
from src.models import User
from src.services import BookmarkService, BookService, FlashcardService, HighlightTagService
from src.services.auth_service import get_current_user
from src.services.highlight_service import HighlightService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=schemas.BooksListResponse, status_code=status.HTTP_200_OK)
def get_books(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
    offset: int = Query(0, ge=0, description="Number of books to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of books to return"),
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
        return service.get_books_with_counts(current_user.id, offset, limit, search)
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
        service = HighlightService(db)
        return service.get_recently_viewed_books(current_user.id, limit)
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
        service = BookService(db)
        return service.get_book_details(book_id, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
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
        service = BookService(db)
        service.delete_book(book_id, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
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
        service = BookService(db)
        return service.delete_highlights(book_id, request.highlight_ids, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
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
        service = BookService(db)
        return service.upload_cover(book_id, cover, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
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
    service = BookService(db)
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
        service = BookService(db)
        return service.update_book(book_id, request, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
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
            tags=[schemas.HighlightTag.model_validate(tag) for tag in tags]
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
        tag = service.create_tag_for_book(book_id, request.name, user_id=current_user.id)
        return schemas.HighlightTag.model_validate(tag)
    except CrossbillError:
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
        service = HighlightTagService(db)
        tag = service.update_tag(
            book_id=book_id,
            tag_id=tag_id,
            user_id=current_user.id,
            name=request.name,
            tag_group_id=request.tag_group_id,
        )
        return schemas.HighlightTag.model_validate(tag)
    except CrossbillError as e:
        raise HTTPException(
            status_code=e.status_code,
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
        service = HighlightTagService(db)

        # Add tag by ID or by name (with get_or_create)
        if request.tag_id is not None:
            highlight = service.add_tag_to_highlight(highlight_id, request.tag_id, current_user.id)
        elif request.name is not None:
            highlight = service.add_tag_to_highlight_by_name(
                book_id, highlight_id, request.name, current_user.id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either tag_id or name must be provided",
            )

        return schemas.Highlight.model_validate(highlight)
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
        service = HighlightTagService(db)
        highlight = service.remove_tag_from_highlight(highlight_id, tag_id, current_user.id)
        return schemas.Highlight.model_validate(highlight)
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
        return service.create_bookmark(book_id, request.highlight_id, current_user.id)
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
        return service.get_bookmarks_by_book(book_id, current_user.id)
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
        flashcard = service.create_flashcard_for_book(
            book_id=book_id,
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
        service = FlashcardService(db)
        return service.get_flashcards_by_book(book_id, current_user.id)
    except CrossbillError:
        raise
    except Exception as e:
        logger.error(f"Failed to get flashcards for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
