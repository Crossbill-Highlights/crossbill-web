"""Service layer for reading session-related business logic."""

from collections.abc import Sequence

import structlog
from sqlalchemy.orm import Session

from src import models, repositories, schemas
from src.config import get_settings
from src.exceptions import BookNotFoundError, ReadingSessionNotFoundError, ValidationError
from src.hash_utils import compute_reading_session_hash
from src.repositories.reading_session_repository import ReadingSessionRepository
from src.schemas.reading_session_schemas import (
    ReadingSessionBase,
    ReadingSessionUploadSessionItem,
)
from src.services.ai.ai_service import get_ai_summary_from_text
from src.services.ebook.ebook_service import EbookService
from src.services.ebook.epub.xpoint_utils import is_xpoint_in_range

logger = structlog.get_logger(__name__)


class ReadingSessionService:
    """Service for handling reading session-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = repositories.BookRepository(db)
        self.session_repo = ReadingSessionRepository(db)
        self.highlight_repo = repositories.HighlightRepository(db)
        self.ebook_service = EbookService(db)

    def upload_reading_sessions(
        self,
        client_book_id: str,
        sessions: list[ReadingSessionUploadSessionItem],
        user_id: int,
    ) -> schemas.ReadingSessionUploadResponse:
        """
        Process reading session upload from KOReader for a single book.

        This method:
        1. Gets or creates the book by content hash (with keywords as tags)
        2. Processes sessions and builds database objects
        3. Bulk creates sessions with deduplication
        4. Returns statistics

        Note: All validation is handled by FastAPI before reaching this method.
        If any session is invalid, the entire request fails with 422.

        Args:
            book_data: Book metadata for all sessions
            sessions: List of validated reading sessions for this book
            user_id: ID of the user

        Returns:
            ReadingSessionUploadResponse with upload statistics
        """
        logger.info(
            "processing_reading_session_upload",
            session_count=len(sessions),
            client_book_id=client_book_id,
        )

        # Log session details for debugging
        for idx, session in enumerate(sessions):
            duration = (session.end_time - session.start_time).total_seconds()
            logger.debug(
                "received_session",
                index=idx,
                duration_seconds=duration,
                start_time=session.start_time.isoformat(),
                end_time=session.end_time.isoformat(),
                start_xpoint=session.start_xpoint,
                end_xpoint=session.end_xpoint,
                start_page=session.start_page,
                end_page=session.end_page,
            )

        # Get or create book using BookService (handles client_book_id lookup with content_hash fallback)
        book = self.book_repo.find_by_client_book_id(client_book_id, user_id)

        if not book:
            logger.error(
                "book_not_found_for_highlight_upload",
                client_book_id=client_book_id,
            )
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found. "
                "Please create the book first"
            )

        to_save: list[ReadingSessionBase] = []

        # Filter away sessions where start and end points are the same
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

        for session in sessions:
            session_hash = compute_reading_session_hash(
                book_title=book.title,
                book_author=book.author,
                start_time=session.start_time.isoformat(),
                device_id=session.device_id,
            )

            to_save.append(
                ReadingSessionBase(
                    book_id=book.id,
                    content_hash=session_hash,
                    device_id=session.device_id,
                    start_time=session.start_time,
                    end_time=session.end_time,
                    start_xpoint=session.start_xpoint,
                    end_xpoint=session.end_xpoint,
                    start_page=session.start_page,
                    end_page=session.end_page,
                    content=None,
                    ai_summary=None,
                )
            )

        logger.debug(
            "calling_bulk_create",
            sessions_to_save=len(to_save),
        )

        result = self.session_repo.bulk_create(user_id, to_save)
        created_count = result.created_count
        skipped_duplicate_count = len(to_save) - created_count

        logger.debug(
            "bulk_create_result",
            created_count=created_count,
            skipped_duplicate_count=skipped_duplicate_count,
        )

        # Link highlights to created reading sessions
        if result.created_sessions:
            linked_count = self._link_highlights_to_sessions(
                book.id, user_id, result.created_sessions
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
        )

        return schemas.ReadingSessionUploadResponse(
            success=True,
            message=self._build_upload_message(created_count, skipped_duplicate_count),
            book_id=book.id,
            created_count=created_count,
            skipped_duplicate_count=skipped_duplicate_count,
        )

    def _build_upload_message(
        self,
        created: int,
        skipped_duplicate: int,
    ) -> str:
        """Build a human-readable message summarizing the upload result."""
        parts = []

        if created > 0:
            parts.append(f"Created {created} session{'s' if created != 1 else ''}")

        if skipped_duplicate > 0:
            parts.append(f"{skipped_duplicate} skipped (duplicate)")

        if not parts:
            return "No sessions to process"

        return ". ".join(parts) + "."

    def _link_highlights_to_sessions(
        self,
        book_id: int,
        user_id: int,
        sessions: list[models.ReadingSession],
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
        # Get all highlights for this book that could be matched
        highlights = self.highlight_repo.get_by_book(book_id, user_id)

        if not highlights:
            return 0

        total_links = 0

        for session in sessions:
            matching_highlights = self._find_matching_highlights(session, highlights)

            if matching_highlights:
                # Use the SQLAlchemy relationship to add links
                # This will automatically insert into the join table
                for highlight in matching_highlights:
                    if highlight not in session.highlights:
                        session.highlights.append(highlight)
                        total_links += 1

        self.db.flush()
        return total_links

    def _find_matching_highlights(
        self,
        session: models.ReadingSession,
        highlights: Sequence[models.Highlight],
    ) -> list[models.Highlight]:
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
        is_xpoint_based = session.start_xpoint is not None and session.end_xpoint is not None

        for highlight in highlights:
            try:
                if is_page_based and highlight.page is not None:
                    # Page-based matching (PDF)
                    if session.start_page <= highlight.page <= session.end_page:  # type: ignore[operator]
                        matching.append(highlight)
                elif (
                    is_xpoint_based
                    and highlight.start_xpoint is not None
                    and session.start_xpoint is not None
                    and session.end_xpoint is not None
                    and is_xpoint_in_range(
                        highlight.start_xpoint,
                        session.start_xpoint,
                        session.end_xpoint,
                    )
                ):
                    # XPoint-based matching (EPUB)
                    matching.append(highlight)
            except Exception as e:
                # Log but don't fail - invalid xpoints shouldn't break the whole process
                logger.warning(
                    "highlight_matching_error",
                    highlight_id=highlight.id,
                    session_id=session.id,
                    error=str(e),
                )
                continue

        return matching

    async def get_reading_sessions_for_book(
        self,
        book_id: int,
        user_id: int,
        limit: int = 30,
        offset: int = 0,
    ) -> schemas.ReadingSessionsResponse:
        """Get reading sessions for a specific book."""
        # Validate book exists and belongs to user
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        session_models = self.session_repo.get_by_book_id(book_id, user_id, limit, offset)
        total = self.session_repo.count_by_book_id(book_id, user_id)

        sessions = [schemas.ReadingSession.model_validate(s) for s in session_models]

        for s in sessions:
            if s.start_xpoint and s.end_xpoint:
                text_content = self.ebook_service.extract_text_between(
                    book_id, user_id, s.start_xpoint, s.end_xpoint
                )
                s.content = text_content

        return schemas.ReadingSessionsResponse(
            sessions=sessions,
            total=total,
            offset=offset,
            limit=limit,
        )

    async def get_ai_summary(
        self,
        session_id: int,
        user_id: int,
    ) -> str:
        """Get or generate AI summary for a reading session.

        This method implements caching:
        - If ai_summary exists in DB, return it immediately
        - If null, extract content, generate summary via AI, save to DB, return result

        Args:
            session_id: ID of the reading session
            user_id: ID of the user (for ownership verification)

        Returns:
            The AI-generated summary text

        Raises:
            ReadingSessionNotFoundError: If session not found or user doesn't own it
            ValidationError: If session has no position data (no xpoints or pages)
            BookNotFoundError: If book not found (from epub_service)
            XPointParseError: If xpoint format is invalid (from epub_service)
            XPointNavigationError: If cannot navigate to xpoint (from epub_service)
        """
        session = self.session_repo.get_by_id(session_id, user_id)
        if not session:
            raise ReadingSessionNotFoundError(session_id)

        if session.ai_summary:
            logger.info(
                "returning_cached_ai_summary",
                session_id=session_id,
                user_id=user_id,
            )
            return session.ai_summary

        content = None

        # Try EPUB xpoints first
        if session.start_xpoint and session.end_xpoint:
            logger.info(
                "extracting_epub_content_for_ai_summary",
                session_id=session_id,
                book_id=session.book_id,
            )
            content = self.ebook_service.extract_text_between(
                session.book_id,
                user_id,
                session.start_xpoint,
                session.end_xpoint,
            )
        elif session.start_page is not None and session.end_page is not None:
            content = self.ebook_service.extract_text_between(
                session.book_id,
                user_id,
                session.start_page,
                session.end_page,
            )
        else:
            # Session has neither xpoints nor pages (shouldn't happen due to validation)
            raise ValidationError("Reading session has no position data (no xpoints or pages)")

        # Check if content was extracted
        if not content or not content.strip():
            logger.warning(
                "empty_content_extracted",
                session_id=session_id,
            )
            raise ValidationError("No content could be extracted from the reading session")

        # Generate AI summary
        logger.info(
            "generating_ai_summary",
            session_id=session_id,
            content_length=len(content),
        )
        ai_summary = await get_ai_summary_from_text(content)

        # Save to database
        self.session_repo.update_ai_summary(session_id, user_id, ai_summary)
        self.db.commit()

        logger.info(
            "ai_summary_generated_and_cached",
            session_id=session_id,
            summary_length=len(ai_summary),
        )

        return ai_summary
