"""Generic repository base collapsing the common find/save/delete boilerplate.

Simple, single-table entity repositories share the same shape: look a row up by
id (scoped to the owner), persist via a create-vs-update sentinel on the domain
id, and delete by id (scoped to the owner). ``BaseRepository`` provides those
three operations plus ``find_by_ids`` so concrete repositories only implement the
queries that are genuinely bespoke.

Ownership scoping varies between tables — most carry a ``user_id`` column, but a
few enforce ownership through a relationship (e.g. bookmarks via their book).
The overridable ``_ownership_filter`` hook accommodates both.
"""

from typing import Any, Generic, Protocol, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.entity import EntityId
from src.domain.common.value_objects.ids import UserId


class _DomainEntity(Protocol):
    """A domain entity carrying a strongly-typed id."""

    @property
    def id(self) -> EntityId: ...


TDomain = TypeVar("TDomain", bound=_DomainEntity)
TOrm = TypeVar("TOrm")


class EntityMapper(Protocol[TDomain, TOrm]):
    """Bidirectional ORM <-> domain mapper used by :class:`BaseRepository`."""

    def to_domain(self, orm_model: TOrm, /) -> TDomain: ...

    def to_orm(self, domain_entity: TDomain, orm_model: TOrm | None = ..., /) -> TOrm: ...


class BaseRepository(Generic[TDomain, TOrm]):
    """Common CRUD for simple, single-table entity repositories."""

    def __init__(
        self,
        db: AsyncSession,
        orm_class: type[TOrm],
        mapper: EntityMapper[TDomain, TOrm],
    ) -> None:
        self.db = db
        self._orm_class: Any = orm_class
        self._mapper = mapper

    def _ownership_filter(self, stmt: Select[Any], user_id: UserId) -> Select[Any]:
        """Restrict a query to rows owned by ``user_id``.

        The default assumes the table has a ``user_id`` column. Repositories
        whose ownership is enforced through a relationship override this hook.
        """
        return stmt.where(self._orm_class.user_id == user_id.value)

    async def find_by_id(self, entity_id: EntityId, user_id: UserId) -> TDomain | None:
        """Load a single owned row by id, or ``None`` when absent."""
        stmt = self._ownership_filter(select(self._orm_class), user_id).where(
            self._orm_class.id == entity_id.value
        )
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return self._mapper.to_domain(orm_model) if orm_model is not None else None

    async def find_by_ids(self, entity_ids: list[int], user_id: UserId) -> list[TDomain]:
        """Load owned rows for the given ids (empty input yields an empty list)."""
        if not entity_ids:
            return []
        stmt = self._ownership_filter(select(self._orm_class), user_id).where(
            self._orm_class.id.in_(entity_ids)
        )
        result = await self.db.execute(stmt)
        return [self._mapper.to_domain(orm) for orm in result.scalars().all()]

    async def save(self, entity: TDomain, /) -> TDomain:
        """Insert a new entity (id sentinel ``0``) or update the existing row."""
        if entity.id.value == 0:
            orm_model = self._mapper.to_orm(entity)
            self.db.add(orm_model)
            await self.db.commit()
            await self.db.refresh(orm_model)
            return self._mapper.to_domain(orm_model)

        existing = await self.db.get(self._orm_class, entity.id.value)
        if existing is None:
            raise ValueError(f"{self._orm_class.__name__} {entity.id.value} not found")
        self._mapper.to_orm(entity, existing)
        await self.db.commit()
        await self.db.refresh(existing)
        return self._mapper.to_domain(existing)

    async def delete(self, entity_id: EntityId, user_id: UserId) -> bool:
        """Delete an owned row by id, returning whether a row was removed."""
        stmt = self._ownership_filter(select(self._orm_class), user_id).where(
            self._orm_class.id == entity_id.value
        )
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        if orm_model is None:
            return False
        await self.db.delete(orm_model)
        await self.db.commit()
        return True
