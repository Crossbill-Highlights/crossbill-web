"""Mapper for User ORM ↔ Domain conversion."""

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.infrastructure.common.mappers import orm_id
from src.infrastructure.identity.orm.user_model import User as UserORM


class UserMapper:
    """Mapper for User ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: UserORM) -> User:
        """Convert ORM model to domain entity."""
        return User.create_with_id(
            id=UserId(orm_model.id),
            email=orm_model.email,
            hashed_password=orm_model.hashed_password,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    def to_orm(self, domain_entity: User, orm_model: UserORM | None = None) -> UserORM:
        """Convert domain entity to ORM model."""
        if orm_model is None:
            orm_model = UserORM(
                id=orm_id(domain_entity.id),
            )
        orm_model.email = domain_entity.email
        orm_model.hashed_password = domain_entity.hashed_password
        return orm_model
