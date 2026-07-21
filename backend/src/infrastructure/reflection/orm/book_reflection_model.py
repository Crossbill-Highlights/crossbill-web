"""SQLAlchemy ORM model for book reflections."""

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.infrastructure.reflection.orm.associations import book_reflection_notes

if TYPE_CHECKING:
    from src.infrastructure.notes.orm.note_model import Note


class BookReflection(Base):
    """A reader's analytical-reading answers about a book (one per book)."""

    __tablename__ = "book_reflections"
    __table_args__ = (UniqueConstraint("book_id", name="uq_book_reflections_book_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    what_is_it_about_note_id: Mapped[int | None] = mapped_column(
        ForeignKey("notes.id", ondelete="SET NULL"), nullable=True
    )
    what_does_it_say_note_id: Mapped[int | None] = mapped_column(
        ForeignKey("notes.id", ondelete="SET NULL"), nullable=True
    )
    do_i_agree_note_id: Mapped[int | None] = mapped_column(
        ForeignKey("notes.id", ondelete="SET NULL"), nullable=True
    )
    so_what_note_id: Mapped[int | None] = mapped_column(
        ForeignKey("notes.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship (one-directional; reflections are always queried from this side)
    notes: Mapped[list["Note"]] = relationship(secondary=book_reflection_notes, lazy="selectin")

    def __repr__(self) -> str:
        """String representation of BookReflection."""
        return f"<BookReflection(id={self.id}, book_id={self.book_id})>"
