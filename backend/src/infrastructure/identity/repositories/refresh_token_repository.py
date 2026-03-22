"""Repository for RefreshToken domain entities."""

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from src.infrastructure.identity.mappers.refresh_token_mapper import RefreshTokenMapper
from src.models import RefreshToken as RefreshTokenORM


class RefreshTokenRepository:
    """Repository for RefreshToken domain entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.mapper = RefreshTokenMapper()

    async def find_by_jti(self, jti: str) -> RefreshToken | None:
        stmt = select(RefreshTokenORM).where(RefreshTokenORM.jti == jti)
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    async def save(self, token: RefreshToken) -> RefreshToken:
        if token.id.value == 0:
            # New token
            orm_model = self.mapper.to_orm(token)
            self.db.add(orm_model)
            await self.db.commit()
            await self.db.refresh(orm_model)
            return self.mapper.to_domain(orm_model)
        # Update existing (e.g., revoking)
        stmt = select(RefreshTokenORM).where(RefreshTokenORM.id == token.id.value)
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one()
        orm_model.revoked_at = token.revoked_at
        await self.db.commit()
        await self.db.refresh(orm_model)
        return self.mapper.to_domain(orm_model)

    async def revoke_family(self, family_id: str) -> None:
        stmt = (
            update(RefreshTokenORM)
            .where(
                RefreshTokenORM.family_id == family_id,
                RefreshTokenORM.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def delete_expired_for_user(self, user_id: UserId) -> None:
        stmt = delete(RefreshTokenORM).where(
            RefreshTokenORM.user_id == user_id.value,
            RefreshTokenORM.expires_at < datetime.now(UTC),
        )
        await self.db.execute(stmt)
        await self.db.commit()
