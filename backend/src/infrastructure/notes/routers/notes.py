"""API routes for note management."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from starlette import status

from src.application.notes.use_cases.create_note_use_case import CreateNoteUseCase
from src.application.notes.use_cases.dtos import NoteWithLinkedEntities
from src.application.notes.use_cases.get_note_use_case import GetNoteUseCase
from src.application.notes.use_cases.get_notes_by_book_use_case import GetNotesByBookUseCase
from src.core import container
from src.domain.identity import User
from src.domain.notes.entities.note import Note as NoteEntity
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.notes.schemas import (
    Note,
    NoteCreateRequest,
    NoteCreateResponse,
    NoteKindLiteral,
    NoteLinkedChapter,
    NoteLinkedHighlight,
    NoteLinkedTag,
    NotesResponse,
    NoteWithLinks,
)

router = APIRouter(tags=["notes"])

HIGHLIGHT_SNIPPET_LENGTH = 200


def note_entity_to_schema(entity: NoteEntity) -> Note:
    """Convert a Note domain entity to its response schema."""
    return Note(
        id=entity.id.value,
        user_id=entity.user_id.value,
        title=entity.title,
        body=entity.body,
        kind=entity.kind.value if entity.kind else None,
        book_ids=entity.book_ids,
        chapter_ids=entity.chapter_ids,
        highlight_ids=entity.highlight_ids,
        highlight_tag_ids=entity.highlight_tag_ids,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def note_with_links_to_schema(dto: NoteWithLinkedEntities) -> NoteWithLinks:
    """Convert a NoteWithLinkedEntities DTO to its response schema."""
    base = note_entity_to_schema(dto.note)
    return NoteWithLinks(
        **base.model_dump(),
        chapters=[
            NoteLinkedChapter(id=chapter.id.value, name=chapter.name) for chapter in dto.chapters
        ],
        highlights=[
            NoteLinkedHighlight(
                id=highlight.id.value, text=highlight.text[:HIGHLIGHT_SNIPPET_LENGTH]
            )
            for highlight in dto.highlights
        ],
        highlight_tags=[
            NoteLinkedTag(id=tag.id.value, name=tag.name) for tag in dto.highlight_tags
        ],
    )


@router.post(
    "/notes",
    response_model=NoteCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    request: NoteCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: CreateNoteUseCase = Depends(inject_use_case(container.notes.create_note_use_case)),
) -> NoteCreateResponse:
    note_entity = await use_case.create_note(
        user_id=current_user.id.value,
        title=request.title,
        body=request.body,
        kind=request.kind,
        book_id=request.book_id,
        chapter_ids=request.chapter_ids,
        highlight_ids=request.highlight_ids,
        highlight_tag_ids=request.highlight_tag_ids,
    )
    return NoteCreateResponse(
        success=True,
        message="Note created successfully",
        note=note_entity_to_schema(note_entity),
    )


@router.get(
    "/notes/{note_id}",
    response_model=NoteWithLinks,
    status_code=status.HTTP_200_OK,
)
async def get_note(
    note_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetNoteUseCase = Depends(inject_use_case(container.notes.get_note_use_case)),
) -> NoteWithLinks:
    dto = await use_case.get_note(note_id=note_id, user_id=current_user.id.value)
    return note_with_links_to_schema(dto)


@router.get(
    "/books/{book_id}/notes",
    response_model=NotesResponse,
    status_code=status.HTTP_200_OK,
)
async def get_notes_for_book(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    kind: Annotated[NoteKindLiteral | None, Query()] = None,
    chapter_id: Annotated[int | None, Query()] = None,
    highlight_id: Annotated[int | None, Query()] = None,
    highlight_tag_id: Annotated[int | None, Query()] = None,
    use_case: GetNotesByBookUseCase = Depends(
        inject_use_case(container.notes.get_notes_by_book_use_case)
    ),
) -> NotesResponse:
    dtos = await use_case.get_notes(
        book_id=book_id,
        user_id=current_user.id.value,
        kind=kind,
        chapter_id=chapter_id,
        highlight_id=highlight_id,
        highlight_tag_id=highlight_tag_id,
    )
    return NotesResponse(notes=[note_with_links_to_schema(dto) for dto in dtos])
