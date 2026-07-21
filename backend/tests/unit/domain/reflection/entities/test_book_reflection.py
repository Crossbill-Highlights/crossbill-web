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
    def test_create_defaults_to_empty_answers(self) -> None:
        reflection = make_reflection()
        assert reflection.id.value == 0
        assert reflection.user_id == UserId(1)
        assert reflection.book_id == BookId(7)
        assert reflection.what_is_it_about == ""
        assert reflection.what_does_it_say == ""
        assert reflection.do_i_agree == ""
        assert reflection.so_what == ""
        assert reflection.note_ids == []

    def test_create_with_values(self) -> None:
        reflection = make_reflection(
            what_is_it_about="About X",
            so_what="Therefore Y",
            note_ids=[1, 2],
        )
        assert reflection.what_is_it_about == "About X"
        assert reflection.so_what == "Therefore Y"
        assert reflection.note_ids == [1, 2]


class TestBookReflectionCommands:
    def test_update_answers_replaces_all_fields(self) -> None:
        reflection = make_reflection(what_is_it_about="old")
        reflection.update_answers(
            what_is_it_about="new about",
            what_does_it_say="new say",
            do_i_agree="new agree",
            so_what="new so",
        )
        assert reflection.what_is_it_about == "new about"
        assert reflection.what_does_it_say == "new say"
        assert reflection.do_i_agree == "new agree"
        assert reflection.so_what == "new so"

    def test_replace_note_links_copies_list(self) -> None:
        reflection = make_reflection()
        source = [3, 4]
        reflection.replace_note_links(source)
        source.append(5)
        assert reflection.note_ids == [3, 4]
