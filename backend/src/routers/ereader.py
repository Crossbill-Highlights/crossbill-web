"""API routes for ereader operations."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src import schemas
from src.database import DatabaseSession
from src.exceptions import CrossbillError
from src.models import User
from src.services.auth_service import get_current_user
from src.services.book_service import BookService
from src.services.ebook.ebook_service import EbookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ereader", tags=["ereader"])


@router.post(
    "/books",
    response_model=schemas.EreaderBookMetadata,
    status_code=status.HTTP_200_OK,
)
def create_book(
    book_data: schemas.BookCreate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.EreaderBookMetadata:
    """
    Create or get a book by client_book_id.

    This endpoint creates a new book if it doesn't exist, or returns the existing
    book's metadata if it does. Used by KOReader to ensure a book exists before
    uploading highlights, covers, or EPUB files.

    Args:
        book_data: Book creation data (same format as highlight upload)
        db: Database session
        current_user: Authenticated user

    Returns:
        EreaderBookMetadata with book_id, bookname, author, has_cover, has_epub
    """
    try:
        service = BookService(db)
        service.create_book(book_data, current_user.id)

        # Commit the book creation
        db.commit()

        # Return metadata in the same format as GET /ereader/books/{client_book_id}
        return service.get_book_metadata_for_ereader(book_data.client_book_id, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(
            f"Failed to create book: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/books/{client_book_id}",
    response_model=schemas.EreaderBookMetadata,
    status_code=status.HTTP_200_OK,
)
def get_book_metadata(
    client_book_id: str,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.EreaderBookMetadata:
    """
    Get basic book metadata by client_book_id for ereader operations.

    This endpoint returns lightweight book information that KOReader uses to
    decide whether it needs to upload cover images, epub files, etc.

    Args:
        client_book_id: The client-provided stable book identifier
        db: Database session
        current_user: Authenticated user

    Returns:
        EreaderBookMetadata with book_id, bookname, author, hasCover, hasEpub

    Raises:
        HTTPException: 404 if book is not found
    """
    try:
        service = BookService(db)
        return service.get_book_metadata_for_ereader(client_book_id, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(
            f"Failed to get book metadata for client_book_id={client_book_id}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.post(
    "/books/{client_book_id}/cover",
    response_model=schemas.CoverUploadResponse,
    status_code=status.HTTP_200_OK,
)
def upload_book_cover(
    client_book_id: str,
    cover: Annotated[UploadFile, File(...)],
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.CoverUploadResponse:
    """
    Upload a book cover image using client_book_id.

    This endpoint accepts an uploaded image file and saves it as the book's cover.
    Used by KOReader which identifies books by client_book_id.

    Args:
        client_book_id: The client-provided stable book identifier
        cover: Uploaded image file (JPEG, PNG, or WebP)
        db: Database session
        current_user: Authenticated user

    Returns:
        CoverUploadResponse with success status and cover URL

    Raises:
        HTTPException: 404 if book is not found, or if upload fails
    """
    try:
        service = BookService(db)
        return service.upload_cover_by_client_book_id(client_book_id, cover, current_user.id)
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(
            f"Failed to upload cover for client_book_id={client_book_id}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


# Maximum ebook file size (50MB - epubs and PDFs can be large)
MAX_EBOOK_SIZE = 50 * 1024 * 1024


@router.post(
    "/books/{client_book_id}/epub",
    response_model=schemas.EpubUploadResponse,
    status_code=status.HTTP_200_OK,
)
def upload_book_epub(
    client_book_id: str,
    epub: Annotated[UploadFile, File(...)],
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.EpubUploadResponse:
    """
    Upload an ebook file (EPUB) for a book using client_book_id.

    This endpoint accepts an uploaded ebook file and saves it for the book.
    Used by KOReader which identifies books by client_book_id.

    Args:
        client_book_id: The client-provided stable book identifier
        epub: Uploaded ebook file (EPUB or PDF)
        db: Database session
        current_user: Authenticated user

    Returns:
        EpubUploadResponse with success status

    Raises:
        HTTPException: 400 for invalid file, 404 if book is not found
    """
    try:
        # Validate content-type
        allowed_types = {"application/epub+zip"}
        if epub.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only EPUB and PDF files are allowed",
            )

        # Read file with size limit
        content = epub.file.read(MAX_EBOOK_SIZE + 1)
        if len(content) > MAX_EBOOK_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large (max {MAX_EBOOK_SIZE // (1024 * 1024)}MB)",
            )

        # Upload the ebook through service layer
        service = EbookService(db)
        service.upload_ebook(client_book_id, content, epub.content_type or "", current_user.id)

        # Commit the database update
        db.commit()

        return schemas.EpubUploadResponse(
            success=True,
            message="Ebook uploaded successfully",
        )
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(
            f"Failed to upload ebook for client_book_id={client_book_id}: {e!s}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
