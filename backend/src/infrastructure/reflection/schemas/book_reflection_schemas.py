"""Pydantic schemas for BookReflection API request/response validation."""

from pydantic import BaseModel, Field


class BookReflectionResponse(BaseModel):
    """Schema for a book reflection response."""

    book_id: int
    what_is_it_about: str
    what_does_it_say: str
    do_i_agree: str
    so_what: str
    note_ids: list[int] = Field(default_factory=list)


class BookReflectionUpdateRequest(BaseModel):
    """Schema for upserting a book reflection (full replace)."""

    what_is_it_about: str = Field("", description="Q1: what the whole book is about")
    what_does_it_say: str = Field("", description="Q2: what the book says in detail")
    do_i_agree: str = Field("", description="Q3: the reader's judgement of the book")
    so_what: str = Field("", description="Q4: what follows if the book is true")
    note_ids: list[int] = Field(default_factory=list, description="Linked term/concept notes")
