"""API routes for books management."""

import logging
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src import schemas
from src.database import DatabaseSession
from src.exceptions import CrossbillError
from src.services import BookService, HighlightTagService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/book", tags=["books"])


@router.get("/{book_id}", response_model=schemas.BookDetails, status_code=status.HTTP_200_OK)
def get_book_details(
    book_id: int,
    db: DatabaseSession,
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
        return service.get_book_details(book_id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to fetch book details for book_id={book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch book details: {e!s}",
        ) from e


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: DatabaseSession,
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
        service.delete_book(book_id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to delete book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete book: {e!s}",
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
        return service.delete_highlights(book_id, request.highlight_ids)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to delete highlights for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete highlights: {e!s}",
        ) from e


@router.post(
    "/{book_id}/metadata/cover",
    response_model=schemas.CoverUploadResponse,
    status_code=status.HTTP_200_OK,
)
def upload_book_cover(
    book_id: int,
    cover: Annotated[UploadFile, File(...)],
    db: DatabaseSession = None,
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
        return service.upload_cover(book_id, cover)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to upload cover for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload cover: {e!s}",
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
        return service.update_book(book_id, request)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to update book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update book: {e!s}",
        ) from e


@router.get(
    "/{book_id}/highlight_tags",
    response_model=schemas.HighlightTagsResponse,
    status_code=status.HTTP_200_OK,
)
def get_highlight_tags(
    book_id: int,
    db: DatabaseSession,
) -> schemas.HighlightTag:
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
        tags = service.get_tags_for_book(book_id)
        return schemas.HighlightTagsResponse(tags=tags)
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
        return service.create_tag_for_book(book_id, request.name)
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
            detail=f"Failed to create highlight tag: {e!s}",
        ) from e


@router.delete(
    "/{book_id}/highlight_tag/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_highlight_tag(
    book_id: int,
    tag_id: int,
    db: DatabaseSession,
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
        deleted = service.delete_tag(book_id, tag_id)
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
            f"Failed to delete highlight tag {tag_id} for book {book_id}: {e!s}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete highlight tag: {e!s}",
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
            highlight = service.add_tag_to_highlight(highlight_id, request.tag_id)
        elif request.name is not None:
            highlight = service.add_tag_to_highlight_by_name(book_id, highlight_id, request.name)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either tag_id or name must be provided",
            )

        return highlight
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
            f"Failed to add tag to highlight {highlight_id}: {e!s}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add tag to highlight: {e!s}",
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
        highlight = service.remove_tag_from_highlight(highlight_id, tag_id)
        return highlight
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
            f"Failed to remove tag from highlight {highlight_id}: {e!s}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove tag from highlight: {e!s}",
        ) from e
