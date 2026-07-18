"""Use case for retrieving a single note with linked entities."""

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.notes.protocols.note_repository import NoteRepositoryProtocol
from src.application.notes.use_cases.dtos import NoteWithLinkedEntities
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.tag_repository import (
    TagRepositoryProtocol,
)
from src.domain.common.value_objects import ChapterId, HighlightId, NoteId, TagId, UserId
from src.domain.notes.exceptions import NoteNotFoundError


class GetNoteUseCase:
    """Use case for retrieving a single note with linked entities."""

    def __init__(
        self,
        note_repository: NoteRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        tag_repository: TagRepositoryProtocol,
        flashcard_repository: FlashcardRepositoryProtocol,
    ) -> None:
        self.note_repository = note_repository
        self.chapter_repository = chapter_repository
        self.highlight_repository = highlight_repository
        self.tag_repository = tag_repository
        self.flashcard_repository = flashcard_repository

    async def get_note(self, note_id: int, user_id: int) -> NoteWithLinkedEntities:
        user_id_vo = UserId(user_id)
        note = await self.note_repository.find_by_id(NoteId(note_id), user_id_vo)
        if not note:
            raise NoteNotFoundError(note_id)

        chapters = []
        for chapter_id in note.chapter_ids:
            chapter = await self.chapter_repository.find_by_id(ChapterId(chapter_id), user_id_vo)
            if chapter:
                chapters.append(chapter)

        highlights = []
        for highlight_id in note.highlight_ids:
            highlight = await self.highlight_repository.find_by_id(
                HighlightId(highlight_id), user_id_vo
            )
            # Soft-deleted highlights keep their link rows but are hidden from display
            if highlight and highlight.deleted_at is None:
                highlights.append(highlight)

        tags = []
        for tag_id in note.tag_ids:
            tag = await self.tag_repository.find_by_id(TagId(tag_id), user_id_vo)
            if tag:
                tags.append(tag)

        flashcards = await self.flashcard_repository.find_by_note(NoteId(note_id), user_id_vo)

        return NoteWithLinkedEntities(
            note=note,
            chapters=chapters,
            highlights=highlights,
            tags=tags,
            flashcards=flashcards,
        )
