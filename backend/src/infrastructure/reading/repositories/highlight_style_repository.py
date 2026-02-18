"""Repository for HighlightStyle persistence."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domain.common.value_objects import BookId, HighlightStyleId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.infrastructure.reading.mappers.highlight_style_mapper import HighlightStyleMapper
from src.models import Highlight as HighlightORM
from src.models import HighlightStyle as HighlightStyleORM


class HighlightStyleRepository:
    """SQLAlchemy implementation of HighlightStyle repository."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = HighlightStyleMapper()

    def find_by_id(
        self, style_id: HighlightStyleId, user_id: UserId
    ) -> HighlightStyle | None:
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.id == style_id.value,
            HighlightStyleORM.user_id == user_id.value,
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm) if orm else None

    def find_or_create(
        self,
        user_id: UserId,
        book_id: BookId,
        device_color: str | None,
        device_style: str | None,
    ) -> HighlightStyle:
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.user_id == user_id.value,
            HighlightStyleORM.book_id == book_id.value,
            HighlightStyleORM.device_color == device_color,
            HighlightStyleORM.device_style == device_style,
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        if orm:
            return self.mapper.to_domain(orm)

        style = HighlightStyle.create(
            user_id=user_id,
            book_id=book_id,
            device_color=device_color,
            device_style=device_style,
        )
        orm = self.mapper.to_orm(style)
        self.db.add(orm)
        self.db.flush()
        return self.mapper.to_domain(orm)

    def find_by_book(
        self, book_id: BookId, user_id: UserId
    ) -> list[HighlightStyle]:
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.user_id == user_id.value,
            HighlightStyleORM.book_id == book_id.value,
        )
        orms = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orms]

    def find_global(self, user_id: UserId) -> list[HighlightStyle]:
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.user_id == user_id.value,
            HighlightStyleORM.book_id.is_(None),
        )
        orms = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orms]

    def find_for_resolution(
        self, user_id: UserId, book_id: BookId
    ) -> list[HighlightStyle]:
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.user_id == user_id.value,
            (HighlightStyleORM.book_id == book_id.value)
            | (HighlightStyleORM.book_id.is_(None)),
        )
        orms = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orms]

    def save(self, style: HighlightStyle) -> HighlightStyle:
        if style.id.value == 0:
            orm = self.mapper.to_orm(style)
            self.db.add(orm)
            self.db.flush()
            return self.mapper.to_domain(orm)

        existing = self.db.execute(
            select(HighlightStyleORM).where(
                HighlightStyleORM.id == style.id.value
            )
        ).scalar_one_or_none()
        if existing:
            self.mapper.to_orm(style, existing)
            self.db.flush()
            return self.mapper.to_domain(existing)

        orm = self.mapper.to_orm(style)
        self.db.add(orm)
        self.db.flush()
        return self.mapper.to_domain(orm)

    def count_highlights_by_style(
        self, style_id: HighlightStyleId
    ) -> int:
        stmt = select(func.count()).select_from(HighlightORM).where(
            HighlightORM.highlight_style_id == style_id.value,
            HighlightORM.deleted_at.is_(None),
        )
        result = self.db.execute(stmt).scalar()
        return result or 0
