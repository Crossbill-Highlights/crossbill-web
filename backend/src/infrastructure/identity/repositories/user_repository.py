"""Repository for User domain entities."""

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import EmailAlreadyExistsError
from src.infrastructure.identity.mappers.user_mapper import UserMapper
from src.models import User as UserORM

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User domain entities."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = UserMapper()

    def find_by_id(self, user_id: UserId) -> User | None:
        """
        Find a user by ID.

        Args:
            user_id: The user ID

        Returns:
            User entity if found, None otherwise
        """
        stmt = select(UserORM).where(UserORM.id == user_id.value)
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def find_by_email(self, email: str) -> User | None:
        """
        Find a user by email.

        Args:
            email: The user's email address

        Returns:
            User entity if found, None otherwise
        """
        stmt = select(UserORM).where(UserORM.email == email)
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def email_exists(self, email: str) -> bool:
        """
        Check if an email is already registered.

        Args:
            email: The email address to check

        Returns:
            True if email exists, False otherwise
        """
        stmt = select(UserORM.id).where(UserORM.email == email)
        result = self.db.execute(stmt).scalar_one_or_none()
        return result is not None

    def save(self, user: User) -> User:
        """
        Save a user entity.

        Args:
            user: The user entity to save

        Returns:
            Saved user entity with database-generated values

        Raises:
            EmailAlreadyExistsError: If email is already registered (for new users)
        """
        if user.id.value == 0:
            # Create new user
            try:
                orm_model = self.mapper.to_orm(user)
                self.db.add(orm_model)
                self.db.commit()
                self.db.refresh(orm_model)
                logger.info(f"Created user with email: {user.email} (id={orm_model.id})")
                return self.mapper.to_domain(orm_model)
            except IntegrityError as e:
                self.db.rollback()
                # Check if it's a unique constraint violation on email
                if "email" in str(e.orig):
                    raise EmailAlreadyExistsError(user.email) from e
                raise
        else:
            # Update existing user
            stmt = select(UserORM).where(UserORM.id == user.id.value)
            orm_model = self.db.execute(stmt).scalar_one_or_none()
            if not orm_model:
                raise ValueError(f"User with id {user.id.value} not found")

            orm_model = self.mapper.to_orm(user, orm_model)
            self.db.commit()
            self.db.refresh(orm_model)
            logger.info(f"Updated user {user.id.value}")
            return self.mapper.to_domain(orm_model)
