"""Service for uploading reading sessions with deduplication and highlight linking."""

from dataclasses import dataclass
from datetime import datetime

import structlog
from sqlalchemy.orm import Session

from src.config import get_settings
from src.domain.common.value_objects import (
    BookId,
    ContentHash,
    ReadingSessionId,
    UserId,
    XPointRange,
)
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.reading_session import ReadingSession
from src.exceptions import BookNotFoundError
from src.hash_utils import compute_reading_session_hash_v2
from src.infrastructure.library.repositories.book_repository import BookRepository
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository
from src.infrastructure.reading.repositories.reading_session_repository import (
    ReadingSessionRepository,
)
from src.services.ebook.epub.xpoint_utils import is_xpoint_in_range

logger = structlog.get_logger(__name__)


@dataclass
class ReadingSessionUploadData:
    """DTO for session upload from API."""

    start_time: datetime
    end_time: datetime
    start_xpoint: str | None = None
    end_xpoint: str | None = None
    start_page: int | None = None
    end_page: int | None = None
    device_id: str | None = None


@dataclass
class ReadingSessionUploadResult:
    """Result of upload operation."""

    book_id: BookId
    created_count: int
    skipped_duplicate_count: int
    linked_highlights_count: int


class ReadingSessionUploadService:
    """Service for uploading and processing reading sessions."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = BookRepository(db)
        self.session_repo = ReadingSessionRepository(db)
        self.highlight_repo = HighlightRepository(db)

    def upload_reading_sessions(
        self,
        client_book_id: str,
        sessions: list[ReadingSessionUploadData],
        user_id: int,
    ) -> ReadingSessionUploadResult:
        """
        Process reading session upload from KOReader for a single book.

        This method:
        1. Looks up the book by client_book_id
        2. Filters sessions (same start/end points, minimum duration)
        3. Computes NEW hash: hash(book_id + user_id + start_time + device_id)
        4. Creates ReadingSession entities using factory method
        5. Bulk creates via repository
        6. Links highlights to created sessions
        7. Commits transaction

        Args:
            client_book_id: Client-provided book identifier
            sessions: List of validated reading sessions for this book
            user_id: ID of the user

        Returns:
            ReadingSessionUploadResult with upload statistics
        """
        logger.info(
            "processing_reading_session_upload",
            session_count=len(sessions),
            client_book_id=client_book_id,
        )

        # Get book by client_book_id
        user_id_vo = UserId(user_id)
        book = self.book_repo.find_by_client_book_id(client_book_id, user_id_vo)

        if not book:
            logger.error(
                "book_not_found_for_reading_session_upload",
                client_book_id=client_book_id,
            )
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found. "
                "Please create the book first"
            )

        # Filter sessions where start and end points are the same
        initial_count = len(sessions)
        sessions = [
            s for s in sessions if s.start_xpoint != s.end_xpoint or s.start_page != s.end_page
        ]
        filtered_same_points = initial_count - len(sessions)
        if filtered_same_points > 0:
            logger.debug(
                "filtered_sessions_with_same_start_end",
                filtered_count=filtered_same_points,
            )

        # Filter out sessions shorter than minimum duration
        settings = get_settings()
        min_duration = settings.MINIMUM_READING_SESSION_DURATION
        before_duration_filter = len(sessions)
        sessions = [
            s for s in sessions if (s.end_time - s.start_time).total_seconds() >= min_duration
        ]
        filtered_too_short = before_duration_filter - len(sessions)
        if filtered_too_short > 0:
            logger.debug(
                "filtered_sessions_below_minimum_duration",
                filtered_count=filtered_too_short,
                min_duration_seconds=min_duration,
            )

        # Create domain entities with NEW hash
        domain_sessions: list[ReadingSession] = []
        for session in sessions:
            # Compute new hash using IDs
            session_hash = compute_reading_session_hash_v2(
                book_id=book.id.value,
                user_id=user_id,
                start_time=session.start_time.isoformat(),
                device_id=session.device_id,
            )

            # Parse XPointRange if both xpoints exist
            xpoint_range = None
            if session.start_xpoint and session.end_xpoint:
                xpoint_range = XPointRange.parse(session.start_xpoint, session.end_xpoint)

            # Create domain entity with our custom hash
            # Use constructor directly to provide our own content_hash
            domain_session = ReadingSession(
                id=ReadingSessionId.generate(),
                user_id=user_id_vo,
                book_id=book.id,
                start_time=session.start_time,
                end_time=session.end_time,
                content_hash=ContentHash(session_hash),
                start_xpoint=xpoint_range,
                start_page=session.start_page,
                end_page=session.end_page,
                device_id=session.device_id,
                ai_summary=None,
            )
            domain_sessions.append(domain_session)

        logger.debug(
            "calling_bulk_create",
            sessions_to_save=len(domain_sessions),
        )

        # Bulk create via repository
        result = self.session_repo.bulk_create(user_id_vo, domain_sessions)
        created_count = result.created_count
        skipped_duplicate_count = len(domain_sessions) - created_count

        logger.debug(
            "bulk_create_result",
            created_count=created_count,
            skipped_duplicate_count=skipped_duplicate_count,
        )

        # Link highlights to created reading sessions
        linked_count = 0
        if result.created_sessions:
            linked_count = self._link_highlights_to_sessions(
                book.id, user_id_vo, result.created_sessions
            )
            logger.info(
                "linked_highlights_to_sessions",
                linked_count=linked_count,
                session_count=len(result.created_sessions),
            )

        self.db.commit()

        logger.info(
            "reading_session_upload_complete",
            created=created_count,
            skipped_duplicate=skipped_duplicate_count,
            linked_highlights=linked_count,
        )

        return ReadingSessionUploadResult(
            book_id=book.id,
            created_count=created_count,
            skipped_duplicate_count=skipped_duplicate_count,
            linked_highlights_count=linked_count,
        )

    def _link_highlights_to_sessions(
        self,
        book_id: BookId,
        user_id: UserId,
        sessions: list[ReadingSession],
    ) -> int:
        """
        Link highlights to reading sessions based on position overlap.

        For each session, finds highlights whose position falls within the session's
        reading range (either page-based for PDFs or xpoint-based for EPUBs).

        Args:
            book_id: ID of the book
            user_id: ID of the user
            sessions: List of newly created reading sessions

        Returns:
            Total number of highlight-session links created
        """
        # Get all highlights for this book via repository
        highlights = self.highlight_repo.find_by_book_id(book_id, user_id)

        if not highlights:
            return 0

        # Build list of (session_id, highlight_id) pairs to link
        session_highlight_pairs = []

        for session in sessions:
            matching_highlights = self._find_matching_highlights(session, highlights)

            if matching_highlights:
                for highlight in matching_highlights:
                    session_highlight_pairs.append((session.id, highlight.id))

        # Bulk insert links via repository
        if session_highlight_pairs:
            return self.session_repo.link_highlights_to_sessions(session_highlight_pairs)

        return 0

    def _find_matching_highlights(
        self,
        session: ReadingSession,
        highlights: list[Highlight],
    ) -> list[Highlight]:
        """
        Find highlights that fall within a reading session's range.

        Matching is done based on:
        - Page-based (PDFs): highlight.page BETWEEN session.start_page AND session.end_page
        - XPoint-based (EPUBs): highlight.start_xpoint is between session's xpoint range

        Args:
            session: The reading session to match against
            highlights: List of candidate highlights

        Returns:
            List of highlights that fall within the session's range
        """
        matching = []

        # Determine if this is a page-based or xpoint-based session
        is_page_based = session.start_page is not None and session.end_page is not None
        is_xpoint_based = session.start_xpoint is not None

        for highlight in highlights:
            try:
                # Page-based matching (PDF) or XPoint-based matching (EPUB)
                if (
                    is_page_based
                    and highlight.page is not None
                    and session.start_page <= highlight.page <= session.end_page  # type: ignore[operator]
                ) or (
                    is_xpoint_based
                    and highlight.xpoints is not None
                    and is_xpoint_in_range(
                        highlight.xpoints.start.to_string(),
                        session.start_xpoint.start.to_string(),  # type: ignore[union-attr]
                        session.start_xpoint.end.to_string(),  # type: ignore[union-attr]
                    )
                ):
                    matching.append(highlight)
            except Exception as e:
                # Log but don't fail - invalid xpoints shouldn't break the whole process
                logger.warning(
                    "highlight_matching_error",
                    highlight_id=highlight.id.value,
                    session_id=session.id.value,
                    error=str(e),
                )
                continue

        return matching
