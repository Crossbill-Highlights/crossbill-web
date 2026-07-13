"""Shared helpers for note use cases."""

from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.exceptions import ValidationError
from src.domain.common.value_objects import ChapterId, HighlightId, HighlightTagId, UserId
from src.domain.notes.entities.note import NoteKind
from src.domain.notes.exceptions import NoteLinkBookMismatchError
from src.domain.reading.exceptions import (
    ChapterNotFoundError,
    HighlightNotFoundError,
    HighlightTagNotFoundError,
)


def parse_note_kind(kind: str | None) -> NoteKind | None:
    """Convert an API kind string to NoteKind, or raise ValidationError."""
    if kind is None:
        return None
    try:
        return NoteKind(kind)
    except ValueError as exc:
        raise ValidationError(f"Invalid note kind: {kind}") from exc


async def validate_link_targets(
    user_id: UserId,
    allowed_book_ids: set[int],
    chapter_ids: list[int],
    highlight_ids: list[int],
    highlight_tag_ids: list[int],
    chapter_repository: ChapterRepositoryProtocol,
    highlight_repository: HighlightRepositoryProtocol,
    highlight_tag_repository: HighlightTagRepositoryProtocol,
) -> None:
    """Validate that every linked entity exists and belongs to a linked book."""
    for chapter_id in chapter_ids:
        chapter = await chapter_repository.find_by_id(ChapterId(chapter_id), user_id)
        if not chapter:
            raise ChapterNotFoundError(chapter_id)
        if chapter.book_id.value not in allowed_book_ids:
            raise NoteLinkBookMismatchError("Chapter", chapter_id)

    for highlight_id in highlight_ids:
        highlight = await highlight_repository.find_by_id(HighlightId(highlight_id), user_id)
        if not highlight:
            raise HighlightNotFoundError(highlight_id)
        if highlight.book_id.value not in allowed_book_ids:
            raise NoteLinkBookMismatchError("Highlight", highlight_id)

    for tag_id in highlight_tag_ids:
        tag = await highlight_tag_repository.find_by_id(HighlightTagId(tag_id), user_id)
        if not tag:
            raise HighlightTagNotFoundError(tag_id)
        if tag.book_id.value not in allowed_book_ids:
            raise NoteLinkBookMismatchError("HighlightTag", tag_id)
