"""SQLAlchemy ORM model for highlight styles."""

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.infrastructure.identity.orm.user_model import User
    from src.infrastructure.library.orm.book_model import Book
    from src.infrastructure.reading.orm.highlight_model import Highlight


class HighlightStyle(Base):
    """HighlightStyle model for storing highlight style labels and colors."""

    __tablename__ = "highlight_styles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    book_id: Mapped[int | None] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=True
    )
    device_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ui_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="highlight_styles")
    book: Mapped["Book | None"] = relationship(back_populates="highlight_styles")
    highlights: Mapped[list["Highlight"]] = relationship(back_populates="highlight_style_rel")

    def __repr__(self) -> str:
        """String representation of HighlightStyle."""
        return (
            f"<HighlightStyle(id={self.id}, user_id={self.user_id}, "
            f"device_color='{self.device_color}', device_style='{self.device_style}')>"
        )
