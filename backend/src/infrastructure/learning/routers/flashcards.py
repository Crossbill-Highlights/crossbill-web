"""API routes for flashcard management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.application.learning.services.flashcard_service import FlashcardService
from src.database import DatabaseSession
from src.domain.common.exceptions import DomainError
from src.domain.identity.entities.user import User
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.identity.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.put(
    "/{flashcard_id}",
    response_model=schemas.FlashcardUpdateResponse,
    status_code=status.HTTP_200_OK,
)
def update_flashcard(
    flashcard_id: int,
    request: schemas.FlashcardUpdateRequest,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.FlashcardUpdateResponse:
    """
    Update a flashcard's question and/or answer.

    Args:
        flashcard_id: ID of the flashcard to update
        request: Request containing updated question and/or answer
        db: Database session

    Returns:
        Updated flashcard

    Raises:
        HTTPException: If flashcard not found or update fails
    """
    try:
        service = FlashcardService(db)
        flashcard_entity = service.update_flashcard(
            flashcard_id=flashcard_id,
            user_id=current_user.id.value,
            question=request.question,
            answer=request.answer,
        )
        # Manually construct Pydantic schema from domain entity
        flashcard = schemas.Flashcard(
            id=flashcard_entity.id.value,
            user_id=flashcard_entity.user_id.value,
            book_id=flashcard_entity.book_id.value,
            highlight_id=flashcard_entity.highlight_id.value
            if flashcard_entity.highlight_id
            else None,
            question=flashcard_entity.question,
            answer=flashcard_entity.answer,
        )
        return schemas.FlashcardUpdateResponse(
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
    response_model=schemas.FlashcardDeleteResponse,
    status_code=status.HTTP_200_OK,
)
def delete_flashcard(
    flashcard_id: int,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.FlashcardDeleteResponse:
    """
    Delete a flashcard.

    Args:
        flashcard_id: ID of the flashcard to delete
        db: Database session

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If flashcard not found or deletion fails
    """
    try:
        service = FlashcardService(db)
        service.delete_flashcard(flashcard_id=flashcard_id, user_id=current_user.id.value)
        return schemas.FlashcardDeleteResponse(
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
