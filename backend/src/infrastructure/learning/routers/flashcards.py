"""API routes for flashcard management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.learning.use_cases.flashcards.delete_flashcard_use_case import (
    DeleteFlashcardUseCase,
)
from src.application.learning.use_cases.flashcards.update_flashcard_use_case import (
    UpdateFlashcardUseCase,
)
from src.core import container
from src.domain.common.exceptions import DomainError
from src.domain.identity.entities.user import User
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.learning.schemas import (
    Flashcard,
    FlashcardDeleteResponse,
    FlashcardUpdateRequest,
    FlashcardUpdateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.put(
    "/{flashcard_id}",
    response_model=FlashcardUpdateResponse,
    status_code=status.HTTP_200_OK,
)
def update_flashcard(
    flashcard_id: int,
    request: FlashcardUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: UpdateFlashcardUseCase = Depends(
        inject_use_case(container.update_flashcard_use_case)
    ),
) -> FlashcardUpdateResponse:
    """
    Update a flashcard's question and/or answer.

    Args:
        flashcard_id: ID of the flashcard to update
        request: Request containing updated question and/or answer
        use_case: FlashcardUseCase injected via dependency container

    Returns:
        Updated flashcard

    Raises:
        HTTPException: If flashcard not found or update fails
    """
    try:
        flashcard_entity = use_case.update_flashcard(
            flashcard_id=flashcard_id,
            user_id=current_user.id.value,
            question=request.question,
            answer=request.answer,
        )
        # Manually construct Pydantic schema from domain entity
        flashcard = Flashcard(
            id=flashcard_entity.id.value,
            user_id=flashcard_entity.user_id.value,
            book_id=flashcard_entity.book_id.value,
            highlight_id=flashcard_entity.highlight_id.value
            if flashcard_entity.highlight_id
            else None,
            question=flashcard_entity.question,
            answer=flashcard_entity.answer,
        )
        return FlashcardUpdateResponse(
            success=True,
            message="Flashcard updated successfully",
            flashcard=flashcard,
        )
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to update flashcard {flashcard_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.delete(
    "/{flashcard_id}",
    response_model=FlashcardDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_flashcard(
    flashcard_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: DeleteFlashcardUseCase = Depends(
        inject_use_case(container.delete_flashcard_use_case)
    ),
) -> FlashcardDeleteResponse:
    """
    Delete a flashcard.

    Args:
        flashcard_id: ID of the flashcard to delete
        use_case: FlashcardUseCase injected via dependency container

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If flashcard not found or deletion fails
    """
    try:
        use_case.delete_flashcard(flashcard_id=flashcard_id, user_id=current_user.id.value)
        return FlashcardDeleteResponse(
            success=True,
            message="Flashcard deleted successfully",
        )
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to delete flashcard {flashcard_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
