"""AI-powered features for highlights."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.application.learning.services.flashcard_ai_service import FlashcardAIService
from src.database import DatabaseSession
from src.domain.common.exceptions import DomainError
from src.domain.identity.entities.user import User
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.identity.dependencies import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/highlights", tags=["highlights", "ai"])


@router.get(
    "/{highlight_id}/flashcard_suggestions",
    response_model=schemas.HighlightFlashcardSuggestionsResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def get_highlight_flashcard_suggestions(
    highlight_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightFlashcardSuggestionsResponse:
    """
    Get AI-generated flashcard suggestions for a highlight.

    Args:
        highlight_id: ID of the highlight
        current_user: Authenticated user

    Returns:
        HighlightFlashcardSuggestionsResponse with list of flashcard suggestions

    Raises:
        HTTPException 404: If highlight not found or not owned by user
        HTTPException 500: For unexpected errors
    """
    try:
        service = FlashcardAIService(db)
        suggestions_data = await service.get_flashcard_suggestions(
            highlight_id, current_user.id.value
        )

        # Convert data classes to Pydantic schemas
        suggestions = [
            schemas.FlashcardSuggestionItem(question=s.question, answer=s.answer)
            for s in suggestions_data
        ]

        return schemas.HighlightFlashcardSuggestionsResponse(suggestions=suggestions)
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(
            "failed_to_generate_flashcard_suggestions",
            highlight_id=highlight_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
