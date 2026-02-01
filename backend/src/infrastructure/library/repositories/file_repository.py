"""Repository for file I/O operations."""

import logging
from pathlib import Path

from src.config import BOOK_COVERS_DIR, EPUBS_DIR, PDFS_DIR  # type: ignore[attr-defined]
from src.domain.common.value_objects.ids import BookId

logger = logging.getLogger(__name__)


class FileRepository:
    """Repository for managing book files (EPUB, PDF, covers)."""

    def save_epub(self, book_id: BookId, content: bytes, filename: str) -> Path:
        """
        Save an EPUB file to disk.

        Args:
            book_id: ID of the book
            content: File content as bytes
            filename: Name for the file (should include book_id)

        Returns:
            Path to the saved file
        """
        EPUBS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = EPUBS_DIR / filename
        file_path.write_bytes(content)
        logger.info(f"Saved EPUB file: {file_path}")
        return file_path

    def save_pdf(self, book_id: BookId, content: bytes, filename: str) -> Path:
        """
        Save a PDF file to disk.

        Args:
            book_id: ID of the book
            content: File content as bytes
            filename: Name for the file (should include book_id)

        Returns:
            Path to the saved file
        """
        PDFS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = PDFS_DIR / filename
        file_path.write_bytes(content)
        logger.info(f"Saved PDF file: {file_path}")
        return file_path

    def save_cover(self, book_id: BookId, content: bytes, filename: str) -> Path:
        """
        Save a cover image to disk.

        Args:
            book_id: ID of the book
            content: File content as bytes
            filename: Name for the file (should include book_id)

        Returns:
            Path to the saved file
        """
        BOOK_COVERS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = BOOK_COVERS_DIR / filename
        file_path.write_bytes(content)
        logger.info(f"Saved cover file: {file_path}")
        return file_path

    def delete_epub(self, book_id: BookId) -> bool:
        """
        Delete EPUB file for a book.

        Uses glob pattern to find the file by book_id suffix.

        Args:
            book_id: ID of the book

        Returns:
            True if file was deleted, False if not found
        """
        epub_files = list(EPUBS_DIR.glob(f"*_{book_id.value}.epub"))

        if not epub_files:
            logger.info(f"No EPUB file found for book {book_id}")
            return False

        epub_path = epub_files[0]

        try:
            epub_path.unlink()
            logger.info(f"Deleted EPUB file: {epub_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete EPUB file {epub_path}: {e!s}")
            return False

    def delete_pdf(self, book_id: BookId) -> bool:
        """
        Delete PDF file for a book.

        Uses glob pattern to find the file by book_id suffix.

        Args:
            book_id: ID of the book

        Returns:
            True if file was deleted, False if not found
        """
        pdf_files = list(PDFS_DIR.glob(f"*_{book_id.value}.pdf"))

        if not pdf_files:
            logger.info(f"No PDF file found for book {book_id}")
            return False

        pdf_path = pdf_files[0]

        try:
            pdf_path.unlink()
            logger.info(f"Deleted PDF file: {pdf_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete PDF file {pdf_path}: {e!s}")
            return False

    def delete_cover(self, book_id: BookId) -> bool:
        """
        Delete cover image for a book.

        Uses glob pattern to find the file by book_id suffix.

        Args:
            book_id: ID of the book

        Returns:
            True if file was deleted, False if not found
        """
        cover_files = list(BOOK_COVERS_DIR.glob(f"*_{book_id.value}.*"))

        if not cover_files:
            logger.info(f"No cover file found for book {book_id}")
            return False

        cover_path = cover_files[0]

        try:
            cover_path.unlink()
            logger.info(f"Deleted cover file: {cover_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cover file {cover_path}: {e!s}")
            return False

    def find_epub(self, book_id: BookId) -> Path | None:
        """
        Find EPUB file path for a book.

        Args:
            book_id: ID of the book

        Returns:
            Path to the EPUB file, or None if not found
        """
        epub_files = list(EPUBS_DIR.glob(f"*_{book_id.value}.epub"))

        if not epub_files:
            return None

        return epub_files[0]

    def find_pdf(self, book_id: BookId) -> Path | None:
        """
        Find PDF file path for a book.

        Args:
            book_id: ID of the book

        Returns:
            Path to the PDF file, or None if not found
        """
        pdf_files = list(PDFS_DIR.glob(f"*_{book_id.value}.pdf"))

        if not pdf_files:
            return None

        return pdf_files[0]

    def find_cover(self, book_id: BookId) -> Path | None:
        """
        Find cover file path for a book.

        Args:
            book_id: ID of the book

        Returns:
            Path to the cover file, or None if not found
        """
        # Look for cover with book_id in filename (supports multiple formats)
        cover_files = list(BOOK_COVERS_DIR.glob(f"{book_id.value}.*"))

        if not cover_files:
            return None

        return cover_files[0]
