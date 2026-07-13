"""Use case for creating notes."""

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.notes.protocols.note_repository import NoteRepositoryProtocol
from src.application.notes.use_cases.helpers import parse_note_kind, validate_link_targets
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.notes.entities.note import Note
from src.domain.reading.exceptions import BookNotFoundError

logger = structlog.get_logger(__name__)


class CreateNoteUseCase:
    """Use case for creating notes."""

    def __init__(
        self,
        note_repository: NoteRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        highlight_tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.note_repository = note_repository
        self.book_repository = book_repository
        self.chapter_repository = chapter_repository
        self.highlight_repository = highlight_repository
        self.highlight_tag_repository = highlight_tag_repository

    async def create_note(
        self,
        user_id: int,
        title: str,
        body: str,
        kind: str | None,
        book_id: int,
        chapter_ids: list[int],
        highlight_ids: list[int],
        highlight_tag_ids: list[int],
    ) -> Note:
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        book = await self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        await validate_link_targets(
            user_id=user_id_vo,
            allowed_book_ids={book_id},
            chapter_ids=chapter_ids,
            highlight_ids=highlight_ids,
            highlight_tag_ids=highlight_tag_ids,
            chapter_repository=self.chapter_repository,
            highlight_repository=self.highlight_repository,
            highlight_tag_repository=self.highlight_tag_repository,
        )

        note = Note.create(
            user_id=user_id_vo,
            title=title,
            body=body,
            kind=parse_note_kind(kind),
            book_ids=[book_id],
            chapter_ids=chapter_ids,
            highlight_ids=highlight_ids,
            highlight_tag_ids=highlight_tag_ids,
        )
        note = await self.note_repository.save(note)

        logger.info("created_note", note_id=note.id.value, book_id=book_id)
        return note
