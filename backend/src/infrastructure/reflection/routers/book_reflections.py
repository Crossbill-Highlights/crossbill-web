"""API routes for book reflections."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.application.reflection.use_cases.get_book_reflection_use_case import (
    GetBookReflectionUseCase,
)
from src.application.reflection.use_cases.upsert_book_reflection_use_case import (
    UpsertBookReflectionUseCase,
)
from src.core import container
from src.domain.identity import User
from src.domain.reflection.entities.book_reflection import BookReflection as BookReflectionEntity
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.reflection.schemas import (
    BookReflectionResponse,
    BookReflectionUpdateRequest,
)

router = APIRouter(prefix="/books", tags=["reflections"])


def _reflection_to_schema(entity: BookReflectionEntity) -> BookReflectionResponse:
    """Convert a BookReflection domain entity to its response schema."""
    return BookReflectionResponse(
        book_id=entity.book_id.value,
        what_is_it_about=entity.what_is_it_about,
        what_does_it_say=entity.what_does_it_say,
        do_i_agree=entity.do_i_agree,
        so_what=entity.so_what,
        note_ids=entity.note_ids,
    )


@router.get(
    "/{book_id}/reflection",
    response_model=BookReflectionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_book_reflection(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetBookReflectionUseCase = Depends(
        inject_use_case(container.reflection.get_book_reflection_use_case)
    ),
) -> BookReflectionResponse:
    reflection = await use_case.get_reflection(book_id=book_id, user_id=current_user.id.value)
    return _reflection_to_schema(reflection)


@router.put(
    "/{book_id}/reflection",
    response_model=BookReflectionResponse,
    status_code=status.HTTP_200_OK,
)
async def upsert_book_reflection(
    book_id: int,
    request: BookReflectionUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: UpsertBookReflectionUseCase = Depends(
        inject_use_case(container.reflection.upsert_book_reflection_use_case)
    ),
) -> BookReflectionResponse:
    reflection = await use_case.upsert_reflection(
        book_id=book_id,
        user_id=current_user.id.value,
        what_is_it_about=request.what_is_it_about,
        what_does_it_say=request.what_does_it_say,
        do_i_agree=request.do_i_agree,
        so_what=request.so_what,
        note_ids=request.note_ids,
    )
    return _reflection_to_schema(reflection)
