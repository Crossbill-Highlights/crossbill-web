"""API router for chapter text content extraction."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.application.reading.use_cases.chapter_content_use_case import (
    ChapterContentUseCase,
)
from src.core import container
from src.domain.common.exceptions import DomainError
from src.domain.identity import User
from src.exceptions import CrossbillError
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.reading.schemas.chapter_content_schemas import (
    ChapterContentResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chapters", tags=["chapters"])


@router.get(
    "/{chapter_id}/content",
    response_model=ChapterContentResponse,
    status_code=status.HTTP_200_OK,
)
def get_chapter_content(
    chapter_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: ChapterContentUseCase = Depends(inject_use_case(container.chapter_content_use_case)),
) -> ChapterContentResponse:
    """Get the full text content of a chapter from the EPUB file."""
    try:
        content, chapter_name, book_id = use_case.get_chapter_content(
            chapter_id=chapter_id,
            user_id=current_user.id.value,
        )

        return ChapterContentResponse(
            chapter_id=chapter_id,
            chapter_name=chapter_name,
            book_id=book_id,
            content=content,
        )
    except DomainError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except CrossbillError:
        raise
    except Exception as e:
        logger.error(f"Failed to get chapter content: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract chapter content",
        ) from e
