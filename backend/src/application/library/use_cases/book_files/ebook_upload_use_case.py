"""Use case for ebook upload operations."""

import logging
import re

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.library.protocols.epub_toc_parser import EpubTocParserProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.application.library.protocols.position_index_service import PositionIndexServiceProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.reading_session_repository import (
    ReadingSessionRepositoryProtocol,
)
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.common.value_objects.position_index import PositionIndex
from src.domain.library.entities.chapter import TocChapter
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


class EbookUploadUseCase:
    """Use case for uploading ebook files."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        file_repository: FileRepositoryProtocol,
        epub_toc_parser: EpubTocParserProtocol,
        position_index_service: PositionIndexServiceProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        session_repository: ReadingSessionRepositoryProtocol,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            book_repository: Book repository protocol implementation
            chapter_repository: Chapter repository protocol implementation
            file_repository: File repository protocol implementation
            epub_toc_parser: EPUB TOC parser service
            position_index_service: Service for building position indices from EPUBs
            highlight_repository: Repository for highlight persistence
            session_repository: Repository for reading session persistence
        """
        self.book_repository = book_repository
        self.chapter_repository = chapter_repository
        self.file_repository = file_repository
        self.epub_toc_parser = epub_toc_parser
        self.position_index_service = position_index_service
        self.highlight_repository = highlight_repository
        self.session_repository = session_repository

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

        if not self.epub_toc_parser.validate_epub(content):
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
        self.book_repository.save(book)

        # Build position index from EPUB DOM
        position_index = self.position_index_service.build_position_index(epub_path)

        # Parse TOC and sync chapters (with positions)
        toc_chapters = self.epub_toc_parser.parse_toc(epub_path)
        if toc_chapters:
            enriched_chapters = []
            for tc in toc_chapters:
                start_pos = position_index.resolve(tc.start_xpoint) if tc.start_xpoint else None
                end_pos = position_index.resolve(tc.end_xpoint) if tc.end_xpoint else None
                enriched_chapters.append(
                    TocChapter(
                        name=tc.name,
                        chapter_number=tc.chapter_number,
                        parent_name=tc.parent_name,
                        start_xpoint=tc.start_xpoint,
                        end_xpoint=tc.end_xpoint,
                        start_position=start_pos,
                        end_position=end_pos,
                    )
                )
            self.chapter_repository.sync_chapters_from_toc(book.id, user_id, enriched_chapters)

        # Backfill positions for existing entities
        self._backfill_positions(book.id, user_id, position_index)

        return epub_filename, str(epub_path)

    def _backfill_positions(
        self,
        book_id: BookId,
        user_id: UserId,
        position_index: PositionIndex,
    ) -> None:
        """Backfill position data for existing highlights and reading sessions."""
        # Backfill highlights
        highlights = self.highlight_repository.find_by_book_id(book_id, user_id)
        highlight_updates = []
        for h in highlights:
            if h.xpoints and h.xpoints.start:
                pos = position_index.resolve(h.xpoints.start.to_string())
                if pos:
                    highlight_updates.append((h.id, pos))
        if highlight_updates:
            self.highlight_repository.bulk_update_positions(highlight_updates)

        # Backfill reading sessions
        sessions = self.session_repository.find_by_book_id(book_id, user_id, limit=10000, offset=0)
        session_updates = []
        for s in sessions:
            if s.start_xpoint:
                start_pos = position_index.resolve(s.start_xpoint.start.to_string())
                end_pos = position_index.resolve(s.start_xpoint.end.to_string())
                if start_pos and end_pos:
                    session_updates.append((s.id, start_pos, end_pos))
        if session_updates:
            self.session_repository.bulk_update_positions(session_updates)
