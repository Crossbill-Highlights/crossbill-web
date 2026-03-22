"""Mapper for RefreshToken ORM <-> Domain conversion."""

from src.domain.common.value_objects.ids import RefreshTokenId, UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from src.models import RefreshTokenRecord


class RefreshTokenMapper:
    """Mapper for RefreshToken ORM <-> Domain conversion."""

    def to_domain(self, orm_model: RefreshTokenRecord) -> RefreshToken:
        return RefreshToken(
            id=RefreshTokenId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            token_hash=orm_model.token_hash,
            family_id=orm_model.family_id,
            expires_at=orm_model.expires_at,
            revoked_at=orm_model.revoked_at,
            created_at=orm_model.created_at,
        )

    def to_orm(self, entity: RefreshToken) -> RefreshTokenRecord:
        return RefreshTokenRecord(
            id=entity.id.value if entity.id.value != 0 else None,
            user_id=entity.user_id.value,
            token_hash=entity.token_hash,
            family_id=entity.family_id,
            expires_at=entity.expires_at,
            revoked_at=entity.revoked_at,
        )
