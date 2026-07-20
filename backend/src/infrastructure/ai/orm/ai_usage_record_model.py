"""SQLAlchemy ORM model for AI usage tracking."""

from datetime import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.infrastructure.identity.orm.user_model import User


class AIUsageRecord(Base):
    """ORM model for AI usage tracking."""

    __tablename__ = "ai_usage_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(nullable=False)
    output_tokens: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[dt] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_ai_usage_records_entity", "entity_type", "entity_id"),)

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<AIUsageRecord(id={self.id}, task_type={self.task_type}, entity_type={self.entity_type})>"
