"""API routes for flashcard management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.database import DatabaseSession
from src.exceptions import CrossbillError
from src.models import User
from src.services import FlashcardService
from src.services.auth_service import get_current_user

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
        flashcard = service.update_flashcard(
            flashcard_id=flashcard_id,
            user_id=current_user.id,
            question=request.question,
            answer=request.answer,
        )
        return schemas.FlashcardUpdateResponse(
            success=True,
            message="Flashcard updated successfully",
            flashcard=flashcard,
        )
    except CrossbillError:
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
        service.delete_flashcard(flashcard_id=flashcard_id, user_id=current_user.id)
        return schemas.FlashcardDeleteResponse(
            success=True,
            message="Flashcard deleted successfully",
        )
    except CrossbillError:
        raise
    except Exception as e:
        logger.error(f"Failed to delete flashcard {flashcard_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
