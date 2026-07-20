"""Shared helpers for ORM ↔ domain mappers."""

from uuid import UUID

from src.domain.common.entity import EntityId


def orm_id(entity_id: EntityId) -> int | UUID | None:
    """Map a domain ``EntityId`` to an ORM primary key.

    New entities carry the integer sentinel ``0`` until the database assigns a
    real id; returning ``None`` in that case lets the ORM generate the key on
    insert. UUID-based ids are always passed through unchanged.
    """
    value = entity_id.value
    if isinstance(value, int) and value == 0:
        return None
    return value
