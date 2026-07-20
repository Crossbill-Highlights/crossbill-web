"""SQLAlchemy ORM model for bookmarks."""

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.infrastructure.library.orm.book_model import Book
    from src.infrastructure.reading.orm.highlight_model import Highlight


class Bookmark(Base):
    """Bookmark model for tracking reading progress within a book."""

    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    highlight_id: Mapped[int] = mapped_column(
        ForeignKey("highlights.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    book: Mapped["Book"] = relationship(back_populates="bookmarks")
    highlight: Mapped["Highlight"] = relationship(back_populates="bookmarks")

    def __repr__(self) -> str:
        """String representation of Bookmark."""
        return f"<Bookmark(id={self.id}, book_id={self.book_id}, highlight_id={self.highlight_id})>"
