"""Service for querying reading sessions with highlights and content."""

from dataclasses import dataclass

import structlog
from sqlalchemy.orm import Session

from src.application.library.services.ebook_text_extraction_service import (
    EbookTextExtractionService,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.reading_session import ReadingSession
from src.exceptions import BookNotFoundError
from src.infrastructure.library.repositories.book_repository import BookRepository
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository
from src.infrastructure.reading.repositories.reading_session_repository import (
    ReadingSessionRepository,
)

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


class ReadingSessionQueryService:
    """Service for querying reading sessions."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = BookRepository(db)
        self.session_repo = ReadingSessionRepository(db)
        self.highlight_repo = HighlightRepository(db)
        self.text_extraction_service = EbookTextExtractionService(db)

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
        book = self.book_repo.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Fetch sessions via repository (paginated)
        sessions = self.session_repo.find_by_book_id(book_id_vo, user_id_vo, limit, offset)
        total = self.session_repo.count_by_book_id(book_id_vo, user_id_vo)

        # Fetch highlights for all sessions in one query
        session_ids = [s.id for s in sessions]
        highlights_by_session = self.highlight_repo.get_highlights_by_session_ids(
            session_ids, user_id_vo
        )

        # Build DTOs
        sessions_with_highlights = []
        for session in sessions:
            highlights = highlights_by_session.get(session.id, [])

            # Optionally extract content
            extracted_content = None
            if include_content and session.start_xpoint:
                try:
                    extracted_content = self.text_extraction_service.extract_text(
                        book_id,
                        user_id,
                        session.start_xpoint.start.to_string(),
                        session.start_xpoint.end.to_string(),
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
