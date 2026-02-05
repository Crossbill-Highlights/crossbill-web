"""Use case for flashcard AI operations."""

from dataclasses import dataclass

import structlog

from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.domain.common.value_objects.ids import HighlightId, UserId
from src.exceptions import NotFoundError
from src.infrastructure.ai.ai_service import get_ai_flashcard_suggestions_from_text

logger = structlog.get_logger(__name__)


@dataclass
class FlashcardSuggestion:
    """Simple data class for AI suggestions."""

    question: str
    answer: str


class FlashcardAIUseCase:
    """Use case for flashcard AI operations."""

    def __init__(
        self,
        highlight_repository: HighlightRepositoryProtocol,
    ) -> None:
        """Initialize use case with repository protocols."""
        self.highlight_repository = highlight_repository

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
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise NotFoundError(f"Highlight with id {highlight_id} not found")

        ai_suggestions = await get_ai_flashcard_suggestions_from_text(highlight.text)

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
