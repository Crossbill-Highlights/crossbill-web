"""Use case for ebook upload operations."""

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from ebooklib import epub

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.reading.exceptions import BookNotFoundError
from src.exceptions import InvalidEbookError

logger = logging.getLogger(__name__)


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


# TODO: should this and helper functions here be a domain service?
def _extract_toc_hierarchy(
    toc_items: list[Any], current_number: int = 1, parent_name: str | None = None
) -> list[tuple[str, int, str | None]]:
    """
    Extract hierarchical TOC structure into a list preserving parent relationships.

    EPUB TOC can be nested. This function preserves the hierarchy while
    assigning sequential chapter numbers for reading order.

    Args:
        toc_items: List of TOC items from ebooklib (can be Link objects or tuples)
        current_number: Starting chapter number (used for recursion)
        parent_name: Name of the parent chapter (None for root-level chapters)

    Returns:
        List of (chapter_title, chapter_number, parent_name) tuples in reading order.
        parent_name is None for root-level chapters.
    """
    chapters = []

    for item in toc_items:
        # TOC items can be Link objects or tuples (Section, [children])
        if isinstance(item, tuple):
            # Nested section: (Link, [children])
            section, children = item[0], item[1] if len(item) > 1 else []

            # Add the section itself
            if hasattr(section, "title"):
                chapters.append((section.title, current_number, parent_name))
                section_name = section.title
                current_number += 1
            else:
                section_name = parent_name

            # Recursively process children with this section as parent
            child_chapters = _extract_toc_hierarchy(children, current_number, section_name)
            chapters.extend(child_chapters)
            current_number += len(child_chapters)

        elif hasattr(item, "title"):
            # Simple Link object
            chapters.append((item.title, current_number, parent_name))
            current_number += 1

    return chapters


class EbookUploadUseCase:
    """Use case for uploading ebook files."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        file_repository: FileRepositoryProtocol,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            book_repository: Book repository protocol implementation
            chapter_repository: Chapter repository protocol implementation
            file_repository: File repository protocol implementation
        """
        self.book_repository = book_repository
        self.chapter_repository = chapter_repository
        self.file_repository = file_repository

    def upload_ebook(
        self,
        client_book_id: str,
        content: bytes,
        content_type: str,
        user_id: int,
    ) -> tuple[str, str]:
        """
        Upload and save an ebook file (EPUB or PDF).

        Args:
            client_book_id: Client-provided book identifier
            content: File content as bytes
            content_type: MIME type of the file
            user_id: ID of the user uploading the file

        Returns:
            tuple[str, str]: (file_path_for_db, absolute_file_path)

        Raises:
            EntityNotFoundError: If book not found for the given client_book_id
            InvalidEbookError: If file validation fails
            NotImplementedError: If PDF upload is requested (not yet implemented)
        """
        # Route by content type
        if content_type in ["application/epub+zip", "application/epub"]:
            return self._upload_epub(client_book_id, content, UserId(user_id))
        if content_type == "application/pdf":
            raise NotImplementedError("PDF upload not yet implemented")
        raise InvalidEbookError(f"Unsupported content type: {content_type}", ebook_type="UNKNOWN")

    def _upload_epub(
        self,
        client_book_id: str,
        content: bytes,
        user_id: UserId,
    ) -> tuple[str, str]:
        """
        Upload and validate an EPUB file for a book.

        This method:
        1. Validates the book exists and belongs to user
        2. Validates epub structure using ebooklib
        3. Generates sanitized filename from book title and ID
        4. Saves file to epubs directory
        5. Removes old epub file if filename differs
        6. Updates book.file_path and book.file_type in database
        7. Parses TOC and saves chapters

        Args:
            client_book_id: Client-provided book identifier
            content: The epub file content as bytes
            user_id: ID of the user uploading the epub

        Returns:
            tuple[str, str]: (epub_path_for_db, absolute_file_path)

        Raises:
            EntityNotFoundError: If book not found or doesn't belong to user
            InvalidEbookError: If epub structure validation fails
        """
        # Find book by client_book_id
        book = self.book_repository.find_by_client_book_id(client_book_id, user_id)
        if not book:
            raise BookNotFoundError(f"client_book_id={client_book_id}")

        if not _validate_epub(content):
            raise InvalidEbookError("EPUB structure validation failed", ebook_type="EPUB")

        # TODO: These likely belong to the repository level
        # Generate filename: sanitized_title_bookid.epub
        sanitized_title = _sanitize_filename(book.title)
        epub_filename = f"{sanitized_title}_{book.id.value}.epub"

        # Check if book already has an epub file for deletion
        old_file_path = None
        if book.file_path and book.file_type == "epub":
            old_file_path = book.file_path

        # Delete old epub file if it exists and has different name
        if old_file_path and old_file_path != epub_filename:
            self.file_repository.delete_epub(book.id)

        # Save new epub file
        epub_path = self.file_repository.save_epub(book.id, content, epub_filename)
        book.update_file(epub_filename, "epub")

        # Parse TOC and save chapters to database
        # TODO: this parsing logic might belong to domain level
        toc_chapters = self._parse_toc_from_epub(epub_path)
        if toc_chapters:
            # TODO: maybe we could pass domain objects to the repository?
            self.chapter_repository.sync_chapters_from_toc(book.id, user_id, toc_chapters)

        return epub_filename, str(epub_path)

    def _parse_toc_from_epub(self, epub_path: Path) -> list[tuple[str, int, str | None]]:
        """
        Parse table of contents from an EPUB file.

        Extracts chapter titles, reading order, and hierarchy from the EPUB's TOC.
        Handles both NCX (EPUB 2) and Navigation Document (EPUB 3) formats.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            List of (chapter_title, chapter_number, parent_name) tuples in reading order.
            parent_name is None for root-level chapters.
            Returns empty list if EPUB has no TOC or TOC is invalid.
        """
        try:
            book = epub.read_epub(str(epub_path))

            # Get TOC from epub (supports both NCX and nav.xhtml)
            toc = book.toc

            if not toc:
                logger.info(f"EPUB at {epub_path} has no table of contents")
                return []

            # Extract hierarchical TOC structure
            chapters = _extract_toc_hierarchy(toc)

            logger.info(f"Parsed {len(chapters)} chapters from EPUB TOC at {epub_path}")
            return chapters

        except Exception as e:
            logger.error(f"Failed to parse TOC from EPUB at {epub_path}: {e!s}")
            return []
