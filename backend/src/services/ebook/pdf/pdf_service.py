"""
PDF Service - Handles PDF file operations

This service provides PDF-specific functionality for the ebook system.
Currently partially stubbed - file operations are implemented but upload
and text extraction require PDF parsing libraries (pypdf, pdfplumber, etc.)
"""

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from src import repositories
from src.config import PDFS_DIR
from src.exceptions import BookNotFoundError

# Module-level constants
logger = logging.getLogger(__name__)


class PdfService:
    """Service for handling PDF ebook operations."""

    def __init__(self, db: Session) -> None:
        """
        Initialize the PDF service.

        Args:
            db: Database session
        """
        self.db = db
        self.book_repo = repositories.BookRepository(db)
        self.chapter_repo = repositories.ChapterRepository(db)

        # Create PDFs directory if it doesn't exist
        PDFS_DIR.mkdir(parents=True, exist_ok=True)

    def get_pdf_path(self, book_id: int, user_id: int) -> Path:
        """
        Get the filesystem path to a PDF file.

        Args:
            book_id: The book ID
            user_id: The user ID (for ownership verification)

        Returns:
            Path to the PDF file

        Raises:
            BookNotFoundError: If the book doesn't exist, doesn't belong to the user,
                             or doesn't have a PDF file
        """
        # Fetch book and verify ownership
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        # Verify book has a PDF file
        if not book.file_path or book.file_type != "pdf":
            raise BookNotFoundError(book_id)

        return PDFS_DIR / book.file_path

    def upload_pdf_by_client_book_id(
        self, client_book_id: str, content: bytes, user_id: int
    ) -> tuple[str, str]:
        """
        Upload a PDF file for a book identified by client_book_id.

        Args:
            client_book_id: Client-provided book identifier
            content: The PDF file content as bytes
            user_id: The user ID

        Returns:
            Tuple of (filename, absolute_file_path)

        Raises:
            NotImplementedError: PDF upload not yet implemented
        """
        logger.warning("PDF upload is not yet implemented")
        raise NotImplementedError(
            "PDF file support is coming soon. Currently only EPUB files are supported."
        )

    def delete_pdf(self, book_id: int) -> bool:
        """
        Delete the PDF file for a book.

        This is called when a book is deleted.
        Does not verify ownership - caller must do that.

        Args:
            book_id: ID of the book

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        # Find PDF file for this book using glob pattern
        pdf_files = list(PDFS_DIR.glob(f"*_{book_id}.pdf"))

        if not pdf_files:
            return False

        pdf_path = pdf_files[0]

        try:
            pdf_path.unlink()
            logger.info(f"Deleted PDF file for book {book_id}: {pdf_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete PDF file {pdf_path}: {e!s}")
            return False

    def extract_text_between_pages(
        self, book_id: int, user_id: int, start_page: int, end_page: int
    ) -> str:
        """
        Extract text from a PDF between two page numbers.

        Args:
            book_id: The book ID
            user_id: The user ID
            start_page: Starting page number (inclusive)
            end_page: Ending page number (inclusive)

        Returns:
            The extracted text

        Raises:
            NotImplementedError: PDF text extraction not yet implemented
        """
        logger.warning("PDF text extraction is not yet implemented")
        raise NotImplementedError("PDF text extraction is coming soon")
