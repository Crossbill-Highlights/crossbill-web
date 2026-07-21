"""BookReflection entity for a reader's analytical-reading answers about a book."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.common.aggregate_root import AggregateRoot
from src.domain.common.value_objects import BookId, BookReflectionId, UserId


@dataclass
class BookReflection(AggregateRoot[BookReflectionId]):
    """A single reflection per book: the four analytical-reading answers.

    Each answer is backed by a full :class:`Note` (markdown, links, flashcards).
    The four ``*_note_id`` fields reference that answer note, or are ``None`` when
    the question is still unanswered. ``note_ids`` link the term/concept notes the
    reader used to come to terms with the author (the Q2 side list).
    """

    id: BookReflectionId
    user_id: UserId
    book_id: BookId
    what_is_it_about_note_id: int | None = None
    what_does_it_say_note_id: int | None = None
    do_i_agree_note_id: int | None = None
    so_what_note_id: int | None = None
    note_ids: list[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_answer_notes(
        self,
        what_is_it_about_note_id: int | None,
        what_does_it_say_note_id: int | None,
        do_i_agree_note_id: int | None,
        so_what_note_id: int | None,
    ) -> None:
        """Replace all four answer-note references (the frontend sends the full set)."""
        self.what_is_it_about_note_id = what_is_it_about_note_id
        self.what_does_it_say_note_id = what_does_it_say_note_id
        self.do_i_agree_note_id = do_i_agree_note_id
        self.so_what_note_id = so_what_note_id

    def replace_note_links(self, note_ids: list[int]) -> None:
        """Replace the linked-note set."""
        self.note_ids = list(note_ids)

    @classmethod
    def create(
        cls,
        user_id: UserId,
        book_id: BookId,
        what_is_it_about_note_id: int | None = None,
        what_does_it_say_note_id: int | None = None,
        do_i_agree_note_id: int | None = None,
        so_what_note_id: int | None = None,
        note_ids: list[int] | None = None,
    ) -> BookReflection:
        """Create a new reflection (ID will be 0 until persisted)."""
        return cls(
            id=BookReflectionId.generate(),
            user_id=user_id,
            book_id=book_id,
            what_is_it_about_note_id=what_is_it_about_note_id,
            what_does_it_say_note_id=what_does_it_say_note_id,
            do_i_agree_note_id=do_i_agree_note_id,
            so_what_note_id=so_what_note_id,
            note_ids=list(note_ids or []),
        )

    @classmethod
    def create_with_id(
        cls,
        id: BookReflectionId,
        user_id: UserId,
        book_id: BookId,
        what_is_it_about_note_id: int | None,
        what_does_it_say_note_id: int | None,
        do_i_agree_note_id: int | None,
        so_what_note_id: int | None,
        note_ids: list[int],
        created_at: datetime,
        updated_at: datetime,
    ) -> BookReflection:
        """Reconstitute a reflection from persistence."""
        return cls(
            id=id,
            user_id=user_id,
            book_id=book_id,
            what_is_it_about_note_id=what_is_it_about_note_id,
            what_does_it_say_note_id=what_does_it_say_note_id,
            do_i_agree_note_id=do_i_agree_note_id,
            so_what_note_id=so_what_note_id,
            note_ids=note_ids,
            created_at=created_at,
            updated_at=updated_at,
        )
