"""Use case for generating and caching AI summaries for reading sessions."""

import structlog

from src.application.reading.protocols.ebook_text_extraction_service import (
    EbookTextExtractionServiceProtocol,
)
from src.application.reading.protocols.reading_session_repository import (
    ReadingSessionRepositoryProtocol,
)
from src.domain.common.value_objects import ReadingSessionId, UserId
from src.exceptions import ReadingSessionNotFoundError, ValidationError
from src.infrastructure.ai.ai_service import get_ai_summary_from_text

logger = structlog.get_logger(__name__)


class ReadingSessionAISummaryUseCase:
    """Use case for AI summary generation with caching."""

    def __init__(
        self,
        session_repository: ReadingSessionRepositoryProtocol,
        text_extraction_service: EbookTextExtractionServiceProtocol,
    ) -> None:
        """Initialize use case with dependencies."""
        self.session_repository = session_repository
        self.text_extraction_service = text_extraction_service

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

        session = self.session_repository.find_by_id(session_id_vo, user_id_vo)
        if not session:
            raise ReadingSessionNotFoundError(session_id)

        if session.ai_summary:
            logger.info(
                "returning_cached_ai_summary",
                session_id=session_id,
                user_id=user_id,
            )
            return session.ai_summary

        if session.start_xpoint:
            logger.info(
                "extracting_epub_content_for_ai_summary",
                session_id=session_id,
                book_id=session.book_id.value,
            )
            content = self.text_extraction_service.extract_text(
                session.book_id,
                user_id_vo,
                session.start_xpoint.start.to_string(),
                session.start_xpoint.end.to_string(),
            )
        elif session.start_page is not None and session.end_page is not None:
            # Try PDF pages
            content = self.text_extraction_service.extract_text(
                session.book_id,
                user_id_vo,
                session.start_page,
                session.end_page,
            )
        else:
            raise ValidationError("Reading session has no position data (no xpoints or pages)")

        if not content or not content.strip():
            logger.warning(
                "empty_content_extracted",
                session_id=session_id,
            )
            raise ValidationError("No content could be extracted from the reading session")

        logger.info(
            "generating_ai_summary",
            session_id=session_id,
            content_length=len(content),
        )
        ai_summary = await get_ai_summary_from_text(content)

        session.set_ai_summary(ai_summary)
        self.session_repository.save(session)

        logger.info(
            "ai_summary_generated_and_cached",
            session_id=session_id,
            summary_length=len(ai_summary),
        )

        return ai_summary
