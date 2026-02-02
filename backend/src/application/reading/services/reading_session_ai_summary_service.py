"""Service for generating and caching AI summaries for reading sessions."""

import structlog
from sqlalchemy.orm import Session

from src.application.library.services.ebook_text_extraction_service import (
    EbookTextExtractionService,
)
from src.domain.common.value_objects import ReadingSessionId, UserId
from src.exceptions import ReadingSessionNotFoundError, ValidationError
from src.infrastructure.ai.ai_service import get_ai_summary_from_text
from src.infrastructure.reading.repositories.reading_session_repository import (
    ReadingSessionRepository,
)

logger = structlog.get_logger(__name__)


class ReadingSessionAISummaryService:
    """Service for AI summary generation with caching."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.session_repo = ReadingSessionRepository(db)
        self.text_extraction_service = EbookTextExtractionService(db)

    async def get_or_generate_summary(self, session_id: int, user_id: int) -> str:
        """
        Get or generate AI summary for a reading session.

        This method implements caching:
        - If ai_summary exists in DB, return it immediately (cache hit)
        - If null, extract content, generate summary via AI, save to DB, return result

        Args:
            session_id: ID of the reading session
            user_id: ID of the user (for ownership verification)

        Returns:
            The AI-generated summary text

        Raises:
            ReadingSessionNotFoundError: If session not found or user doesn't own it
            ValidationError: If session has no position data (no xpoints or pages)
        """
        session_id_vo = ReadingSessionId(session_id)
        user_id_vo = UserId(user_id)

        session = self.session_repo.find_by_id(session_id_vo, user_id_vo)
        if not session:
            raise ReadingSessionNotFoundError(session_id)

        # Check for cached summary
        if session.ai_summary:
            logger.info(
                "returning_cached_ai_summary",
                session_id=session_id,
                user_id=user_id,
            )
            return session.ai_summary

        # Extract content from ebook
        content = None

        # Try EPUB xpoints first
        if session.start_xpoint:
            logger.info(
                "extracting_epub_content_for_ai_summary",
                session_id=session_id,
                book_id=session.book_id.value,
            )
            content = self.text_extraction_service.extract_text(
                session.book_id.value,
                user_id,
                session.start_xpoint.start.to_string(),
                session.start_xpoint.end.to_string(),
            )
        elif session.start_page is not None and session.end_page is not None:
            # Try PDF pages
            content = self.text_extraction_service.extract_text(
                session.book_id.value,
                user_id,
                session.start_page,
                session.end_page,
            )
        else:
            # Session has neither xpoints nor pages
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

        # Update domain entity
        session.set_ai_summary(ai_summary)

        # Save via repository
        self.session_repo.save(session)
        self.db.commit()

        logger.info(
            "ai_summary_generated_and_cached",
            session_id=session_id,
            summary_length=len(ai_summary),
        )

        return ai_summary
