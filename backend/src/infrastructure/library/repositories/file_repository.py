"""Repository for file I/O operations."""

import asyncio
import logging
import re

from src.config import BOOK_COVERS_DIR, EPUBS_DIR, PDFS_DIR  # type: ignore[attr-defined]
from src.domain.common.value_objects.ids import BookId

logger = logging.getLogger(__name__)


def _validate_filename(filename: str) -> None:
    """Validate that a filename does not contain path traversal sequences."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError(f"Invalid filename: {filename}")


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

    async def delete_epub(self, filename: str) -> bool:
        """
        Delete an EPUB file by filename.

        Args:
            filename: Name of the file to delete

        Returns:
            True if file was deleted, False if not found
        """
        _validate_filename(filename)
        file_path = EPUBS_DIR / filename
        if not await asyncio.to_thread(file_path.exists):
            logger.info(f"No EPUB file found: {file_path}")
            return False

        try:
            await asyncio.to_thread(file_path.unlink)
            logger.info(f"Deleted EPUB file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete EPUB file {file_path}: {e!s}")
            return False

    async def delete_pdf(self, filename: str) -> bool:
        """
        Delete a PDF file by filename.

        Args:
            filename: Name of the file to delete

        Returns:
            True if file was deleted, False if not found
        """
        _validate_filename(filename)
        file_path = PDFS_DIR / filename
        if not await asyncio.to_thread(file_path.exists):
            logger.info(f"No PDF file found: {file_path}")
            return False

        try:
            await asyncio.to_thread(file_path.unlink)
            logger.info(f"Deleted PDF file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete PDF file {file_path}: {e!s}")
            return False

    async def delete_cover(self, filename: str) -> bool:
        """
        Delete a cover image by filename.

        Args:
            filename: Name of the file to delete

        Returns:
            True if file was deleted, False if not found
        """
        _validate_filename(filename)
        file_path = BOOK_COVERS_DIR / filename
        if not await asyncio.to_thread(file_path.exists):
            logger.info(f"No cover file found: {file_path}")
            return False

        try:
            await asyncio.to_thread(file_path.unlink)
            logger.info(f"Deleted cover file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cover file {file_path}: {e!s}")
            return False

    async def get_epub(self, filename: str) -> bytes | None:
        """
        Get EPUB file content by filename.

        Args:
            filename: Name of the file to read

        Returns:
            EPUB file content as bytes, or None if not found
        """
        _validate_filename(filename)
        file_path = EPUBS_DIR / filename
        if not await asyncio.to_thread(file_path.exists):
            return None
        return await asyncio.to_thread(file_path.read_bytes)

    async def get_pdf(self, filename: str) -> bytes | None:
        """
        Get PDF file content by filename.

        Args:
            filename: Name of the file to read

        Returns:
            PDF file content as bytes, or None if not found
        """
        _validate_filename(filename)
        file_path = PDFS_DIR / filename
        if not await asyncio.to_thread(file_path.exists):
            return None
        return await asyncio.to_thread(file_path.read_bytes)

    async def get_cover(self, filename: str) -> bytes | None:
        """
        Get cover image content by filename.

        Args:
            filename: Name of the file to read

        Returns:
            Cover image content as bytes, or None if not found
        """
        _validate_filename(filename)
        file_path = BOOK_COVERS_DIR / filename
        if not await asyncio.to_thread(file_path.exists):
            return None
        return await asyncio.to_thread(file_path.read_bytes)

