"""Repository for RefreshToken domain entities."""

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from src.infrastructure.identity.mappers.refresh_token_mapper import RefreshTokenMapper
from src.models import RefreshTokenRecord


class RefreshTokenRepository:
    """Repository for server-side refresh token records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.mapper = RefreshTokenMapper()

    async def save(self, token: RefreshToken) -> RefreshToken:
        orm_model = self.mapper.to_orm(token)
        self.db.add(orm_model)
        await self.db.commit()
        await self.db.refresh(orm_model)
        return self.mapper.to_domain(orm_model)

    async def find_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshTokenRecord).where(RefreshTokenRecord.token_hash == token_hash)
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    async def revoke_family(self, family_id: str) -> None:
        """Revoke all non-revoked tokens in a family."""
        stmt = (
            update(RefreshTokenRecord)
            .where(
                RefreshTokenRecord.family_id == family_id,
                RefreshTokenRecord.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def revoke_all_for_user(self, user_id: UserId) -> None:
        """Revoke all non-revoked tokens for a user."""
        stmt = (
            update(RefreshTokenRecord)
            .where(
                RefreshTokenRecord.user_id == user_id.value,
                RefreshTokenRecord.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def delete_expired(self) -> int:
        """Delete expired tokens. Returns count of deleted rows."""
        stmt = delete(RefreshTokenRecord).where(RefreshTokenRecord.expires_at < datetime.now(UTC))
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount  # type: ignore[return-value]
