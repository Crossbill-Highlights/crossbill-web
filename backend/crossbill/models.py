"""Database models."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crossbill.database import Base

# Association table for many-to-many relationship between books and tags
book_tags = Table(
    "book_tags",
    Base.metadata,
    Column(
        "book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)


# Association table for many-to-many relationship between highlights and highlight_tags
highlight_highlight_tags = Table(
    "highlight_highlight_tags",
    Base.metadata,
    Column(
        "highlight_id",
        Integer,
        ForeignKey("highlights.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "highlight_tag_id",
        Integer,
        ForeignKey("highlight_tags.id", ondelete="CASCADE"),
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
    tags: Mapped[list["Tag"]] = relationship(
        secondary=book_tags, back_populates="books", lazy="selectin"
    )
    highlight_tags: Mapped[list["HighlightTag"]] = relationship(
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
    chapter_number: Mapped[int | None] = mapped_column(nullable=True, index=True)
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
    text_search_vector: Mapped[str | None] = mapped_column(
        Text().with_variant(TSVECTOR, "postgresql"), nullable=True, index=True
    )

    # Relationships
    book: Mapped["Book"] = relationship(back_populates="highlights")
    chapter: Mapped["Chapter | None"] = relationship(back_populates="highlights")
    highlight_tags: Mapped[list["HighlightTag"]] = relationship(
        secondary=highlight_highlight_tags, back_populates="highlights", lazy="selectin"
    )

    # Unique constraint for deduplication: same text at same time in same book
    __table_args__ = (UniqueConstraint("book_id", "text", "datetime", name="uq_highlight_dedup"),)

    def __repr__(self) -> str:
        """String representation of Highlight."""
        return f"<Highlight(id={self.id}, text='{self.text[:50]}...', book_id={self.book_id})>"


class Tag(Base):
    """Tag model for categorizing books."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
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
    books: Mapped[list["Book"]] = relationship(
        secondary=book_tags, back_populates="tags", lazy="selectin"
    )

    def __repr__(self) -> str:
        """String representation of Tag."""
        return f"<Tag(id={self.id}, name='{self.name}')>"


class HighlightTag(Base):
    """HighlightTag model for categorizing highlights within a book."""

    __tablename__ = "highlight_tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
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
    book: Mapped["Book"] = relationship(back_populates="highlight_tags")
    highlights: Mapped[list["Highlight"]] = relationship(
        secondary=highlight_highlight_tags, back_populates="highlight_tags", lazy="selectin"
    )

    # Unique constraint: tag names are unique within a book
    __table_args__ = (UniqueConstraint("book_id", "name", name="uq_highlight_tag_book_name"),)

    def __repr__(self) -> str:
        """String representation of HighlightTag."""
        return f"<HighlightTag(id={self.id}, name='{self.name}', book_id={self.book_id})>"
