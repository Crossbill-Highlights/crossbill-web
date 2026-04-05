"""S3-compatible repository for file I/O operations."""

import asyncio
import fnmatch
import logging
import re
from typing import Any

from src.domain.common.value_objects.ids import BookId

logger = logging.getLogger(__name__)


def _sanitize_title(text: str) -> str:
    """
    Sanitize text for use in an S3 object key.

    Removes/replaces characters that are invalid in filenames.
    Limits length to prevent overly long keys.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for use in keys/filenames
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', "", text)
    sanitized = re.sub(r"\s+", "_", sanitized)
    sanitized = sanitized.strip("_.")
    max_length = 100
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


class S3FileRepository:
    """Repository for managing book files (EPUB, PDF, covers) in S3-compatible storage."""

    def __init__(self, s3_client: Any, bucket_name: str) -> None:  # noqa: ANN401
        self._client = s3_client
        self._bucket = bucket_name

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_keys(self, prefix: str, pattern: str) -> list[str]:
        """List object keys under *prefix* whose basename matches *pattern*."""
        response = self._client.list_objects_v2(Bucket=self._bucket, Prefix=prefix)
        contents = response.get("Contents", [])
        return [
            obj["Key"]
            for obj in contents
            if fnmatch.fnmatch(obj["Key"].split("/")[-1], pattern)
        ]

    async def _async_find_keys(self, prefix: str, pattern: str) -> list[str]:
        return await asyncio.to_thread(self._find_keys, prefix, pattern)

    async def _delete_by_pattern(self, prefix: str, pattern: str) -> bool:
        """Delete the first key matching *pattern* under *prefix*."""
        keys = await self._async_find_keys(prefix, pattern)
        if not keys:
            return False
        key = keys[0]
        try:
            await asyncio.to_thread(
                self._client.delete_object, Bucket=self._bucket, Key=key
            )
            logger.info(f"Deleted S3 object: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete S3 object {key}: {e!s}")
            return False

    async def _get_by_pattern(self, prefix: str, pattern: str) -> bytes | None:
        """Return the bytes of the first key matching *pattern* under *prefix*."""
        keys = await self._async_find_keys(prefix, pattern)
        if not keys:
            return None
        key = keys[0]

        def _read() -> bytes:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()  # type: ignore[no-any-return]

        return await asyncio.to_thread(_read)

    # ------------------------------------------------------------------
    # Public interface (FileRepositoryProtocol)
    # ------------------------------------------------------------------

    async def save_epub(self, book_id: BookId, content: bytes, title: str) -> str:
        """
        Upload an EPUB file to S3.

        Deletes any existing EPUB for this book before uploading.

        Args:
            book_id: ID of the book
            content: File content as bytes
            title: Title of the book

        Returns:
            Filename (basename) of the uploaded object
        """
        await self.delete_epub(book_id)

        sanitized_title = _sanitize_title(title)
        filename = f"{sanitized_title}_{book_id.value}.epub"
        key = f"epubs/{filename}"
        await asyncio.to_thread(
            self._client.put_object, Bucket=self._bucket, Key=key, Body=content
        )
        logger.info(f"Uploaded EPUB to S3: {key}")
        return filename

    async def save_pdf(self, book_id: BookId, content: bytes, title: str) -> str:
        """
        Upload a PDF file to S3.

        Args:
            book_id: ID of the book
            content: File content as bytes
            title: Title of the book

        Returns:
            Filename (basename) of the uploaded object
        """
        sanitized_title = _sanitize_title(title)
        filename = f"{sanitized_title}_{book_id.value}.pdf"
        key = f"pdfs/{filename}"
        await asyncio.to_thread(
            self._client.put_object, Bucket=self._bucket, Key=key, Body=content
        )
        logger.info(f"Uploaded PDF to S3: {key}")
        return filename

    async def save_cover(self, book_id: BookId, content: bytes) -> str:
        """
        Upload a cover image to S3.

        Args:
            book_id: ID of the book
            content: File content as bytes

        Returns:
            Filename (basename) of the uploaded object
        """
        filename = f"{book_id.value}.jpg"
        key = f"book-covers/{filename}"
        await asyncio.to_thread(
            self._client.put_object, Bucket=self._bucket, Key=key, Body=content
        )
        logger.info(f"Uploaded cover to S3: {key}")
        return filename

    async def delete_epub(self, book_id: BookId) -> bool:
        """
        Delete the EPUB file for a book from S3.

        Args:
            book_id: ID of the book

        Returns:
            True if deleted, False if not found or error
        """
        return await self._delete_by_pattern("epubs/", f"*_{book_id.value}.epub")

    async def delete_pdf(self, book_id: BookId) -> bool:
        """
        Delete the PDF file for a book from S3.

        Args:
            book_id: ID of the book

        Returns:
            True if deleted, False if not found or error
        """
        return await self._delete_by_pattern("pdfs/", f"*_{book_id.value}.pdf")

    async def delete_cover(self, book_id: BookId) -> bool:
        """
        Delete the cover image for a book from S3.

        Args:
            book_id: ID of the book

        Returns:
            True if deleted, False if not found or error
        """
        return await self._delete_by_pattern("book-covers/", f"{book_id.value}.*")

    async def get_epub(self, book_id: BookId) -> bytes | None:
        """
        Retrieve EPUB file content from S3.

        Args:
            book_id: ID of the book

        Returns:
            EPUB bytes or None if not found
        """
        return await self._get_by_pattern("epubs/", f"*_{book_id.value}.epub")

    async def get_pdf(self, book_id: BookId) -> bytes | None:
        """
        Retrieve PDF file content from S3.

        Args:
            book_id: ID of the book

        Returns:
            PDF bytes or None if not found
        """
        return await self._get_by_pattern("pdfs/", f"*_{book_id.value}.pdf")

    async def get_cover(self, book_id: BookId) -> bytes | None:
        """
        Retrieve cover image content from S3.

        Args:
            book_id: ID of the book

        Returns:
            Cover image bytes or None if not found
        """
        return await self._get_by_pattern("book-covers/", f"{book_id.value}.*")

    async def has_cover(self, book_id: BookId) -> bool:
        """Check if a cover image exists for a book in S3."""
        keys = await self._async_find_keys("book-covers/", f"{book_id.value}.*")
        return len(keys) > 0
