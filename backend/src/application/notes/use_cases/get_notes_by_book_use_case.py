"""Use case for retrieving notes for a book with linked entities."""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.notes.protocols.note_repository import NoteRepositoryProtocol
from src.application.notes.use_cases.dtos import NoteWithLinkedEntities
from src.application.notes.use_cases.helpers import parse_note_kind
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, ChapterId, HighlightId, HighlightTagId, UserId
from src.domain.reading.exceptions import BookNotFoundError


class GetNotesByBookUseCase:
    """Use case for retrieving notes for a book with linked entities."""

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

    async def get_notes(
        self,
        book_id: int,
        user_id: int,
        kind: str | None = None,
        chapter_id: int | None = None,
        highlight_id: int | None = None,
        highlight_tag_id: int | None = None,
    ) -> list[NoteWithLinkedEntities]:
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        book = await self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        notes = await self.note_repository.find_by_book(
            book_id_vo,
            user_id_vo,
            kind=parse_note_kind(kind),
            chapter_id=ChapterId(chapter_id) if chapter_id is not None else None,
            highlight_id=HighlightId(highlight_id) if highlight_id is not None else None,
            highlight_tag_id=(
                HighlightTagId(highlight_tag_id) if highlight_tag_id is not None else None
            ),
        )
        if not notes:
            return []

        # Batch-load the book's entities once and resolve links from maps.
        # Soft-deleted highlights are excluded by find_by_book_id, so linked
        # deleted highlights silently drop out of the summaries.
        chapters_by_id = {
            chapter.id.value: chapter
            for chapter in await self.chapter_repository.find_all_by_book(book_id_vo, user_id_vo)
        }
        highlights_by_id = {
            highlight.id.value: highlight
            for highlight in await self.highlight_repository.find_by_book_id(book_id_vo, user_id_vo)
        }
        # Fetch the tags the notes actually reference by id. (find_by_book only
        # returns tags with active highlight associations, which would drop
        # tags attached to a note but no highlight.)
        referenced_tag_ids = {tid for note in notes for tid in note.highlight_tag_ids}
        tags_by_id = {
            tag.id.value: tag
            for tag in await self.highlight_tag_repository.find_by_ids(
                list(referenced_tag_ids), user_id_vo
            )
        }

        return [
            NoteWithLinkedEntities(
                note=note,
                chapters=[chapters_by_id[cid] for cid in note.chapter_ids if cid in chapters_by_id],
                highlights=[
                    highlights_by_id[hid] for hid in note.highlight_ids if hid in highlights_by_id
                ],
                highlight_tags=[
                    tags_by_id[tid] for tid in note.highlight_tag_ids if tid in tags_by_id
                ],
            )
            for note in notes
        ]
