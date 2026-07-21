"""Association table linking book reflections to their notes."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, func

from src.database import Base

book_reflection_notes = Table(
    "book_reflection_notes",
    Base.metadata,
    Column(
        "book_reflection_id",
        Integer,
        ForeignKey("book_reflections.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "note_id",
        Integer,
        ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)
