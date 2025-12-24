"""Tag repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from src import models

logger = logging.getLogger(__name__)


class TagRepository:
    """Repository for Tag database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_name(self, name: str, user_id: int) -> models.Tag | None:
        """Get a tag by its name for a specific user."""
        stmt = select(models.Tag).where(
            models.Tag.name == name,
            models.Tag.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, tag_id: int, user_id: int) -> models.Tag | None:
        """Get a tag by its ID for a specific user."""
        stmt = select(models.Tag).where(
            models.Tag.id == tag_id,
            models.Tag.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, name: str, user_id: int) -> models.Tag:
        """Create a new tag for a user."""
        tag = models.Tag(name=name, user_id=user_id)
        self.db.add(tag)
        self.db.flush()
        self.db.refresh(tag)
        logger.info(f"Created tag: {tag.name} (id={tag.id}, user_id={user_id})")
        return tag

    def get_or_create(self, name: str, user_id: int) -> models.Tag:
        """Get existing tag by name for user or create a new one."""
        tag = self.get_by_name(name, user_id)
        if tag:
            return tag
        return self.create(name, user_id)

    def get_all(self, user_id: int) -> list[models.Tag]:
        """Get all tags for a specific user."""
        stmt = select(models.Tag).where(models.Tag.user_id == user_id).order_by(models.Tag.name)
        return list(self.db.execute(stmt).scalars().all())

    def get_by_names(self, names: list[str], user_id: int) -> list[models.Tag]:
        """Get multiple tags by their names for a specific user in a single query."""
        if not names:
            return []
        stmt = select(models.Tag).where(
            models.Tag.name.in_(names),
            models.Tag.user_id == user_id,
        )
        return list(self.db.execute(stmt).scalars().all())

    def bulk_create(self, names: list[str], user_id: int) -> list[models.Tag]:
        """Create multiple tags in a single operation."""
        if not names:
            return []
        tags = [models.Tag(name=name, user_id=user_id) for name in names]
        self.db.add_all(tags)
        self.db.flush()
        for tag in tags:
            self.db.refresh(tag)
        logger.info(f"Bulk created {len(tags)} tags for user_id={user_id}")
        return tags

    def get_or_create_many(self, names: list[str], user_id: int) -> list[models.Tag]:
        """Get existing tags or create new ones for a list of names.

        Uses bulk operations to minimize database queries:
        1. Single query to fetch all existing tags by name
        2. Single bulk insert for new tags
        """
        if not names:
            return []

        # Normalize names (strip whitespace, filter empty)
        normalized = [name.strip() for name in names if name.strip()]
        if not normalized:
            return []

        # Single query to get all existing tags
        existing_tags = self.get_by_names(normalized, user_id)
        existing_names = {tag.name for tag in existing_tags}

        # Find names that need to be created
        new_names = [name for name in normalized if name not in existing_names]

        # Bulk create new tags
        new_tags = self.bulk_create(new_names, user_id) if new_names else []

        return existing_tags + new_tags
