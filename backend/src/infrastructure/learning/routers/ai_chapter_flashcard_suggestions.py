"""AI-powered flashcard suggestions for chapters."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.learning.use_cases.flashcards.get_chapter_flashcard_suggestions_use_case import (
    GetChapterFlashcardSuggestionsUseCase,
)
from src.core import container
from src.domain.common.exceptions import DomainError
from src.domain.identity.entities.user import User
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.learning.schemas import (
    FlashcardSuggestionItem,
    HighlightFlashcardSuggestionsResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chapters", tags=["flashcards"])


@router.get(
    "/{chapter_id}/flashcard_suggestions",
    response_model=HighlightFlashcardSuggestionsResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def get_chapter_flashcard_suggestions(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetChapterFlashcardSuggestionsUseCase = Depends(
        inject_use_case(container.get_chapter_flashcard_suggestions_use_case)
    ),
) -> HighlightFlashcardSuggestionsResponse:
    """
    Get AI-generated flashcard suggestions from chapter prereading content.

    Requires the chapter to have a generated pre-reading summary.
    """
    try:
        suggestions_data = await use_case.get_suggestions(chapter_id)

        suggestions = [
            FlashcardSuggestionItem(question=s.question, answer=s.answer) for s in suggestions_data
        ]

        return HighlightFlashcardSuggestionsResponse(suggestions=suggestions)
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            "failed_to_generate_chapter_flashcard_suggestions",
            chapter_id=chapter_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
