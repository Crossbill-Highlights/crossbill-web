"""API routes for books management."""

import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from crossbill import repositories, schemas
from crossbill.database import DatabaseSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/book", tags=["books"])

# Directory for book cover images
COVERS_DIR = Path(__file__).parent.parent.parent / "book-covers"


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
        # Get the book
        book_repo = repositories.BookRepository(db)
        book = book_repo.get_by_id(book_id)

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found",
            )

        # Get chapters for the book
        chapter_repo = repositories.ChapterRepository(db)
        chapters = chapter_repo.get_by_book_id(book_id)

        # Get highlights for each chapter
        highlight_repo = repositories.HighlightRepository(db)

        chapters_with_highlights = []
        for chapter in chapters:
            highlights = highlight_repo.find_by_chapter(chapter.id)

            # Convert highlights to schema
            highlight_schemas = [
                schemas.Highlight(
                    id=h.id,
                    book_id=h.book_id,
                    chapter_id=h.chapter_id,
                    text=h.text,
                    chapter=None,  # Not needed in response
                    page=h.page,
                    note=h.note,
                    datetime=h.datetime,
                    created_at=h.created_at,
                    updated_at=h.updated_at,
                )
                for h in highlights
            ]

            chapter_with_highlights = schemas.ChapterWithHighlights(
                id=chapter.id,
                name=chapter.name,
                chapter_number=chapter.chapter_number,
                highlights=highlight_schemas,
                created_at=chapter.created_at,
                updated_at=chapter.updated_at,
            )
            chapters_with_highlights.append(chapter_with_highlights)

        # Create the response
        return schemas.BookDetails(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            cover=book.cover,
            chapters=chapters_with_highlights,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
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
        book_repo = repositories.BookRepository(db)
        deleted = book_repo.delete(book_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found",
            )

        logger.info(f"Successfully deleted book {book_id}")
    except HTTPException:
        # Re-raise HTTP exceptions as-is
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
        # Verify book exists
        book_repo = repositories.BookRepository(db)
        book = book_repo.get_by_id(book_id)

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found",
            )

        # Soft delete highlights
        highlight_repo = repositories.HighlightRepository(db)
        deleted_count = highlight_repo.soft_delete_by_ids(book_id, request.highlight_ids)

        return schemas.HighlightDeleteResponse(
            success=True,
            message=f"Successfully deleted {deleted_count} highlight(s)",
            deleted_count=deleted_count,
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
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
    cover: UploadFile = File(...),
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
        # Verify book exists
        book_repo = repositories.BookRepository(db)
        book = book_repo.get_by_id(book_id)

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found",
            )

        # Ensure covers directory exists
        COVERS_DIR.mkdir(parents=True, exist_ok=True)

        # Save the uploaded file
        cover_filename = f"{book_id}.jpg"
        cover_path = COVERS_DIR / cover_filename

        # Read and write the file content
        content = cover.file.read()
        cover_path.write_bytes(content)

        logger.info(f"Successfully saved cover for book {book_id} at {cover_path}")

        # Update book's cover field in database
        cover_url = f"/media/covers/{cover_filename}"
        book.cover = cover_url
        db.commit()

        return schemas.CoverUploadResponse(
            success=True,
            message="Cover uploaded successfully",
            cover_url=cover_url,
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Failed to upload cover for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload cover: {e!s}",
        ) from e
