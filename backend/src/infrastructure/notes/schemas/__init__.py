"""Notes API schemas."""

from src.infrastructure.notes.schemas.note_schemas import (
    Note,
    NoteCreateRequest,
    NoteCreateResponse,
    NoteKindLiteral,
    NoteLinkedChapter,
    NoteLinkedHighlight,
    NoteLinkedTag,
    NoteUpdateRequest,
    NoteUpdateResponse,
    NoteWithLinks,
)

__all__ = [
    "Note",
    "NoteCreateRequest",
    "NoteCreateResponse",
    "NoteKindLiteral",
    "NoteLinkedChapter",
    "NoteLinkedHighlight",
    "NoteLinkedTag",
    "NoteUpdateRequest",
    "NoteUpdateResponse",
    "NoteWithLinks",
]
