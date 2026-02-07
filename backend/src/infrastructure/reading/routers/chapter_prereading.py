"""API router for chapter prereading content."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.application.reading.use_cases.chapter_prereading_use_case import (
    ChapterPrereadingUseCase,
)
from src.core import container
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.domain.identity import User
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.reading.schemas.chapter_prereading_schemas import (
    BookPrereadingResponse,
    ChapterPrereadingResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chapters", tags=["prereading"])


@router.get(
    "/{chapter_id}/prereading",
    response_model=ChapterPrereadingResponse | None,
    status_code=status.HTTP_200_OK,
)
def get_chapter_prereading(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: ChapterPrereadingUseCase = Depends(
        inject_use_case(container.chapter_prereading_use_case)
    ),
) -> ChapterPrereadingResponse | None:
    """Get existing prereading content for a chapter."""
    try:
        result = use_case.get_prereading_content(
            chapter_id=ChapterId(chapter_id),
            user_id=UserId(current_user.id.value),
        )

        if not result:
            return None

        return ChapterPrereadingResponse(
            id=result.id.value,
            chapter_id=result.chapter_id.value,
            summary=result.summary,
            keypoints=result.keypoints,
            generated_at=result.generated_at,
            ai_model=result.ai_model,
        )
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{chapter_id}/prereading/generate",
    response_model=ChapterPrereadingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_chapter_prereading(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: ChapterPrereadingUseCase = Depends(
        inject_use_case(container.chapter_prereading_use_case)
    ),
) -> ChapterPrereadingResponse:
    """Generate prereading content for a chapter."""
    try:
        result = await use_case.generate_prereading_content(
            chapter_id=ChapterId(chapter_id),
            user_id=UserId(current_user.id.value),
        )

        return ChapterPrereadingResponse(
            id=result.id.value,
            chapter_id=result.chapter_id.value,
            summary=result.summary,
            keypoints=result.keypoints,
            generated_at=result.generated_at,
            ai_model=result.ai_model,
        )
    except DomainError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        if "position data" in str(e).lower() or "too short" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate prereading content",
        ) from e


book_prereading_router = APIRouter(prefix="/books", tags=["prereading"])


@book_prereading_router.get(
    "/{book_id}/prereading",
    response_model=BookPrereadingResponse,
    status_code=status.HTTP_200_OK,
)
def get_book_prereading(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: ChapterPrereadingUseCase = Depends(
        inject_use_case(container.chapter_prereading_use_case)
    ),
) -> BookPrereadingResponse:
    """Get all prereading content for chapters in a book."""
    try:
        results = use_case.get_all_prereading_for_book(
            book_id=BookId(book_id),
            user_id=UserId(current_user.id.value),
        )

        return BookPrereadingResponse(
            items=[
                ChapterPrereadingResponse(
                    id=r.id.value,
                    chapter_id=r.chapter_id.value,
                    summary=r.summary,
                    keypoints=r.keypoints,
                    generated_at=r.generated_at,
                    ai_model=r.ai_model,
                )
                for r in results
            ]
        )
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
