"""Application service for flashcard AI operations."""

from dataclasses import dataclass

import structlog
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import HighlightId, UserId
from src.exceptions import ValidationError
from src.infrastructure.ai.ai_service import get_ai_flashcard_suggestions_from_text
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository

logger = structlog.get_logger(__name__)


@dataclass
class FlashcardSuggestion:
    """Simple data class for AI suggestions."""

    question: str
    answer: str


class FlashcardAIService:
    """Application service for flashcard AI operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.highlight_repository = HighlightRepository(db)

    async def get_flashcard_suggestions(
        self, highlight_id: int, user_id: int
    ) -> list[FlashcardSuggestion]:
        """
        Get AI-generated flashcard suggestions for a highlight.

        Args:
            highlight_id: ID of the highlight
            user_id: ID of the user (for ownership verification)

        Returns:
            List of flashcard suggestions

        Raises:
            ValidationError: If highlight not found or user doesn't own it
        """
        # Convert to value objects
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        # Validate highlight exists and belongs to user
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise ValidationError(f"Highlight with id {highlight_id} not found", status_code=404)

        # Get AI suggestions from highlight text
        ai_suggestions = await get_ai_flashcard_suggestions_from_text(highlight.text)

        # Convert to data classes
        suggestions = [
            FlashcardSuggestion(question=suggestion.question, answer=suggestion.answer)
            for suggestion in ai_suggestions
        ]

        logger.info(
            "flashcard_suggestions_generated",
            highlight_id=highlight_id,
            suggestion_count=len(suggestions),
        )

        return suggestions
