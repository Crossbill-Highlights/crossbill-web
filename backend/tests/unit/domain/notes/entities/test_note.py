"""Tests for Note domain entity."""

from typing import Any

import pytest

from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects import UserId
from src.domain.notes.entities.note import Note, NoteKind


def make_note(**overrides: object) -> Note:
    defaults: dict[str, Any] = {
        "user_id": UserId(1),
        "title": "Stoicism",
        "book_ids": [1],
    }
    defaults.update(overrides)
    return Note.create(**defaults)


class TestNoteInvariants:
    def test_create_sets_fields_and_strips_title(self) -> None:
        note = make_note(title="  Raskolnikov  ", body="Main character", kind=NoteKind.CHARACTER)
        assert note.title == "Raskolnikov"
        assert note.body == "Main character"
        assert note.kind == NoteKind.CHARACTER
        assert note.book_ids == [1]
        assert note.id.value == 0

    def test_empty_title_raises(self) -> None:
        with pytest.raises(DomainError, match="title"):
            make_note(title="")

    def test_whitespace_title_raises(self) -> None:
        with pytest.raises(DomainError, match="title"):
            make_note(title="   ")

    def test_no_linked_books_raises(self) -> None:
        with pytest.raises(DomainError, match="at least one book"):
            make_note(book_ids=[])


class TestNoteUpdate:
    def test_update_content(self) -> None:
        note = make_note()
        note.update_content(title="  New title ", body="New body", kind=NoteKind.TERM)
        assert note.title == "New title"
        assert note.body == "New body"
        assert note.kind == NoteKind.TERM

    def test_update_content_empty_title_raises(self) -> None:
        note = make_note()
        with pytest.raises(DomainError, match="title"):
            note.update_content(title="", body="x", kind=None)

    def test_replace_links(self) -> None:
        note = make_note(chapter_ids=[10], highlight_ids=[20])
        note.replace_links(book_ids=[1], chapter_ids=[11, 12], highlight_ids=[], tag_ids=[30])
        assert note.chapter_ids == [11, 12]
        assert note.highlight_ids == []
        assert note.tag_ids == [30]

    def test_replace_links_requires_book(self) -> None:
        note = make_note()
        with pytest.raises(DomainError, match="at least one book"):
            note.replace_links(book_ids=[], chapter_ids=[], highlight_ids=[], tag_ids=[])
