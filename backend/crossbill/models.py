"""Database models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crossbill.database import Base


class Book(Base):
    """Book model for storing book metadata."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str | None] = mapped_column(String(500), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cover: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    highlights: Mapped[list["Highlight"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Book."""
        return f"<Book(id={self.id}, title='{self.title}')>"


class Chapter(Base):
    """Chapter model for storing unique chapters within a book."""

    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    book: Mapped["Book"] = relationship(back_populates="chapters")
    highlights: Mapped[list["Highlight"]] = relationship(back_populates="chapter")

    # Unique constraint: chapters are unique within a book
    __table_args__ = (UniqueConstraint("book_id", "name", name="uq_chapter_per_book"),)

    def __repr__(self) -> str:
        """String representation of Chapter."""
        return f"<Chapter(id={self.id}, name='{self.name}', book_id={self.book_id})>"


class Highlight(Base):
    """Highlight model for storing KOReader highlights."""

    __tablename__ = "highlights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chapter_id: Mapped[int | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"), index=True, nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int | None] = mapped_column(nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    datetime: Mapped[str] = mapped_column(String(50), nullable=False)  # KOReader datetime string
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Relationships
    book: Mapped["Book"] = relationship(back_populates="highlights")
    chapter: Mapped["Chapter | None"] = relationship(back_populates="highlights")

    # Unique constraint for deduplication: same text at same time in same book
    __table_args__ = (UniqueConstraint("book_id", "text", "datetime", name="uq_highlight_dedup"),)

    def __repr__(self) -> str:
        """String representation of Highlight."""
        return f"<Highlight(id={self.id}, text='{self.text[:50]}...', book_id={self.book_id})>"
