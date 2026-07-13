"""Notes API schemas."""

from src.infrastructure.notes.schemas.note_schemas import (
    Note,
    NoteCreateRequest,
    NoteCreateResponse,
    NoteDeleteResponse,
    NoteKindLiteral,
    NoteLinkedChapter,
    NoteLinkedHighlight,
    NoteLinkedTag,
    NotesResponse,
    NoteUpdateRequest,
    NoteUpdateResponse,
    NoteWithLinks,
)

__all__ = [
    "Note",
    "NoteCreateRequest",
    "NoteCreateResponse",
    "NoteDeleteResponse",
    "NoteKindLiteral",
    "NoteLinkedChapter",
    "NoteLinkedHighlight",
    "NoteLinkedTag",
    "NoteUpdateRequest",
    "NoteUpdateResponse",
    "NoteWithLinks",
    "NotesResponse",
]
