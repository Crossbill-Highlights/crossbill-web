"""Mapper for RefreshToken ORM <-> Domain conversion."""

from src.domain.common.value_objects.ids import RefreshTokenId, UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from src.models import RefreshToken as RefreshTokenORM


class RefreshTokenMapper:
    """Mapper for RefreshToken ORM <-> Domain conversion."""

    def to_domain(self, orm_model: RefreshTokenORM) -> RefreshToken:
        return RefreshToken.create_with_id(
            id=RefreshTokenId(orm_model.id),
            jti=orm_model.jti,
            user_id=UserId(orm_model.user_id),
            family_id=orm_model.family_id,
            revoked_at=orm_model.revoked_at,
            expires_at=orm_model.expires_at,
            created_at=orm_model.created_at,
        )

    def to_orm(self, domain_entity: RefreshToken) -> RefreshTokenORM:
        return RefreshTokenORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            jti=domain_entity.jti,
            user_id=domain_entity.user_id.value,
            family_id=domain_entity.family_id,
            revoked_at=domain_entity.revoked_at,
            expires_at=domain_entity.expires_at,
        )
