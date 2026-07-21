"""Pydantic schemas for BookReflection API request/response validation."""

from pydantic import BaseModel, Field


class BookReflectionResponse(BaseModel):
    """Schema for a book reflection response.

    Each answer is a reference to the note holding that answer's markdown, or
    ``None`` when the question is unanswered. The frontend resolves the ids to
    note content from its cached notes-for-book query.
    """

    book_id: int
    what_is_it_about_note_id: int | None = None
    what_does_it_say_note_id: int | None = None
    do_i_agree_note_id: int | None = None
    so_what_note_id: int | None = None
    note_ids: list[int] = Field(default_factory=list)


class BookReflectionUpdateRequest(BaseModel):
    """Schema for upserting a book reflection (full replace)."""

    what_is_it_about_note_id: int | None = Field(None, description="Q1 answer note id")
    what_does_it_say_note_id: int | None = Field(None, description="Q2 answer note id")
    do_i_agree_note_id: int | None = Field(None, description="Q3 answer note id")
    so_what_note_id: int | None = Field(None, description="Q4 answer note id")
    note_ids: list[int] = Field(default_factory=list, description="Linked term/concept notes")
