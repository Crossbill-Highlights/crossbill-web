"""BookReflection entity for a reader's analytical-reading answers about a book."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.common.aggregate_root import AggregateRoot
from src.domain.common.value_objects import BookId, BookReflectionId, UserId


@dataclass
class BookReflection(AggregateRoot[BookReflectionId]):
    """A single reflection per book: the four analytical-reading answers.

    ``note_ids`` link the term/concept notes the reader used to come to terms
    with the author (the Q2 answer). The four answer fields are free text and
    may all be empty (an untouched reflection is still valid).
    """

    id: BookReflectionId
    user_id: UserId
    book_id: BookId
    what_is_it_about: str = ""
    what_does_it_say: str = ""
    do_i_agree: str = ""
    so_what: str = ""
    note_ids: list[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_answers(
        self,
        what_is_it_about: str,
        what_does_it_say: str,
        do_i_agree: str,
        so_what: str,
    ) -> None:
        """Replace all four answer fields (the frontend always sends the full set)."""
        self.what_is_it_about = what_is_it_about
        self.what_does_it_say = what_does_it_say
        self.do_i_agree = do_i_agree
        self.so_what = so_what

    def replace_note_links(self, note_ids: list[int]) -> None:
        """Replace the linked-note set."""
        self.note_ids = list(note_ids)

    @classmethod
    def create(
        cls,
        user_id: UserId,
        book_id: BookId,
        what_is_it_about: str = "",
        what_does_it_say: str = "",
        do_i_agree: str = "",
        so_what: str = "",
        note_ids: list[int] | None = None,
    ) -> BookReflection:
        """Create a new reflection (ID will be 0 until persisted)."""
        return cls(
            id=BookReflectionId.generate(),
            user_id=user_id,
            book_id=book_id,
            what_is_it_about=what_is_it_about,
            what_does_it_say=what_does_it_say,
            do_i_agree=do_i_agree,
            so_what=so_what,
            note_ids=list(note_ids or []),
        )

    @classmethod
    def create_with_id(
        cls,
        id: BookReflectionId,
        user_id: UserId,
        book_id: BookId,
        what_is_it_about: str,
        what_does_it_say: str,
        do_i_agree: str,
        so_what: str,
        note_ids: list[int],
        created_at: datetime,
        updated_at: datetime,
    ) -> BookReflection:
        """Reconstitute a reflection from persistence."""
        return cls(
            id=id,
            user_id=user_id,
            book_id=book_id,
            what_is_it_about=what_is_it_about,
            what_does_it_say=what_does_it_say,
            do_i_agree=do_i_agree,
            so_what=so_what,
            note_ids=note_ids,
            created_at=created_at,
            updated_at=updated_at,
        )
