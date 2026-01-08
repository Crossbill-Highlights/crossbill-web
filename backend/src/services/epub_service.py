"""Service layer for epub-related operations."""

import logging
import re
from io import BytesIO
from pathlib import Path

from ebooklib import epub
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from src import repositories
from src.exceptions import BookNotFoundError

logger = logging.getLogger(__name__)

# Directory for epub files (parallel to book-covers)
EPUBS_DIR = Path(__file__).parent.parent.parent / "epubs"

# Maximum epub file size (50MB - epubs are larger than covers)
MAX_EPUB_SIZE = 50 * 1024 * 1024


def _sanitize_filename(text: str) -> str:
    """
    Sanitize text for use in filename.

    Removes/replaces characters that are invalid in filenames.
    Limits length to prevent overly long filenames.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for filenames
    """
    # Remove invalid filename characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", text)
    # Replace spaces and other whitespace with underscores
    sanitized = re.sub(r"\s+", "_", sanitized)
    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip("_.")
    # Limit length (leave room for book_id and extension)
    max_length = 100
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def _validate_epub(content: bytes) -> bool:
    """
    Validate epub file using ebooklib.

    This performs lightweight validation by attempting to read
    the epub structure. Full validation would be too slow for upload.

    Args:
        content: The file content as bytes

    Returns:
        True if valid epub, False otherwise
    """
    try:
        # Create a temporary file-like object from bytes
        epub_file = BytesIO(content)

        # Try to read the epub - ebooklib will raise exception if invalid
        book = epub.read_epub(epub_file)

        # Basic validation: epub should have some metadata
        if not book.get_metadata("DC", "title"):
            logger.warning("EPUB missing title metadata")
            # Allow epubs without metadata (user explicitly uploading)

        return True

    except Exception as e:
        logger.error(f"EPUB validation failed: {e!s}")
        return False


class EpubService:
    """Service for handling epub file operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = repositories.BookRepository(db)

    def upload_epub(self, book_id: int, epub_file: UploadFile, user_id: int) -> tuple[str, str]:
        """
        Upload and validate an epub file for a book.

        This method:
        1. Validates the book exists and belongs to user
        2. Checks file is epub format
        3. Validates epub structure using ebooklib
        4. Generates sanitized filename from book title and ID
        5. Saves file to epubs directory
        6. Removes old epub file if filename differs
        7. Updates book.epub_path in database

        Args:
            book_id: ID of the book
            epub_file: Uploaded epub file
            user_id: ID of the user uploading the epub

        Returns:
            tuple[str, str]: (epub_path_for_db, absolute_file_path)

        Raises:
            BookNotFoundError: If book not found or doesn't belong to user
            HTTPException: If validation fails or upload fails
        """
        # Verify book exists and belongs to user
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        # Check content-type header
        allowed_types = {"application/epub+zip"}
        if epub_file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Only EPUB files are allowed")

        # Read with size limit
        content = epub_file.file.read(MAX_EPUB_SIZE + 1)
        if len(content) > MAX_EPUB_SIZE:
            raise HTTPException(
                status_code=400, detail=f"File too large (max {MAX_EPUB_SIZE // (1024 * 1024)}MB)"
            )

        # Validate epub structure
        if not _validate_epub(content):
            raise HTTPException(status_code=400, detail="Invalid EPUB file")

        # Create epubs directory if it doesn't exist
        EPUBS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename: sanitized_title_bookid.epub
        sanitized_title = _sanitize_filename(book.title)
        epub_filename = f"{sanitized_title}_{book_id}.epub"
        epub_path = EPUBS_DIR / epub_filename

        # Check if book already has an epub file
        old_epub_path = None
        if book.epub_path:
            old_epub_path = EPUBS_DIR / book.epub_path

        # Save new epub file
        epub_path.write_bytes(content)
        logger.info(f"Successfully saved epub for book {book_id} at {epub_path}")

        # Delete old epub file if it exists and has different name
        if old_epub_path and old_epub_path != epub_path and old_epub_path.exists():
            try:
                old_epub_path.unlink()
                logger.info(f"Deleted old epub file: {old_epub_path}")
            except Exception as e:
                logger.warning(f"Failed to delete old epub file {old_epub_path}: {e!s}")

        # Update book's epub_path field in database (store just the filename)
        book.epub_path = epub_filename
        self.db.flush()

        return epub_filename, str(epub_path)

    def get_epub_path(self, book_id: int, user_id: int) -> Path:
        """
        Get the file path for a book's epub file with ownership verification.

        Args:
            book_id: ID of the book
            user_id: ID of the user requesting the epub

        Returns:
            Path to the epub file

        Raises:
            BookNotFoundError: If book not found or user doesn't own it
            HTTPException: If epub file doesn't exist
        """
        book = self.book_repo.get_by_id(book_id, user_id)

        if not book or not book.epub_path:
            raise HTTPException(status_code=404, detail="EPUB file not found")

        epub_path = EPUBS_DIR / book.epub_path

        if not epub_path.exists() or not epub_path.is_file():
            raise HTTPException(status_code=404, detail="EPUB file not found")

        return epub_path

    def upload_epub_by_client_book_id(
        self, client_book_id: str, epub_file: UploadFile, user_id: int
    ) -> tuple[str, str]:
        """
        Upload and validate an epub file for a book using client_book_id.

        This method looks up the book by client_book_id and then uploads the epub.
        Used by KOReader which identifies books by client_book_id.

        Args:
            client_book_id: The client-provided book identifier
            epub_file: Uploaded epub file
            user_id: ID of the user uploading the epub

        Returns:
            tuple[str, str]: (epub_path_for_db, absolute_file_path)

        Raises:
            BookNotFoundError: If book not found for the given client_book_id
            HTTPException: If validation fails or upload fails
        """
        book = self.book_repo.find_by_client_book_id(client_book_id, user_id)

        if not book:
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found"
            )

        # Delegate to the existing upload_epub method using book.id
        return self.upload_epub(book.id, epub_file, user_id)

    def delete_epub(self, book_id: int) -> bool:
        """
        Delete the epub file for a book.

        This is called when a book is deleted.
        Does not verify ownership - caller must do that.

        Args:
            book_id: ID of the book

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        # Find epub file for this book using glob pattern
        epub_files = list(EPUBS_DIR.glob(f"*_{book_id}.epub"))

        if not epub_files:
            return False

        epub_path = epub_files[0]

        try:
            epub_path.unlink()
            logger.info(f"Deleted epub file for book {book_id}: {epub_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete epub file {epub_path}: {e!s}")
            return False
