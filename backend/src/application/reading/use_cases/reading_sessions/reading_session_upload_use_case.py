"""Use case for uploading reading sessions with deduplication and highlight linking."""

from dataclasses import dataclass
from datetime import datetime

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.application.library.protocols.position_index_service import PositionIndexServiceProtocol
from src.application.reading.protocols.highlight_repository import (
    HighlightRepositoryProtocol,
)
from src.application.reading.protocols.reading_session_repository import (
    ReadingSessionRepositoryProtocol,
)
from src.config import get_settings
from src.domain.common.value_objects import (
    BookId,
    ReadingSessionId,
    UserId,
    XPointRange,
)
from src.domain.common.value_objects.position import Position
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.reading_session import ReadingSession
from src.exceptions import BookNotFoundError

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


class ReadingSessionUploadUseCase:
    """Use case for uploading and processing reading sessions."""

    def __init__(
        self,
        session_repository: ReadingSessionRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        position_index_service: PositionIndexServiceProtocol,
        file_repository: FileRepositoryProtocol,
    ) -> None:
        self.session_repository = session_repository
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository
        self.position_index_service = position_index_service
        self.file_repository = file_repository

        settings = get_settings()
        self.min_duration = settings.MINIMUM_READING_SESSION_DURATION

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
        book = self.book_repository.find_by_client_book_id(client_book_id, user_id_vo)

        if not book:
            logger.error(
                "book_not_found_for_reading_session_upload",
                client_book_id=client_book_id,
            )
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found. "
                "Please create the book first"
            )

        # Build position index if EPUB
        position_index = None
        if book.file_type == "epub":
            epub_path = self.file_repository.find_epub(book.id)
            if epub_path:
                position_index = self.position_index_service.build_position_index(epub_path)

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
        sessions = [
            s for s in sessions if (s.end_time - s.start_time).total_seconds() >= self.min_duration
        ]

        # Create domain entities with NEW hash
        domain_sessions: list[ReadingSession] = []
        for session in sessions:
            # Parse XPointRange if both xpoints exist
            xpoint_range = None
            if session.start_xpoint and session.end_xpoint:
                xpoint_range = XPointRange.parse(session.start_xpoint, session.end_xpoint)

            # Resolve positions
            start_position: Position | None = None
            end_position: Position | None = None
            if position_index and session.start_xpoint and session.end_xpoint:
                start_position = position_index.resolve(session.start_xpoint)
                end_position = position_index.resolve(session.end_xpoint)
            elif book.file_type == "pdf":
                if session.start_page is not None:
                    start_position = Position.from_page(session.start_page)
                if session.end_page is not None:
                    end_position = Position.from_page(session.end_page)

            # Create domain entity with our custom hash
            # Use constructor directly to provide our own content_hash
            domain_session = ReadingSession(
                id=ReadingSessionId.generate(),
                user_id=user_id_vo,
                book_id=book.id,
                start_time=session.start_time,
                end_time=session.end_time,
                start_xpoint=xpoint_range,
                start_page=session.start_page,
                end_page=session.end_page,
                start_position=start_position,
                end_position=end_position,
                device_id=session.device_id,
                ai_summary=None,
            )
            domain_sessions.append(domain_session)

        logger.debug(
            "calling_bulk_create",
            sessions_to_save=len(domain_sessions),
        )

        result = self.session_repository.bulk_create(user_id_vo, domain_sessions)
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
        highlights = self.highlight_repository.find_by_book_id(book_id, user_id)

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
            return self.session_repository.link_highlights_to_sessions(session_highlight_pairs)

        return 0

    def _find_matching_highlights(
        self,
        session: ReadingSession,
        highlights: list[Highlight],
    ) -> list[Highlight]:
        """
        Find highlights that fall within a reading session's range.

        Matching is done based on:
        - Position-based (preferred): highlight.position BETWEEN session positions
        - Page-based (fallback): highlight.page BETWEEN session.start_page AND session.end_page

        Args:
            session: The reading session to match against
            highlights: List of candidate highlights

        Returns:
            List of highlights that fall within the session's range
        """
        matching = []

        for highlight in highlights:
            try:
                # Position-based matching (preferred)
                if (
                    session.start_position is not None
                    and session.end_position is not None
                    and highlight.position is not None
                    and session.start_position <= highlight.position <= session.end_position
                ):
                    matching.append(highlight)
                    continue

                # Fallback: page-based matching (when positions not available)
                if (
                    session.start_page is not None
                    and session.end_page is not None
                    and highlight.page is not None
                    and session.start_page <= highlight.page <= session.end_page
                ):
                    matching.append(highlight)

            except Exception as e:
                logger.warning(
                    "highlight_matching_error",
                    highlight_id=highlight.id.value,
                    session_id=session.id.value,
                    error=str(e),
                )
                continue

        return matching
