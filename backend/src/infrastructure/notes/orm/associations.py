"""Association tables for many-to-many relationships between notes and other entities."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, func

from src.database import Base

note_books = Table(
    "note_books",
    Base.metadata,
    Column(
        "note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)

note_chapters = Table(
    "note_chapters",
    Base.metadata,
    Column(
        "note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "chapter_id",
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
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

note_highlights = Table(
    "note_highlights",
    Base.metadata,
    Column(
        "note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "highlight_id",
        Integer,
        ForeignKey("highlights.id", ondelete="CASCADE"),
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

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column(
        "note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
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
