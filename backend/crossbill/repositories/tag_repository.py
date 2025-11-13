"""Tag repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from crossbill import models

logger = logging.getLogger(__name__)


class TagRepository:
    """Repository for Tag database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_name(self, name: str) -> models.Tag | None:
        """Get a tag by its name."""
        stmt = select(models.Tag).where(models.Tag.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, tag_id: int) -> models.Tag | None:
        """Get a tag by its ID."""
        stmt = select(models.Tag).where(models.Tag.id == tag_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, name: str) -> models.Tag:
        """Create a new tag."""
        tag = models.Tag(name=name)
        self.db.add(tag)
        self.db.flush()
        self.db.refresh(tag)
        logger.info(f"Created tag: {tag.name} (id={tag.id})")
        return tag

    def get_or_create(self, name: str) -> models.Tag:
        """Get existing tag by name or create a new one."""
        tag = self.get_by_name(name)
        if tag:
            return tag
        return self.create(name)

    def get_all(self) -> list[models.Tag]:
        """Get all tags."""
        stmt = select(models.Tag).order_by(models.Tag.name)
        return list(self.db.execute(stmt).scalars().all())
