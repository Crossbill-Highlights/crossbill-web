"""Use case for querying reading sessions with highlights and content."""

from dataclasses import dataclass

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.application.reading.protocols.ebook_text_extraction_service import (
    EbookTextExtractionServiceProtocol,
)
from src.application.reading.protocols.highlight_repository import (
    HighlightRepositoryProtocol,
)
from src.application.reading.protocols.reading_session_repository import (
    ReadingSessionRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.reading_session import ReadingSession
from src.exceptions import BookNotFoundError

logger = structlog.get_logger(__name__)


@dataclass
class ReadingSessionWithHighlights:
    """DTO aggregating session with highlights and content."""

    session: ReadingSession
    highlights: list[Highlight]
    extracted_content: str | None = None


@dataclass
class ReadingSessionQueryResult:
    """Paginated result."""

    sessions_with_highlights: list[ReadingSessionWithHighlights]
    total: int
    offset: int
    limit: int


class ReadingSessionQueryUseCase:
    """Use case for querying reading sessions."""

    def __init__(
        self,
        session_repository: ReadingSessionRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        text_extraction_service: EbookTextExtractionServiceProtocol,
        file_repo: FileRepositoryProtocol,
    ) -> None:
        self.session_repository = session_repository
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository
        self.text_extraction_service = text_extraction_service
        self.file_repo = file_repo

    def get_sessions_for_book(
        self,
        book_id: int,
        user_id: int,
        limit: int,
        offset: int,
        include_content: bool = True,
    ) -> ReadingSessionQueryResult:
        """
        Get reading sessions for a specific book with highlights and optional content.

        This is a read-only operation (no commit needed).

        Args:
            book_id: Book ID
            user_id: User ID
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            include_content: Whether to extract content via EbookService

        Returns:
            ReadingSessionQueryResult with sessions, highlights, and optional content
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Validate book exists and belongs to user
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Resolve epub path once for the book
        epub_path = None
        if include_content and book.file_path and book.file_type == "epub":
            epub_path = self.file_repo.find_epub(book.id)

        sessions = self.session_repository.find_by_book_id(book_id_vo, user_id_vo, limit, offset)
        total = self.session_repository.count_by_book_id(book_id_vo, user_id_vo)

        session_ids = [s.id for s in sessions]
        highlights_by_session = self.highlight_repository.get_highlights_by_session_ids(
            session_ids, user_id_vo
        )

        sessions_with_highlights = []
        for session in sessions:
            highlights = highlights_by_session.get(session.id, [])

            # Optionally extract content
            extracted_content = None
            if include_content and session.start_xpoint and epub_path and epub_path.exists():
                try:
                    extracted_content = self.text_extraction_service.extract_text(
                        epub_path=epub_path,
                        start_xpoint=session.start_xpoint.start.to_string(),
                        end_xpoint=session.start_xpoint.end.to_string(),
                    )
                except Exception as e:
                    logger.warning(
                        "failed_to_extract_content",
                        session_id=session.id.value,
                        error=str(e),
                    )

            sessions_with_highlights.append(
                ReadingSessionWithHighlights(
                    session=session,
                    highlights=highlights,
                    extracted_content=extracted_content,
                )
            )

        return ReadingSessionQueryResult(
            sessions_with_highlights=sessions_with_highlights,
            total=total,
            offset=offset,
            limit=limit,
        )
