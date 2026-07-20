"""SQLAlchemy ORM model for AI chat sessions."""

from datetime import datetime as dt
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from src.database import Base

if TYPE_CHECKING:
    from src.infrastructure.identity.orm.user_model import User
    from src.infrastructure.library.orm.chapter_model import Chapter


class AIChatSession(Base):
    """ORM model for AI chat sessions (quiz, discussion, etc.)."""

    __tablename__ = "ai_chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship()
    chapter: Mapped["Chapter"] = relationship()

    def __repr__(self) -> str:
        return (
            f"<AIChatSession(id={self.id}, type={self.session_type}, chapter_id={self.chapter_id})>"
        )
