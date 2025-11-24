"""User repository for database operations."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from src import models

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_by_id(self, user_id: int) -> models.User | None:
        """Get a user by its ID."""
        stmt = select(models.User).where(models.User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> models.User | None:
        """Get a user by its name."""
        stmt = select(models.User).where(models.User.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, name: str) -> models.User:
        """Create a new user."""
        user = models.User(name=name)
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        logger.info(f"Created user: {user.name} (id={user.id})")
        return user

    def create_with_password(self, name: str, hashed_password: str) -> models.User:
        """Create a new user with a hashed password."""
        user = models.User(name=name, hashed_password=hashed_password)
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        logger.info(f"Created user with password: {user.name} (id={user.id})")
        return user

    def get_or_create(self, name: str) -> models.User:
        """Get existing user by name or create a new one."""
        user = self.get_by_name(name)
        if user:
            return user
        return self.create(name)

    def get_all(self) -> list[models.User]:
        """Get all users."""
        stmt = select(models.User).order_by(models.User.name)
        return list(self.db.execute(stmt).scalars().all())
