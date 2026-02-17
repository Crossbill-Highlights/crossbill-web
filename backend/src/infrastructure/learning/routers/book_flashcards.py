import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.application.learning.use_cases.flashcards.create_flashcard_for_book_use_case import (
    CreateFlashcardForBookUseCase,
)
from src.application.learning.use_cases.flashcards.get_flashcards_by_book_use_case import (
    GetFlashcardsByBookUseCase,
)
from src.core import container
from src.domain.common import DomainError
from src.domain.identity import User
from src.exceptions import CrossbillError, ValidationError
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.learning.schemas import (
    Flashcard,
    FlashcardCreateRequest,
    FlashcardCreateResponse,
    FlashcardsWithHighlightsResponse,
    FlashcardWithHighlight,
)
from src.infrastructure.reading.schemas import (
    HighlightResponseBase,
    HighlightStyleResponse,
    HighlightTagInBook,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["flashcards"])


@router.post(
    "/{book_id}/flashcards",
    response_model=FlashcardCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_flashcard_for_book(
    book_id: int,
    request: FlashcardCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: CreateFlashcardForBookUseCase = Depends(
        inject_use_case(container.create_flashcard_for_book_use_case)
    ),
) -> FlashcardCreateResponse:
    """
    Create a standalone flashcard for a book (without a highlight).

    This creates a flashcard that is associated with a book but not tied
    to any specific highlight.

    Args:
        book_id: ID of the book
        request: Request containing question and answer
        use_case: FlashcardUseCase injected via dependency container

    Returns:
        Created flashcard

    Raises:
        HTTPException: If book not found or creation fails
    """
    try:
        flashcard_entity = use_case.create_flashcard(
            book_id=book_id,
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
        return FlashcardCreateResponse(
            success=True,
            message="Flashcard created successfully",
            flashcard=flashcard,
        )
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to create flashcard for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e


@router.get(
    "/{book_id}/flashcards",
    response_model=FlashcardsWithHighlightsResponse,
    status_code=status.HTTP_200_OK,
)
def get_flashcards_for_book(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetFlashcardsByBookUseCase = Depends(
        inject_use_case(container.get_flashcards_by_book_use_case)
    ),
) -> FlashcardsWithHighlightsResponse:
    """
    Get all flashcards for a book with embedded highlight data.

    Returns all flashcards ordered by creation date (newest first).

    Args:
        book_id: ID of the book
        use_case: FlashcardUseCase injected via dependency container

    Returns:
        List of flashcards with highlight data for the book

    Raises:
        HTTPException: If book not found or fetching fails
    """
    try:
        # Get flashcards with highlights from use case (returns DTOs)
        flashcards_with_highlights = use_case.get_flashcards(book_id, current_user.id.value)

        # Convert DTOs to Pydantic schemas
        flashcards = []
        for dto in flashcards_with_highlights:
            fc = dto.flashcard
            highlight = dto.highlight
            chapter = dto.chapter
            tags = dto.highlight_tags

            # Convert highlight to Pydantic schema if present
            highlight_schema = None
            if highlight:
                # Manually construct highlight schema
                highlight_schema = HighlightResponseBase(
                    id=highlight.id.value,
                    book_id=highlight.book_id.value,
                    chapter_id=highlight.chapter_id.value if highlight.chapter_id else None,
                    text=highlight.text,
                    note=highlight.note,
                    page=highlight.page,
                    datetime=highlight.datetime,
                    chapter=chapter.name if chapter else None,
                    chapter_number=chapter.chapter_number if chapter else None,
                    highlight_style=HighlightStyleResponse(**highlight.highlight_style.to_json()),
                    created_at=highlight.created_at,
                    updated_at=highlight.updated_at,
                    highlight_tags=[
                        HighlightTagInBook(
                            id=tag.id.value,
                            name=tag.name,
                            tag_group_id=tag.tag_group_id,
                        )
                        for tag in tags
                    ],
                )

            # Construct flashcard schema with highlight
            flashcard_schema = FlashcardWithHighlight(
                id=fc.id.value,
                user_id=fc.user_id.value,
                book_id=fc.book_id.value,
                highlight_id=fc.highlight_id.value if fc.highlight_id else None,
                question=fc.question,
                answer=fc.answer,
                highlight=highlight_schema,
            )
            flashcards.append(flashcard_schema)

        return FlashcardsWithHighlightsResponse(flashcards=flashcards)
    except (CrossbillError, DomainError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Failed to get flashcards for book {book_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later.",
        ) from e
