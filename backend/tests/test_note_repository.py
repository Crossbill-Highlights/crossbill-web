"""Tests for NoteRepository."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import models
from src.domain.common.value_objects import (
    BookId,
    ChapterId,
    HighlightId,
    HighlightTagId,
    NoteId,
    UserId,
)
from src.domain.notes.entities.note import Note, NoteKind
from src.infrastructure.notes.repositories.note_repository import NoteRepository


@pytest.fixture
def note_repository(db_session: AsyncSession) -> NoteRepository:
    return NoteRepository(db_session)


@pytest.fixture
async def saved_note(
    note_repository: NoteRepository,
    test_user: models.User,
    test_book: models.Book,
    test_chapter: models.Chapter,
) -> Note:
    note = Note.create(
        user_id=UserId(test_user.id),
        title="Raskolnikov",
        body="Main character of Crime and Punishment",
        kind=NoteKind.CHARACTER,
        book_ids=[test_book.id],
        chapter_ids=[test_chapter.id],
    )
    return await note_repository.save(note)


class TestNoteRepositorySave:
    async def test_create_persists_note_with_links(
        self,
        saved_note: Note,
        db_session: AsyncSession,
        test_book: models.Book,
        test_chapter: models.Chapter,
    ) -> None:
        assert saved_note.id.value > 0
        assert saved_note.book_ids == [test_book.id]
        assert saved_note.chapter_ids == [test_chapter.id]
        result = await db_session.execute(select(models.Note).filter_by(id=saved_note.id.value))
        orm_note = result.scalar_one()
        assert orm_note.title == "Raskolnikov"
        assert orm_note.kind == "character"

    async def test_save_with_highlight_and_tag_links(
        self,
        note_repository: NoteRepository,
        test_user: models.User,
        test_book: models.Book,
        test_highlight: models.Highlight,
        test_highlight_tag: models.HighlightTag,
    ) -> None:
        note = Note.create(
            user_id=UserId(test_user.id),
            title="Stoicism",
            book_ids=[test_book.id],
            highlight_ids=[test_highlight.id],
            highlight_tag_ids=[test_highlight_tag.id],
        )
        saved = await note_repository.save(note)
        assert saved.highlight_ids == [test_highlight.id]
        assert saved.highlight_tag_ids == [test_highlight_tag.id]

    async def test_update_replaces_links_and_content(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_highlight: models.Highlight,
    ) -> None:
        saved_note.update_content(title="Rodion", body="Updated", kind=NoteKind.CHARACTER)
        saved_note.replace_links(
            book_ids=saved_note.book_ids,
            chapter_ids=[],
            highlight_ids=[test_highlight.id],
            highlight_tag_ids=[],
        )
        updated = await note_repository.save(saved_note)
        assert updated.title == "Rodion"
        assert updated.chapter_ids == []
        assert updated.highlight_ids == [test_highlight.id]


class TestNoteRepositoryFind:
    async def test_find_by_id(
        self, note_repository: NoteRepository, saved_note: Note, test_user: models.User
    ) -> None:
        found = await note_repository.find_by_id(saved_note.id, UserId(test_user.id))
        assert found is not None
        assert found.title == "Raskolnikov"

    async def test_find_by_id_wrong_user_returns_none(
        self, note_repository: NoteRepository, saved_note: Note
    ) -> None:
        found = await note_repository.find_by_id(saved_note.id, UserId(999))
        assert found is None

    async def test_find_by_book(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_book: models.Book,
        test_user: models.User,
    ) -> None:
        notes = await note_repository.find_by_book(BookId(test_book.id), UserId(test_user.id))
        assert [n.id for n in notes] == [saved_note.id]

    async def test_find_by_book_orders_by_title_case_insensitive(
        self,
        note_repository: NoteRepository,
        test_book: models.Book,
        test_user: models.User,
    ) -> None:
        for title in ["banana", "Apple", "cherry"]:
            await note_repository.save(
                Note.create(
                    user_id=UserId(test_user.id),
                    title=title,
                    book_ids=[test_book.id],
                )
            )
        notes = await note_repository.find_by_book(BookId(test_book.id), UserId(test_user.id))
        assert [n.title for n in notes] == ["Apple", "banana", "cherry"]

    async def test_find_by_book_filters_by_kind(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_book: models.Book,
        test_user: models.User,
    ) -> None:
        matching = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), kind=NoteKind.CHARACTER
        )
        empty = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), kind=NoteKind.TERM
        )
        assert len(matching) == 1
        assert empty == []

    async def test_find_by_book_filters_by_chapter(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_book: models.Book,
        test_chapter: models.Chapter,
        test_user: models.User,
    ) -> None:
        matching = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), chapter_id=ChapterId(test_chapter.id)
        )
        empty = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), chapter_id=ChapterId(99999)
        )
        assert len(matching) == 1
        assert empty == []

    async def test_find_by_book_filters_by_highlight(
        self,
        note_repository: NoteRepository,
        test_user: models.User,
        test_book: models.Book,
        test_highlight: models.Highlight,
    ) -> None:
        note = Note.create(
            user_id=UserId(test_user.id),
            title="Stoicism",
            book_ids=[test_book.id],
            highlight_ids=[test_highlight.id],
        )
        saved = await note_repository.save(note)

        matching = await note_repository.find_by_book(
            BookId(test_book.id),
            UserId(test_user.id),
            highlight_id=HighlightId(test_highlight.id),
        )
        empty = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), highlight_id=HighlightId(99999)
        )
        assert [n.id for n in matching] == [saved.id]
        assert empty == []

    async def test_find_by_book_filters_by_highlight_tag(
        self,
        note_repository: NoteRepository,
        test_user: models.User,
        test_book: models.Book,
        test_highlight_tag: models.HighlightTag,
    ) -> None:
        note = Note.create(
            user_id=UserId(test_user.id),
            title="Stoicism",
            book_ids=[test_book.id],
            highlight_tag_ids=[test_highlight_tag.id],
        )
        saved = await note_repository.save(note)

        matching = await note_repository.find_by_book(
            BookId(test_book.id),
            UserId(test_user.id),
            highlight_tag_id=HighlightTagId(test_highlight_tag.id),
        )
        empty = await note_repository.find_by_book(
            BookId(test_book.id),
            UserId(test_user.id),
            highlight_tag_id=HighlightTagId(99999),
        )
        assert [n.id for n in matching] == [saved.id]
        assert empty == []


class TestNoteRepositoryDelete:
    async def test_delete(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_user: models.User,
        db_session: AsyncSession,
    ) -> None:
        deleted = await note_repository.delete(saved_note.id, UserId(test_user.id))
        assert deleted is True
        result = await db_session.execute(select(models.Note).filter_by(id=saved_note.id.value))
        assert result.scalar_one_or_none() is None

    async def test_delete_wrong_user_returns_false(
        self, note_repository: NoteRepository, saved_note: Note
    ) -> None:
        deleted = await note_repository.delete(saved_note.id, UserId(999))
        assert deleted is False

    async def test_delete_missing_returns_false(
        self, note_repository: NoteRepository, test_user: models.User
    ) -> None:
        deleted = await note_repository.delete(NoteId(99999), UserId(test_user.id))
        assert deleted is False
