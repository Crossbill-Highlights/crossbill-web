"""Repository for User domain entities."""

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import EmailAlreadyExistsError
from src.infrastructure.identity.mappers.user_mapper import UserMapper
from src.models import User as UserORM

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User domain entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.mapper = UserMapper()

    async def find_by_id(self, user_id: UserId) -> User | None:
        """
        Find a user by ID.

        Args:
            user_id: The user ID

        Returns:
            User entity if found, None otherwise
        """
        stmt = select(UserORM).where(UserORM.id == user_id.value)
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    async def find_by_email(self, email: str) -> User | None:
        """
        Find a user by email.

        Args:
            email: The user's email address

        Returns:
            User entity if found, None otherwise
        """
        stmt = select(UserORM).where(UserORM.email == email)
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    async def email_exists(self, email: str) -> bool:
        """
        Check if an email is already registered.

        Args:
            email: The email address to check

        Returns:
            True if email exists, False otherwise
        """
        stmt = select(UserORM.id).where(UserORM.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def save(self, user: User) -> User:
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
                await self.db.commit()
                await self.db.refresh(orm_model)
                logger.info(f"Created user with email: {user.email} (id={orm_model.id})")
                return self.mapper.to_domain(orm_model)
            except IntegrityError as e:
                await self.db.rollback()
                # Check if it's a unique constraint violation on email
                if "email" in str(e.orig):
                    raise EmailAlreadyExistsError(user.email) from e
                raise
        else:
            # Update existing user
            stmt = select(UserORM).where(UserORM.id == user.id.value)
            result = await self.db.execute(stmt)
            orm_model = result.scalar_one_or_none()
            if not orm_model:
                raise ValueError(f"User with id {user.id.value} not found")

            orm_model = self.mapper.to_orm(user, orm_model)
            await self.db.commit()
            await self.db.refresh(orm_model)
            logger.info(f"Updated user {user.id.value}")
            return self.mapper.to_domain(orm_model)
