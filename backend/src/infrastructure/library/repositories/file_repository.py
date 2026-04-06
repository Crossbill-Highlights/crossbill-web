"""Repository for file I/O operations."""

import asyncio
import logging
import re

from src.config import BOOK_COVERS_DIR, EPUBS_DIR, PDFS_DIR  # type: ignore[attr-defined]
from src.domain.common.value_objects.ids import BookId

logger = logging.getLogger(__name__)


def _sanitize_title(text: str) -> str:
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


class FileRepository:
    """Repository for managing book files (EPUB, PDF, covers)."""

    async def save_epub(self, book_id: BookId, content: bytes, title: str) -> str:
        """
        Save an EPUB file to disk.

        Args:
            book_id: ID of the book
            content: File content as bytes
            title: Title of the book

        Returns:
            Filename of the saved file
        """
        await asyncio.to_thread(lambda: EPUBS_DIR.mkdir(parents=True, exist_ok=True))

        # Delete possible existing epub file before saving the new one
        await self.delete_epub(book_id)

        sanitized_title = _sanitize_title(title)
        file_path = EPUBS_DIR / f"{sanitized_title}_{book_id.value}.epub"
        await asyncio.to_thread(file_path.write_bytes, content)
        logger.info(f"Saved EPUB file: {file_path}")
        return file_path.name

    async def save_pdf(self, book_id: BookId, content: bytes, title: str) -> str:
        """
        Save a PDF file to disk.

        Args:
            book_id: ID of the book
            content: File content as bytes
            title: Title of the book

        Returns:
            Filename of the saved file
        """
        await asyncio.to_thread(lambda: PDFS_DIR.mkdir(parents=True, exist_ok=True))
        sanitized_title = _sanitize_title(title)
        file_path = PDFS_DIR / f"{sanitized_title}_{book_id.value}.pdf"
        await asyncio.to_thread(file_path.write_bytes, content)
        logger.info(f"Saved PDF file: {file_path}")
        return file_path.name

    async def save_cover(self, book_id: BookId, content: bytes) -> str:
        """
        Save a cover image to disk.

        Args:
            book_id: ID of the book
            content: File content as bytes

        Returns:
            Filename of the saved file
        """
        await asyncio.to_thread(lambda: BOOK_COVERS_DIR.mkdir(parents=True, exist_ok=True))
        filename = f"{book_id.value}.jpg"
        file_path = BOOK_COVERS_DIR / filename
        await asyncio.to_thread(file_path.write_bytes, content)
        logger.info(f"Saved cover file: {file_path}")
        return file_path.name

    async def delete_epub(self, book_id: BookId) -> bool:
        """
        Delete EPUB file for a book.

        Uses glob pattern to find the file by book_id suffix.

        Args:
            book_id: ID of the book

        Returns:
            True if file was deleted, False if not found
        """
        epub_files = await asyncio.to_thread(
            lambda: list(EPUBS_DIR.glob(f"*_{book_id.value}.epub"))
        )

        if not epub_files:
            logger.info(f"No EPUB file found for book {book_id}")
            return False

        epub_path = epub_files[0]

        try:
            await asyncio.to_thread(epub_path.unlink)
            logger.info(f"Deleted EPUB file: {epub_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete EPUB file {epub_path}: {e!s}")
            return False

    async def delete_pdf(self, book_id: BookId) -> bool:
        """
        Delete PDF file for a book.

        Uses glob pattern to find the file by book_id suffix.

        Args:
            book_id: ID of the book

        Returns:
            True if file was deleted, False if not found
        """
        pdf_files = await asyncio.to_thread(lambda: list(PDFS_DIR.glob(f"*_{book_id.value}.pdf")))

        if not pdf_files:
            logger.info(f"No PDF file found for book {book_id}")
            return False

        pdf_path = pdf_files[0]

        try:
            await asyncio.to_thread(pdf_path.unlink)
            logger.info(f"Deleted PDF file: {pdf_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete PDF file {pdf_path}: {e!s}")
            return False

    async def delete_cover(self, book_id: BookId) -> bool:
        """
        Delete cover image for a book.

        Uses glob pattern to find the file by book_id suffix.

        Args:
            book_id: ID of the book

        Returns:
            True if file was deleted, False if not found
        """
        cover_files = await asyncio.to_thread(
            lambda: list(BOOK_COVERS_DIR.glob(f"{book_id.value}.*"))
        )

        if not cover_files:
            logger.info(f"No cover file found for book {book_id}")
            return False

        cover_path = cover_files[0]

        try:
            await asyncio.to_thread(cover_path.unlink)
            logger.info(f"Deleted cover file: {cover_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cover file {cover_path}: {e!s}")
            return False

    async def get_epub(self, book_id: BookId) -> bytes | None:
        """
        Get EPUB file content for a book.

        Args:
            book_id: ID of the book

        Returns:
            EPUB file content as bytes, or None if not found
        """
        epub_files = await asyncio.to_thread(
            lambda: list(EPUBS_DIR.glob(f"*_{book_id.value}.epub"))
        )

        if not epub_files:
            return None

        return await asyncio.to_thread(epub_files[0].read_bytes)

    async def get_pdf(self, book_id: BookId) -> bytes | None:
        """
        Get PDF file content for a book.

        Args:
            book_id: ID of the book

        Returns:
            PDF file content as bytes, or None if not found
        """
        pdf_files = await asyncio.to_thread(lambda: list(PDFS_DIR.glob(f"*_{book_id.value}.pdf")))

        if not pdf_files:
            return None

        return await asyncio.to_thread(pdf_files[0].read_bytes)

    async def get_cover(self, book_id: BookId) -> bytes | None:
        """
        Get cover image content for a book.

        Args:
            book_id: ID of the book

        Returns:
            Cover image content as bytes, or None if not found
        """
        cover_files = await asyncio.to_thread(
            lambda: list(BOOK_COVERS_DIR.glob(f"{book_id.value}.*"))
        )

        if not cover_files:
            return None

        return await asyncio.to_thread(cover_files[0].read_bytes)

    async def has_cover(self, book_id: BookId) -> bool:
        """Check if a cover image exists for a book."""
        cover_files = await asyncio.to_thread(
            lambda: list(BOOK_COVERS_DIR.glob(f"{book_id.value}.*"))
        )
        return len(cover_files) > 0
