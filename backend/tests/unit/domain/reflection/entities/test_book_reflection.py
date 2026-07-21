"""Tests for BookReflection domain entity."""

from src.domain.common.value_objects import BookId, UserId
from src.domain.reflection.entities.book_reflection import BookReflection


def make_reflection(**overrides: object) -> BookReflection:
    defaults: dict[str, object] = {
        "user_id": UserId(1),
        "book_id": BookId(7),
    }
    defaults.update(overrides)
    return BookReflection.create(**defaults)  # type: ignore[arg-type]


class TestBookReflectionCreate:
    def test_create_defaults_to_no_answer_notes(self) -> None:
        reflection = make_reflection()
        assert reflection.id.value == 0
        assert reflection.user_id == UserId(1)
        assert reflection.book_id == BookId(7)
        assert reflection.what_is_it_about_note_id is None
        assert reflection.what_does_it_say_note_id is None
        assert reflection.do_i_agree_note_id is None
        assert reflection.so_what_note_id is None
        assert reflection.note_ids == []

    def test_create_with_values(self) -> None:
        reflection = make_reflection(
            what_is_it_about_note_id=11,
            so_what_note_id=44,
            note_ids=[1, 2],
        )
        assert reflection.what_is_it_about_note_id == 11
        assert reflection.so_what_note_id == 44
        assert reflection.note_ids == [1, 2]


class TestBookReflectionCommands:
    def test_update_answer_notes_replaces_all_fields(self) -> None:
        reflection = make_reflection(what_is_it_about_note_id=1)
        reflection.update_answer_notes(
            what_is_it_about_note_id=10,
            what_does_it_say_note_id=20,
            do_i_agree_note_id=30,
            so_what_note_id=40,
        )
        assert reflection.what_is_it_about_note_id == 10
        assert reflection.what_does_it_say_note_id == 20
        assert reflection.do_i_agree_note_id == 30
        assert reflection.so_what_note_id == 40

    def test_update_answer_notes_can_clear_to_none(self) -> None:
        reflection = make_reflection(what_is_it_about_note_id=10)
        reflection.update_answer_notes(
            what_is_it_about_note_id=None,
            what_does_it_say_note_id=None,
            do_i_agree_note_id=None,
            so_what_note_id=None,
        )
        assert reflection.what_is_it_about_note_id is None

    def test_replace_note_links_copies_list(self) -> None:
        reflection = make_reflection()
        source = [3, 4]
        reflection.replace_note_links(source)
        source.append(5)
        assert reflection.note_ids == [3, 4]
