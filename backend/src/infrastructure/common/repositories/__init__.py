"""Shared repository infrastructure."""

from src.infrastructure.common.repositories.base_repository import (
    BaseRepository,
    EntityMapper,
)

__all__ = ["BaseRepository", "EntityMapper"]
