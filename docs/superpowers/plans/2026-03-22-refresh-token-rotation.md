# Refresh Token Rotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add server-side refresh token tracking with token family rotation and replay detection.

**Architecture:** New `RefreshToken` domain entity tracked in a `refresh_tokens` DB table. Each refresh token JWT gets a `jti` claim mapping to a DB row. Tokens are grouped into families (one per login session). On refresh, the old token is revoked and a new one issued in the same family. Replaying a revoked token revokes the entire family.

**Tech Stack:** Python, FastAPI, SQLAlchemy async, Alembic, PyJWT, dependency-injector, pytest

**Spec:** `docs/superpowers/specs/2026-03-22-refresh-token-rotation-design.md`

---

## File Structure

### New Files
| File | Responsibility |
|------|---------------|
| `backend/src/domain/identity/entities/refresh_token.py` | RefreshToken domain entity |
| `backend/src/application/identity/protocols/refresh_token_repository.py` | Repository protocol |
| `backend/src/application/identity/dtos.py` | `TokenPairWithMetadata` and `RefreshTokenClaims` application-layer DTOs |
| `backend/src/application/identity/use_cases/authentication/logout_use_case.py` | LogoutUseCase |
| `backend/src/infrastructure/identity/mappers/refresh_token_mapper.py` | ORM ↔ domain mapper |
| `backend/src/infrastructure/identity/repositories/refresh_token_repository.py` | Repository implementation |
| `backend/alembic/versions/048_create_refresh_tokens_table.py` | DB migration |
| `backend/tests/unit/domain/identity/__init__.py` | Test package init |
| `backend/tests/unit/domain/identity/entities/__init__.py` | Test package init |
| `backend/tests/unit/domain/identity/entities/test_refresh_token.py` | Domain entity tests |
| `backend/tests/unit/application/identity/__init__.py` | Test package init |
| `backend/tests/unit/application/identity/use_cases/__init__.py` | Test package init |
| `backend/tests/unit/application/identity/use_cases/authentication/__init__.py` | Test package init |
| `backend/tests/unit/application/identity/use_cases/authentication/test_refresh_access_token_use_case.py` | Refresh rotation use case tests |
| `backend/tests/unit/application/identity/use_cases/test_register_user_use_case.py` | Registration token persistence tests |
| `backend/tests/unit/application/identity/use_cases/authentication/test_authenticate_user_use_case.py` | Login token persistence tests |
| `backend/tests/unit/application/identity/use_cases/authentication/test_logout_use_case.py` | Logout use case tests |

### Modified Files
| File | Change |
|------|--------|
| `backend/src/domain/common/value_objects/ids.py` | Add `RefreshTokenId` |
| `backend/src/models.py` | Add `RefreshToken` ORM model, add relationship to `User` |
| `backend/src/application/identity/protocols/token_service.py` | Update protocol signatures to use new DTOs |
| `backend/src/infrastructure/identity/services/token_service.py` | Add `jti` claim, return `TokenPairWithMetadata`, return `RefreshTokenClaims` |
| `backend/src/infrastructure/identity/services/token_service_adapter.py` | Update adapter to match new protocol |
| `backend/src/application/identity/use_cases/authentication/authenticate_user_use_case.py` | Persist refresh token on login |
| `backend/src/application/identity/use_cases/register_user_use_case.py` | Persist refresh token on registration |
| `backend/src/application/identity/use_cases/authentication/refresh_access_token_use_case.py` | Add rotation logic |
| `backend/src/infrastructure/identity/routers/auth.py` | Convert DTOs for response, wire LogoutUseCase |
| `backend/src/containers/shared.py` | Add `refresh_token_repository` |
| `backend/src/containers/identity.py` | Wire new dependency into use cases |
| `backend/src/containers/root.py` | Pass `refresh_token_repository` to identity container |

---

## Task 1: Add `RefreshTokenId` Value Object

**Files:**
- Modify: `backend/src/domain/common/value_objects/ids.py:190` (append after last ID)

- [ ] **Step 1: Add RefreshTokenId to ids.py**

Append after `AIChatSessionId` (line 190):

```python
@dataclass(frozen=True)
class RefreshTokenId(EntityId):
    """Strongly-typed refresh token identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("RefreshTokenId must be non-negative")

    @classmethod
    def generate(cls) -> "RefreshTokenId":
        return cls(0)  # Database assigns real ID
```

- [ ] **Step 2: Verify with pyright**

Run: `cd backend && uv run pyright src/domain/common/value_objects/ids.py`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add backend/src/domain/common/value_objects/ids.py
git commit -m "feat: add RefreshTokenId value object"
```

---

## Task 2: Create `RefreshToken` Domain Entity

**Files:**
- Create: `backend/src/domain/identity/entities/refresh_token.py`
- Create: `backend/tests/unit/domain/identity/__init__.py`
- Create: `backend/tests/unit/domain/identity/entities/__init__.py`
- Create: `backend/tests/unit/domain/identity/entities/test_refresh_token.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/domain/identity/__init__.py` and `backend/tests/unit/domain/identity/entities/__init__.py` as empty files.

Create `backend/tests/unit/domain/identity/entities/test_refresh_token.py`:

```python
"""Tests for RefreshToken domain entity."""

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.common.value_objects.ids import RefreshTokenId, UserId
from src.domain.identity.entities.refresh_token import RefreshToken


def _create(**overrides):
    defaults = {
        "jti": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": UserId(1),
        "family_id": "660e8400-e29b-41d4-a716-446655440000",
        "expires_at": datetime.now(UTC) + timedelta(days=30),
    }
    defaults.update(overrides)
    return RefreshToken.create(**defaults)


class TestRefreshTokenCreate:
    def test_create_sets_fields(self) -> None:
        token = _create()
        assert token.id == RefreshTokenId(0)
        assert token.jti == "550e8400-e29b-41d4-a716-446655440000"
        assert token.user_id == UserId(1)
        assert token.family_id == "660e8400-e29b-41d4-a716-446655440000"
        assert token.revoked_at is None

    def test_create_with_id_reconstitutes(self) -> None:
        now = datetime.now(UTC)
        token = RefreshToken.create_with_id(
            id=RefreshTokenId(42),
            jti="abc",
            user_id=UserId(1),
            family_id="def",
            revoked_at=None,
            expires_at=now + timedelta(days=30),
            created_at=now,
        )
        assert token.id == RefreshTokenId(42)
        assert token.jti == "abc"
        assert token.created_at == now


class TestRefreshTokenRevoke:
    def test_revoke_sets_revoked_at(self) -> None:
        token = _create()
        assert token.revoked_at is None
        token.revoke()
        assert token.revoked_at is not None

    def test_is_revoked(self) -> None:
        token = _create()
        assert not token.is_revoked
        token.revoke()
        assert token.is_revoked

    def test_is_expired(self) -> None:
        token = _create(expires_at=datetime.now(UTC) - timedelta(hours=1))
        assert token.is_expired

    def test_is_not_expired(self) -> None:
        token = _create(expires_at=datetime.now(UTC) + timedelta(days=30))
        assert not token.is_expired
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/domain/identity/entities/test_refresh_token.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Create the RefreshToken entity**

Create `backend/src/domain/identity/entities/refresh_token.py`:

```python
"""RefreshToken entity for token rotation tracking."""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import RefreshTokenId, UserId


@dataclass
class RefreshToken(Entity[RefreshTokenId]):
    """
    Tracks a refresh token for rotation and replay detection.

    Each token belongs to a family (one per login session).
    When rotated, the old token is revoked and a new one is created
    in the same family. Replaying a revoked token revokes the entire family.
    """

    id: RefreshTokenId
    jti: str
    user_id: UserId
    family_id: str
    revoked_at: datetime | None
    expires_at: datetime
    created_at: datetime | None = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return self.expires_at < datetime.now(UTC)

    def revoke(self) -> None:
        self.revoked_at = datetime.now(UTC)

    @classmethod
    def create(
        cls,
        jti: str,
        user_id: UserId,
        family_id: str,
        expires_at: datetime,
    ) -> "RefreshToken":
        return cls(
            id=RefreshTokenId.generate(),
            jti=jti,
            user_id=user_id,
            family_id=family_id,
            revoked_at=None,
            expires_at=expires_at,
        )

    @classmethod
    def create_with_id(
        cls,
        id: RefreshTokenId,
        jti: str,
        user_id: UserId,
        family_id: str,
        revoked_at: datetime | None,
        expires_at: datetime,
        created_at: datetime,
    ) -> "RefreshToken":
        return cls(
            id=id,
            jti=jti,
            user_id=user_id,
            family_id=family_id,
            revoked_at=revoked_at,
            expires_at=expires_at,
            created_at=created_at,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/unit/domain/identity/entities/test_refresh_token.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run pyright**

Run: `cd backend && uv run pyright src/domain/identity/entities/refresh_token.py`
Expected: 0 errors

- [ ] **Step 6: Commit**

```bash
git add backend/src/domain/identity/entities/refresh_token.py backend/tests/unit/domain/identity/
git commit -m "feat: add RefreshToken domain entity with tests"
```

---

## Task 3: Create Application-Layer DTOs

**Files:**
- Create: `backend/src/application/identity/dtos.py`

- [ ] **Step 1: Create dtos.py**

```python
"""Application-layer DTOs for identity module."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RefreshTokenClaims:
    """Claims extracted from a verified refresh token JWT."""

    user_id: int
    jti: str


@dataclass(frozen=True)
class TokenPairWithMetadata:
    """Token pair with metadata needed for persistence."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    jti: str
    family_id: str
```

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/application/identity/dtos.py`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add backend/src/application/identity/dtos.py
git commit -m "feat: add application-layer DTOs for token rotation"
```

---

## Task 4: Create RefreshToken Repository Protocol

**Files:**
- Create: `backend/src/application/identity/protocols/refresh_token_repository.py`

- [ ] **Step 1: Create the protocol**

```python
"""Protocol for refresh token repository."""

from typing import Protocol

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.refresh_token import RefreshToken


class RefreshTokenRepositoryProtocol(Protocol):
    async def find_by_jti(self, jti: str) -> RefreshToken | None: ...

    async def save(self, token: RefreshToken) -> RefreshToken: ...

    async def revoke_family(self, family_id: str) -> None: ...

    async def delete_expired_for_user(self, user_id: UserId) -> None: ...
```

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/application/identity/protocols/refresh_token_repository.py`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add backend/src/application/identity/protocols/refresh_token_repository.py
git commit -m "feat: add RefreshTokenRepositoryProtocol"
```

---

## Task 5: Update Token Service Protocol and DTOs

**Files:**
- Modify: `backend/src/application/identity/protocols/token_service.py`

- [ ] **Step 1: Update the protocol**

Replace the entire contents of `backend/src/application/identity/protocols/token_service.py`:

```python
"""Protocol for token service."""

from typing import Protocol

from src.application.identity.dtos import RefreshTokenClaims, TokenPairWithMetadata


class TokenServiceProtocol(Protocol):
    def create_token_pair(self, user_id: int, family_id: str) -> TokenPairWithMetadata: ...

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims | None: ...
```

- [ ] **Step 2: Run pyright on protocol file**

Run: `cd backend && uv run pyright src/application/identity/protocols/token_service.py`
Expected: 0 errors

Note: Other files that import `TokenServiceProtocol` will now have type errors — this is expected and will be fixed in later tasks.

- [ ] **Step 3: Commit**

```bash
git add backend/src/application/identity/protocols/token_service.py
git commit -m "feat: update TokenServiceProtocol for token rotation"
```

---

## Task 6: Update Token Service Implementation and Adapter

**Files:**
- Modify: `backend/src/infrastructure/identity/services/token_service.py`
- Modify: `backend/src/infrastructure/identity/services/token_service_adapter.py`

- [ ] **Step 1: Update token_service.py**

Replace the entire contents of `backend/src/infrastructure/identity/services/token_service.py`:

```python
"""Token creation and verification service."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError
from pydantic import BaseModel

from src.application.identity.dtos import RefreshTokenClaims, TokenPairWithMetadata
from src.config import get_settings

settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY or SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


class TokenWithRefresh(BaseModel):
    """Pydantic response model for HTTP API responses."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


def create_access_token(user_id: int) -> str:
    """Create an access token for a user."""
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, jti: str) -> str:
    """Create a refresh token for a user with a jti claim."""
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh", "jti": jti}
    return jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> int | None:
    """Verify an access token and return the user_id if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Reject refresh tokens - they should only be used at the /refresh endpoint
        if payload.get("type") == "refresh":
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (InvalidTokenError, ValueError):
        return None


def verify_refresh_token(token: str) -> RefreshTokenClaims | None:
    """Verify a refresh token and return claims if valid."""
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        jti = payload.get("jti")
        if user_id is None or jti is None:
            return None
        return RefreshTokenClaims(user_id=int(user_id), jti=jti)
    except (InvalidTokenError, ValueError):
        return None


def create_token_pair(user_id: int, family_id: str) -> TokenPairWithMetadata:
    """Create a token pair (access + refresh) for a user."""
    jti = str(uuid.uuid4())
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id, jti)
    return TokenPairWithMetadata(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        jti=jti,
        family_id=family_id,
    )
```

- [ ] **Step 2: Update token_service_adapter.py**

Replace the entire contents of `backend/src/infrastructure/identity/services/token_service_adapter.py`:

```python
"""Adapter wrapping token service functions for DI."""

from src.application.identity.dtos import RefreshTokenClaims, TokenPairWithMetadata
from src.infrastructure.identity.services import token_service


class TokenServiceAdapter:
    """Adapter wrapping token service functions for DI."""

    def create_token_pair(self, user_id: int, family_id: str) -> TokenPairWithMetadata:
        return token_service.create_token_pair(user_id, family_id)

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims | None:
        return token_service.verify_refresh_token(token)
```

- [ ] **Step 3: Run pyright on both files**

Run: `cd backend && uv run pyright src/infrastructure/identity/services/token_service.py src/infrastructure/identity/services/token_service_adapter.py`
Expected: 0 errors

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/identity/services/token_service.py backend/src/infrastructure/identity/services/token_service_adapter.py
git commit -m "feat: add jti claim to refresh tokens, return TokenPairWithMetadata"
```

---

## Task 7: Add ORM Model and Migration

**Files:**
- Modify: `backend/src/models.py:137` (after User model)
- Create: `backend/alembic/versions/048_create_refresh_tokens_table.py`

- [ ] **Step 1: Add RefreshToken ORM model to models.py**

After the `User` class (after line 137 in `backend/src/models.py`), add:

```python
class RefreshToken(Base):
    """Refresh token for token rotation and replay detection."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jti: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    revoked_at: Mapped[dt | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[dt] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, jti='{self.jti}', user_id={self.user_id})>"
```

Also add a relationship to the `User` model. After the `reading_sessions` relationship (line 132), add:

```python
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
```

- [ ] **Step 2: Create migration**

Create `backend/alembic/versions/048_create_refresh_tokens_table.py`:

```python
"""create refresh tokens table

Revision ID: 048
Revises: 047
Create Date: 2026-03-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "048"
down_revision: str | Sequence[str] | None = "047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("family_id", sa.String(36), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(op.f("ix_refresh_tokens_id"), "refresh_tokens", ["id"])
    op.create_index(op.f("ix_refresh_tokens_jti"), "refresh_tokens", ["jti"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"])
    op.create_index(op.f("ix_refresh_tokens_family_id"), "refresh_tokens", ["family_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_family_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_jti"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
```

- [ ] **Step 3: Run pyright on models.py**

Run: `cd backend && uv run pyright src/models.py`
Expected: 0 errors

- [ ] **Step 4: Commit**

```bash
git add backend/src/models.py backend/alembic/versions/048_create_refresh_tokens_table.py
git commit -m "feat: add refresh_tokens table and ORM model"
```

---

## Task 8: Create RefreshToken Mapper and Repository

**Files:**
- Create: `backend/src/infrastructure/identity/mappers/refresh_token_mapper.py`
- Create: `backend/src/infrastructure/identity/repositories/refresh_token_repository.py`

- [ ] **Step 1: Create the mapper**

Create `backend/src/infrastructure/identity/mappers/refresh_token_mapper.py`:

```python
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
```

- [ ] **Step 2: Create the repository**

Create `backend/src/infrastructure/identity/repositories/refresh_token_repository.py`:

```python
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
        orm_model = self.mapper.to_orm(token)
        self.db.add(orm_model)
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
```

- [ ] **Step 3: Run pyright on both files**

Run: `cd backend && uv run pyright src/infrastructure/identity/mappers/refresh_token_mapper.py src/infrastructure/identity/repositories/refresh_token_repository.py`
Expected: 0 errors

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/identity/mappers/refresh_token_mapper.py backend/src/infrastructure/identity/repositories/refresh_token_repository.py
git commit -m "feat: add RefreshToken mapper and repository implementation"
```

---

## Task 9: Wire DI Container

**Files:**
- Modify: `backend/src/containers/shared.py:72` (after token_service)
- Modify: `backend/src/containers/identity.py`
- Modify: `backend/src/containers/root.py:22`

- [ ] **Step 1: Add refresh_token_repository to SharedContainer**

In `backend/src/containers/shared.py`, add import at top:

```python
from src.infrastructure.identity.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
```

After `token_service` (line 72), add:

```python
    refresh_token_repository = providers.Factory(RefreshTokenRepository, db=db)
```

- [ ] **Step 2: Add refresh_token_repository dependency to IdentityContainer**

After `token_service = providers.Dependency()` (line 21), add:

```python
    refresh_token_repository = providers.Dependency()
```

Update `authenticate_user_use_case` (lines 23-28) to include:

```python
    authenticate_user_use_case = providers.Factory(
        AuthenticateUserUseCase,
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service,
        refresh_token_repository=refresh_token_repository,
    )
```

Update `refresh_access_token_use_case` (lines 29-33) to include:

```python
    refresh_access_token_use_case = providers.Factory(
        RefreshAccessTokenUseCase,
        user_repository=user_repository,
        token_service=token_service,
        refresh_token_repository=refresh_token_repository,
    )
```

Update `register_user_use_case` (lines 38-43) to include:

```python
    register_user_use_case = providers.Factory(
        RegisterUserUseCase,
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service,
        refresh_token_repository=refresh_token_repository,
    )
```

Note: `LogoutUseCase` wiring will be added in Task 13 after the use case is created.

- [ ] **Step 3: Update RootContainer to pass refresh_token_repository**

In `backend/src/containers/root.py`, update the `identity` container (lines 18-23):

```python
    identity = providers.Container(
        IdentityContainer,
        user_repository=shared.user_repository,
        password_service=shared.password_service,
        token_service=shared.token_service,
        refresh_token_repository=shared.refresh_token_repository,
    )
```

- [ ] **Step 4: Run pyright on container files**

Run: `cd backend && uv run pyright src/containers/shared.py src/containers/identity.py src/containers/root.py`
Expected: 0 errors (or errors only from not-yet-updated use cases, which is expected)

- [ ] **Step 5: Commit**

```bash
git add backend/src/containers/shared.py backend/src/containers/identity.py backend/src/containers/root.py
git commit -m "feat: wire RefreshTokenRepository into DI containers"
```

---

## Task 10: Update AuthenticateUserUseCase

**Files:**
- Modify: `backend/src/application/identity/use_cases/authentication/authenticate_user_use_case.py`
- Create: `backend/tests/unit/application/identity/__init__.py`
- Create: `backend/tests/unit/application/identity/use_cases/__init__.py`
- Create: `backend/tests/unit/application/identity/use_cases/authentication/__init__.py`
- Create: `backend/tests/unit/application/identity/use_cases/authentication/test_authenticate_user_use_case.py`

- [ ] **Step 1: Write failing tests**

Create the `__init__.py` files (empty) for the test package hierarchy:
- `backend/tests/unit/application/identity/__init__.py`
- `backend/tests/unit/application/identity/use_cases/__init__.py`
- `backend/tests/unit/application/identity/use_cases/authentication/__init__.py`

Create `backend/tests/unit/application/identity/use_cases/authentication/test_authenticate_user_use_case.py`:

```python
"""Tests for AuthenticateUserUseCase with token rotation."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.identity.dtos import TokenPairWithMetadata
from src.application.identity.use_cases.authentication.authenticate_user_use_case import (
    AuthenticateUserUseCase,
)
from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError


def _make_user(user_id: int = 1) -> User:
    return User.create_with_id(
        id=UserId(user_id),
        email="test@example.com",
        hashed_password="hashed",
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )


def _make_token_pair() -> TokenPairWithMetadata:
    return TokenPairWithMetadata(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=900,
        jti="test-jti",
        family_id="test-family",
    )


class TestAuthenticateUserUseCase:
    @pytest.fixture
    def user_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def password_service(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def token_service(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def refresh_token_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def use_case(
        self, user_repository, password_service, token_service, refresh_token_repository
    ) -> AuthenticateUserUseCase:
        return AuthenticateUserUseCase(
            user_repository=user_repository,
            password_service=password_service,
            token_service=token_service,
            refresh_token_repository=refresh_token_repository,
        )

    async def test_authenticate_persists_refresh_token(
        self, use_case, user_repository, password_service, token_service, refresh_token_repository
    ) -> None:
        user = _make_user()
        user_repository.find_by_email.return_value = user
        password_service.verify_password.return_value = True
        token_pair = _make_token_pair()
        token_service.create_token_pair.return_value = token_pair
        refresh_token_repository.save.return_value = MagicMock()

        _, result = await use_case.authenticate("test@example.com", "password")

        # Verify token service called with user_id and a family_id (UUID string)
        token_service.create_token_pair.assert_called_once()
        call_args = token_service.create_token_pair.call_args
        assert call_args[1]["user_id"] == 1 or call_args[0][0] == 1

        # Verify refresh token was persisted
        refresh_token_repository.save.assert_called_once()
        saved_token = refresh_token_repository.save.call_args[0][0]
        assert saved_token.jti == "test-jti"
        assert saved_token.family_id == "test-family"
        assert saved_token.user_id == UserId(1)

    async def test_authenticate_returns_token_pair_with_metadata(
        self, use_case, user_repository, password_service, token_service, refresh_token_repository
    ) -> None:
        user = _make_user()
        user_repository.find_by_email.return_value = user
        password_service.verify_password.return_value = True
        token_pair = _make_token_pair()
        token_service.create_token_pair.return_value = token_pair
        refresh_token_repository.save.return_value = MagicMock()

        _, result = await use_case.authenticate("test@example.com", "password")

        assert result.access_token == "access"
        assert result.jti == "test-jti"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/application/identity/use_cases/authentication/test_authenticate_user_use_case.py -v`
Expected: FAIL

- [ ] **Step 3: Update AuthenticateUserUseCase**

Replace the entire contents of `backend/src/application/identity/use_cases/authentication/authenticate_user_use_case.py`:

```python
"""Use case for authenticating a user with email and password."""

import uuid

import structlog

from src.application.identity.dtos import TokenPairWithMetadata
from src.application.identity.protocols.password_service import PasswordServiceProtocol
from src.application.identity.protocols.refresh_token_repository import (
    RefreshTokenRepositoryProtocol,
)
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.identity.entities.refresh_token import RefreshToken
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError

logger = structlog.get_logger(__name__)


class AuthenticateUserUseCase:
    """Use case for authenticating a user with email and password."""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        password_service: PasswordServiceProtocol,
        token_service: TokenServiceProtocol,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def authenticate(
        self, email: str, password: str
    ) -> tuple[User, TokenPairWithMetadata]:
        user = await self.user_repository.find_by_email(email)

        if not user:
            self.password_service.verify_password(password, self.password_service.get_dummy_hash())
            raise InvalidCredentialsError

        if not user.hashed_password or not self.password_service.verify_password(
            password, user.hashed_password
        ):
            raise InvalidCredentialsError

        family_id = str(uuid.uuid4())
        token_pair = self.token_service.create_token_pair(user.id.value, family_id)

        refresh_token_entity = RefreshToken.create(
            jti=token_pair.jti,
            user_id=user.id,
            family_id=token_pair.family_id,
            expires_at=token_pair.expires_at,
        )
        await self.refresh_token_repository.save(refresh_token_entity)

        logger.info("user_authenticated", user_id=user.id.value, email=email)

        return user, token_pair
```

Wait — `TokenPairWithMetadata` doesn't have `expires_at`. The `RefreshToken.create()` needs it. Let me fix this: we need to compute `expires_at` in the use case. Update the use case to compute it:

Replace the token persistence section with:

```python
        from datetime import UTC, datetime, timedelta
        from src.infrastructure.identity.services.token_service import REFRESH_TOKEN_EXPIRE_DAYS
```

Actually, we should not import from infrastructure. The `expires_at` should come from the token service. Let me add `expires_at` to `TokenPairWithMetadata`.

- [ ] **Step 3 (revised): Add expires_at to TokenPairWithMetadata**

Update `backend/src/application/identity/dtos.py` — add `expires_at` field:

```python
"""Application-layer DTOs for identity module."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RefreshTokenClaims:
    """Claims extracted from a verified refresh token JWT."""

    user_id: int
    jti: str


@dataclass(frozen=True)
class TokenPairWithMetadata:
    """Token pair with metadata needed for persistence."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    jti: str
    family_id: str
    refresh_token_expires_at: datetime
```

Then update `token_service.py` `create_token_pair` function to include `refresh_token_expires_at`:

In `backend/src/infrastructure/identity/services/token_service.py`, update `create_token_pair`:

```python
def create_token_pair(user_id: int, family_id: str) -> TokenPairWithMetadata:
    """Create a token pair (access + refresh) for a user."""
    jti = str(uuid.uuid4())
    access_token = create_access_token(user_id)
    refresh_token_expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(user_id, jti)
    return TokenPairWithMetadata(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        jti=jti,
        family_id=family_id,
        refresh_token_expires_at=refresh_token_expires_at,
    )
```

- [ ] **Step 4: Now write the final AuthenticateUserUseCase**

Replace the entire contents of `backend/src/application/identity/use_cases/authentication/authenticate_user_use_case.py`:

```python
"""Use case for authenticating a user with email and password."""

import uuid

import structlog

from src.application.identity.dtos import TokenPairWithMetadata
from src.application.identity.protocols.password_service import PasswordServiceProtocol
from src.application.identity.protocols.refresh_token_repository import (
    RefreshTokenRepositoryProtocol,
)
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.identity.entities.refresh_token import RefreshToken
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError

logger = structlog.get_logger(__name__)


class AuthenticateUserUseCase:
    """Use case for authenticating a user with email and password."""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        password_service: PasswordServiceProtocol,
        token_service: TokenServiceProtocol,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def authenticate(
        self, email: str, password: str
    ) -> tuple[User, TokenPairWithMetadata]:
        user = await self.user_repository.find_by_email(email)

        if not user:
            self.password_service.verify_password(password, self.password_service.get_dummy_hash())
            raise InvalidCredentialsError

        if not user.hashed_password or not self.password_service.verify_password(
            password, user.hashed_password
        ):
            raise InvalidCredentialsError

        family_id = str(uuid.uuid4())
        token_pair = self.token_service.create_token_pair(user.id.value, family_id)

        refresh_token_entity = RefreshToken.create(
            jti=token_pair.jti,
            user_id=user.id,
            family_id=token_pair.family_id,
            expires_at=token_pair.refresh_token_expires_at,
        )
        await self.refresh_token_repository.save(refresh_token_entity)

        logger.info("user_authenticated", user_id=user.id.value, email=email)

        return user, token_pair
```

- [ ] **Step 5: Update the test fixture to include refresh_token_expires_at**

In `test_authenticate_user_use_case.py`, update `_make_token_pair`:

```python
from datetime import UTC, datetime, timedelta

def _make_token_pair() -> TokenPairWithMetadata:
    return TokenPairWithMetadata(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=900,
        jti="test-jti",
        family_id="test-family",
        refresh_token_expires_at=datetime.now(UTC) + timedelta(days=30),
    )
```

- [ ] **Step 6: Run tests**

Run: `cd backend && uv run pytest tests/unit/application/identity/use_cases/authentication/test_authenticate_user_use_case.py -v`
Expected: All tests PASS

- [ ] **Step 7: Run pyright**

Run: `cd backend && uv run pyright src/application/identity/use_cases/authentication/authenticate_user_use_case.py`
Expected: 0 errors

- [ ] **Step 8: Commit**

```bash
git add backend/src/application/identity/dtos.py backend/src/infrastructure/identity/services/token_service.py backend/src/application/identity/use_cases/authentication/authenticate_user_use_case.py backend/tests/unit/application/identity/
git commit -m "feat: persist refresh token on login"
```

---

## Task 11: Update RegisterUserUseCase

**Files:**
- Modify: `backend/src/application/identity/use_cases/register_user_use_case.py`
- Create: `backend/tests/unit/application/identity/use_cases/test_register_user_use_case.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/unit/application/identity/use_cases/test_register_user_use_case.py`:

```python
"""Tests for RegisterUserUseCase with token rotation."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.identity.dtos import TokenPairWithMetadata
from src.application.identity.use_cases.register_user_use_case import RegisterUserUseCase
from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User


def _make_user(user_id: int = 1) -> User:
    return User.create_with_id(
        id=UserId(user_id),
        email="new@example.com",
        hashed_password="hashed",
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )


def _make_token_pair() -> TokenPairWithMetadata:
    return TokenPairWithMetadata(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=900,
        jti="test-jti",
        family_id="test-family",
        refresh_token_expires_at=datetime.now(UTC) + timedelta(days=30),
    )


class TestRegisterUserUseCase:
    @pytest.fixture
    def user_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def password_service(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def token_service(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def refresh_token_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def use_case(
        self, user_repository, password_service, token_service, refresh_token_repository
    ) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            user_repository=user_repository,
            password_service=password_service,
            token_service=token_service,
            refresh_token_repository=refresh_token_repository,
        )

    @patch("src.application.identity.use_cases.register_user_use_case.is_user_registrations_enabled", return_value=True)
    async def test_register_persists_refresh_token(
        self, _mock_flag, use_case, user_repository, password_service, token_service, refresh_token_repository
    ) -> None:
        password_service.hash_password.return_value = "hashed"
        user = _make_user()
        user_repository.save.return_value = user

        token_pair = _make_token_pair()
        token_service.create_token_pair.return_value = token_pair
        refresh_token_repository.save.return_value = MagicMock()

        _, result = await use_case.register_user("new@example.com", "password")

        refresh_token_repository.save.assert_called_once()
        saved = refresh_token_repository.save.call_args[0][0]
        assert saved.jti == "test-jti"
        assert saved.family_id == "test-family"
        assert saved.user_id == UserId(1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/application/identity/use_cases/test_register_user_use_case.py -v`
Expected: FAIL

- [ ] **Step 3: Update RegisterUserUseCase**

Replace the entire contents of `backend/src/application/identity/use_cases/register_user_use_case.py`:

```python
"""Use case for user registration."""

import uuid

import structlog

from src.application.identity.dtos import TokenPairWithMetadata
from src.application.identity.protocols.password_service import PasswordServiceProtocol
from src.application.identity.protocols.refresh_token_repository import (
    RefreshTokenRepositoryProtocol,
)
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.identity.entities.refresh_token import RefreshToken
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import RegistrationDisabledError
from src.feature_flags import is_user_registrations_enabled

logger = structlog.get_logger(__name__)


class RegisterUserUseCase:
    """Use case for user registration operations."""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        password_service: PasswordServiceProtocol,
        token_service: TokenServiceProtocol,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.password_service = password_service
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def register_user(
        self, email: str, password: str
    ) -> tuple[User, TokenPairWithMetadata]:
        if not is_user_registrations_enabled():
            raise RegistrationDisabledError

        hashed_password = self.password_service.hash_password(password)

        user = User.create(email=email, hashed_password=hashed_password)
        user = await self.user_repository.save(user)

        family_id = str(uuid.uuid4())
        token_pair = self.token_service.create_token_pair(user.id.value, family_id)

        refresh_token_entity = RefreshToken.create(
            jti=token_pair.jti,
            user_id=user.id,
            family_id=token_pair.family_id,
            expires_at=token_pair.refresh_token_expires_at,
        )
        await self.refresh_token_repository.save(refresh_token_entity)

        logger.info("user_registered", user_id=user.id.value, email=email)

        return user, token_pair
```

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest tests/unit/application/identity/use_cases/test_register_user_use_case.py -v`
Expected: PASS

- [ ] **Step 5: Run pyright**

Run: `cd backend && uv run pyright src/application/identity/use_cases/register_user_use_case.py`
Expected: 0 errors

- [ ] **Step 6: Commit**

```bash
git add backend/src/application/identity/use_cases/register_user_use_case.py backend/tests/unit/application/identity/use_cases/test_register_user_use_case.py
git commit -m "feat: persist refresh token on registration"
```

---

## Task 12: Update RefreshAccessTokenUseCase with Rotation Logic

**Files:**
- Modify: `backend/src/application/identity/use_cases/authentication/refresh_access_token_use_case.py`
- Create: `backend/tests/unit/application/identity/use_cases/authentication/test_refresh_access_token_use_case.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/application/identity/use_cases/authentication/test_refresh_access_token_use_case.py`:

```python
"""Tests for RefreshAccessTokenUseCase with token rotation."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.identity.dtos import RefreshTokenClaims, TokenPairWithMetadata
from src.application.identity.use_cases.authentication.refresh_access_token_use_case import (
    RefreshAccessTokenUseCase,
)
from src.domain.common.value_objects.ids import RefreshTokenId, UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError


def _make_user(user_id: int = 1) -> User:
    return User.create_with_id(
        id=UserId(user_id),
        email="test@example.com",
        hashed_password="hashed",
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )


def _make_token_pair(family_id: str = "family-1") -> TokenPairWithMetadata:
    return TokenPairWithMetadata(
        access_token="new-access",
        refresh_token="new-refresh",
        token_type="bearer",
        expires_in=900,
        jti="new-jti",
        family_id=family_id,
        refresh_token_expires_at=datetime.now(UTC) + timedelta(days=30),
    )


def _make_refresh_token(
    jti: str = "old-jti",
    family_id: str = "family-1",
    revoked_at: datetime | None = None,
) -> RefreshToken:
    return RefreshToken.create_with_id(
        id=RefreshTokenId(1),
        jti=jti,
        user_id=UserId(1),
        family_id=family_id,
        revoked_at=revoked_at,
        expires_at=datetime.now(UTC) + timedelta(days=30),
        created_at=datetime.now(UTC),
    )


class TestRefreshAccessTokenUseCase:
    @pytest.fixture
    def user_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def token_service(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def refresh_token_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def use_case(
        self, user_repository, token_service, refresh_token_repository
    ) -> RefreshAccessTokenUseCase:
        return RefreshAccessTokenUseCase(
            user_repository=user_repository,
            token_service=token_service,
            refresh_token_repository=refresh_token_repository,
        )

    async def test_successful_rotation(
        self, use_case, user_repository, token_service, refresh_token_repository
    ) -> None:
        claims = RefreshTokenClaims(user_id=1, jti="old-jti")
        token_service.verify_refresh_token.return_value = claims

        existing_token = _make_refresh_token()
        refresh_token_repository.find_by_jti.return_value = existing_token

        user = _make_user()
        user_repository.find_by_id.return_value = user

        token_pair = _make_token_pair()
        token_service.create_token_pair.return_value = token_pair

        refresh_token_repository.save.return_value = MagicMock()

        _, result = await use_case.refresh_token("old-token")

        assert result.access_token == "new-access"
        # Old token should be revoked
        refresh_token_repository.revoke_family.assert_not_called()
        # New token should be saved
        refresh_token_repository.save.assert_called_once()
        saved = refresh_token_repository.save.call_args[0][0]
        assert saved.jti == "new-jti"
        assert saved.family_id == "family-1"

    async def test_invalid_jwt_raises_error(
        self, use_case, token_service
    ) -> None:
        token_service.verify_refresh_token.return_value = None
        with pytest.raises(InvalidCredentialsError):
            await use_case.refresh_token("bad-token")

    async def test_unknown_jti_raises_error(
        self, use_case, token_service, refresh_token_repository
    ) -> None:
        claims = RefreshTokenClaims(user_id=1, jti="unknown")
        token_service.verify_refresh_token.return_value = claims
        refresh_token_repository.find_by_jti.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await use_case.refresh_token("some-token")

    async def test_revoked_token_triggers_family_revocation(
        self, use_case, token_service, refresh_token_repository
    ) -> None:
        claims = RefreshTokenClaims(user_id=1, jti="revoked-jti")
        token_service.verify_refresh_token.return_value = claims

        revoked_token = _make_refresh_token(
            jti="revoked-jti", revoked_at=datetime.now(UTC)
        )
        refresh_token_repository.find_by_jti.return_value = revoked_token

        with pytest.raises(InvalidCredentialsError):
            await use_case.refresh_token("revoked-token")

        refresh_token_repository.revoke_family.assert_called_once_with("family-1")

    async def test_user_not_found_raises_error(
        self, use_case, token_service, refresh_token_repository, user_repository
    ) -> None:
        claims = RefreshTokenClaims(user_id=1, jti="old-jti")
        token_service.verify_refresh_token.return_value = claims
        refresh_token_repository.find_by_jti.return_value = _make_refresh_token()
        user_repository.find_by_id.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await use_case.refresh_token("some-token")

    async def test_lazy_cleanup_called(
        self, use_case, user_repository, token_service, refresh_token_repository
    ) -> None:
        claims = RefreshTokenClaims(user_id=1, jti="old-jti")
        token_service.verify_refresh_token.return_value = claims
        refresh_token_repository.find_by_jti.return_value = _make_refresh_token()
        user_repository.find_by_id.return_value = _make_user()
        token_service.create_token_pair.return_value = _make_token_pair()
        refresh_token_repository.save.return_value = MagicMock()

        await use_case.refresh_token("token")

        refresh_token_repository.delete_expired_for_user.assert_called_once_with(UserId(1))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/application/identity/use_cases/authentication/test_refresh_access_token_use_case.py -v`
Expected: FAIL

- [ ] **Step 3: Update RefreshAccessTokenUseCase**

Replace the entire contents of `backend/src/application/identity/use_cases/authentication/refresh_access_token_use_case.py`:

```python
"""Use case for refreshing access token with token rotation."""

import structlog

from src.application.identity.dtos import TokenPairWithMetadata
from src.application.identity.protocols.refresh_token_repository import (
    RefreshTokenRepositoryProtocol,
)
from src.application.identity.protocols.token_service import TokenServiceProtocol
from src.application.identity.protocols.user_repository import UserRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import InvalidCredentialsError

logger = structlog.get_logger(__name__)


class RefreshAccessTokenUseCase:
    """Use case for refreshing access token with token rotation."""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        token_service: TokenServiceProtocol,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.user_repository = user_repository
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def refresh_token(
        self, refresh_token: str
    ) -> tuple[User, TokenPairWithMetadata]:
        # 1. Verify JWT and extract claims
        claims = self.token_service.verify_refresh_token(refresh_token)
        if claims is None:
            raise InvalidCredentialsError

        # 2. Look up token in DB by jti
        existing_token = await self.refresh_token_repository.find_by_jti(claims.jti)
        if existing_token is None:
            raise InvalidCredentialsError

        # 3. Replay detection: if token is revoked, revoke entire family
        if existing_token.is_revoked:
            await self.refresh_token_repository.revoke_family(existing_token.family_id)
            logger.warning(
                "refresh_token_replay_detected",
                jti=claims.jti,
                family_id=existing_token.family_id,
            )
            raise InvalidCredentialsError

        # 4. Verify user still exists
        user = await self.user_repository.find_by_id(UserId(claims.user_id))
        if not user:
            raise InvalidCredentialsError

        # 5. Revoke current token
        existing_token.revoke()
        await self.refresh_token_repository.save(existing_token)

        # 6. Create new token pair in same family
        token_pair = self.token_service.create_token_pair(
            user.id.value, existing_token.family_id
        )

        # 7. Persist new refresh token
        new_token = RefreshToken.create(
            jti=token_pair.jti,
            user_id=user.id,
            family_id=existing_token.family_id,
            expires_at=token_pair.refresh_token_expires_at,
        )
        await self.refresh_token_repository.save(new_token)

        # 8. Lazy cleanup
        await self.refresh_token_repository.delete_expired_for_user(user.id)

        logger.info("access_token_refreshed", user_id=user.id.value)

        return user, token_pair
```

Note: The `save` method is used for both creating new tokens and updating existing ones. The repository implementation detects new vs. existing by checking `id.value == 0`. For the revoked token update, the `id.value` is non-zero, so the repository needs to handle updates. Update the repository's `save` method to handle updates:

In `backend/src/infrastructure/identity/repositories/refresh_token_repository.py`, update `save`:

```python
    async def save(self, token: RefreshToken) -> RefreshToken:
        if token.id.value == 0:
            # New token
            orm_model = self.mapper.to_orm(token)
            self.db.add(orm_model)
            await self.db.commit()
            await self.db.refresh(orm_model)
            return self.mapper.to_domain(orm_model)
        else:
            # Update existing (e.g., revoking)
            stmt = select(RefreshTokenORM).where(RefreshTokenORM.id == token.id.value)
            result = await self.db.execute(stmt)
            orm_model = result.scalar_one()
            orm_model.revoked_at = token.revoked_at
            await self.db.commit()
            await self.db.refresh(orm_model)
            return self.mapper.to_domain(orm_model)
```

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest tests/unit/application/identity/use_cases/authentication/test_refresh_access_token_use_case.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Run pyright**

Run: `cd backend && uv run pyright src/application/identity/use_cases/authentication/refresh_access_token_use_case.py src/infrastructure/identity/repositories/refresh_token_repository.py`
Expected: 0 errors

- [ ] **Step 6: Commit**

```bash
git add backend/src/application/identity/use_cases/authentication/refresh_access_token_use_case.py backend/src/infrastructure/identity/repositories/refresh_token_repository.py backend/tests/unit/application/identity/use_cases/authentication/test_refresh_access_token_use_case.py
git commit -m "feat: add token rotation logic to RefreshAccessTokenUseCase"
```

---

## Task 13: Create LogoutUseCase

**Files:**
- Create: `backend/src/application/identity/use_cases/authentication/logout_use_case.py`
- Create: `backend/tests/unit/application/identity/use_cases/authentication/test_logout_use_case.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/application/identity/use_cases/authentication/test_logout_use_case.py`:

```python
"""Tests for LogoutUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.identity.dtos import RefreshTokenClaims
from src.application.identity.use_cases.authentication.logout_use_case import LogoutUseCase
from src.domain.common.value_objects.ids import RefreshTokenId, UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from datetime import UTC, datetime, timedelta


class TestLogoutUseCase:
    @pytest.fixture
    def token_service(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def refresh_token_repository(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def use_case(self, token_service, refresh_token_repository) -> LogoutUseCase:
        return LogoutUseCase(
            token_service=token_service,
            refresh_token_repository=refresh_token_repository,
        )

    async def test_logout_revokes_family(
        self, use_case, token_service, refresh_token_repository
    ) -> None:
        claims = RefreshTokenClaims(user_id=1, jti="test-jti")
        token_service.verify_refresh_token.return_value = claims

        token = RefreshToken.create_with_id(
            id=RefreshTokenId(1),
            jti="test-jti",
            user_id=UserId(1),
            family_id="family-1",
            revoked_at=None,
            expires_at=datetime.now(UTC) + timedelta(days=30),
            created_at=datetime.now(UTC),
        )
        refresh_token_repository.find_by_jti.return_value = token

        await use_case.logout("refresh-token-string")

        refresh_token_repository.revoke_family.assert_called_once_with("family-1")

    async def test_logout_with_invalid_token_succeeds_silently(
        self, use_case, token_service, refresh_token_repository
    ) -> None:
        token_service.verify_refresh_token.return_value = None

        # Should not raise
        await use_case.logout("bad-token")

        refresh_token_repository.revoke_family.assert_not_called()

    async def test_logout_with_none_token_succeeds_silently(
        self, use_case, token_service, refresh_token_repository
    ) -> None:
        # Should not raise
        await use_case.logout(None)

        token_service.verify_refresh_token.assert_not_called()
        refresh_token_repository.revoke_family.assert_not_called()

    async def test_logout_with_unknown_jti_succeeds_silently(
        self, use_case, token_service, refresh_token_repository
    ) -> None:
        claims = RefreshTokenClaims(user_id=1, jti="unknown")
        token_service.verify_refresh_token.return_value = claims
        refresh_token_repository.find_by_jti.return_value = None

        # Should not raise
        await use_case.logout("some-token")

        refresh_token_repository.revoke_family.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/application/identity/use_cases/authentication/test_logout_use_case.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Create LogoutUseCase**

Create `backend/src/application/identity/use_cases/authentication/logout_use_case.py`:

```python
"""Use case for logging out by revoking the refresh token family."""

import structlog

from src.application.identity.protocols.refresh_token_repository import (
    RefreshTokenRepositoryProtocol,
)
from src.application.identity.protocols.token_service import TokenServiceProtocol

logger = structlog.get_logger(__name__)


class LogoutUseCase:
    """Revoke the refresh token family on logout."""

    def __init__(
        self,
        token_service: TokenServiceProtocol,
        refresh_token_repository: RefreshTokenRepositoryProtocol,
    ) -> None:
        self.token_service = token_service
        self.refresh_token_repository = refresh_token_repository

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return

        claims = self.token_service.verify_refresh_token(refresh_token)
        if claims is None:
            return

        existing_token = await self.refresh_token_repository.find_by_jti(claims.jti)
        if existing_token is None:
            return

        await self.refresh_token_repository.revoke_family(existing_token.family_id)

        logger.info(
            "user_logged_out",
            user_id=claims.user_id,
            family_id=existing_token.family_id,
        )
```

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest tests/unit/application/identity/use_cases/authentication/test_logout_use_case.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Run pyright**

Run: `cd backend && uv run pyright src/application/identity/use_cases/authentication/logout_use_case.py`
Expected: 0 errors

- [ ] **Step 6: Wire LogoutUseCase into DI container**

In `backend/src/containers/identity.py`, add import at top:

```python
from src.application.identity.use_cases.authentication.logout_use_case import LogoutUseCase
```

Add the factory after the existing use cases:

```python
    logout_use_case = providers.Factory(
        LogoutUseCase,
        token_service=token_service,
        refresh_token_repository=refresh_token_repository,
    )
```

- [ ] **Step 7: Run pyright on container**

Run: `cd backend && uv run pyright src/containers/identity.py`
Expected: 0 errors

- [ ] **Step 8: Commit**

```bash
git add backend/src/application/identity/use_cases/authentication/logout_use_case.py backend/tests/unit/application/identity/use_cases/authentication/test_logout_use_case.py backend/src/containers/identity.py
git commit -m "feat: add LogoutUseCase for token family revocation"
```

---

## Task 14: Update Auth Router

**Files:**
- Modify: `backend/src/infrastructure/identity/routers/auth.py`

- [ ] **Step 1: Update auth.py**

Replace the entire contents of `backend/src/infrastructure/identity/routers/auth.py`:

```python
"""Authentication routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette import status

from src.application.identity.dtos import TokenPairWithMetadata
from src.application.identity.use_cases.authentication.authenticate_user_use_case import (
    AuthenticateUserUseCase,
)
from src.application.identity.use_cases.authentication.logout_use_case import LogoutUseCase
from src.application.identity.use_cases.authentication.refresh_access_token_use_case import (
    RefreshAccessTokenUseCase,
)
from src.config import get_settings
from src.core import container
from src.domain.identity.exceptions import InvalidCredentialsError
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.services.token_service import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    TokenWithRefresh,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)
settings = get_settings()


class RefreshTokenRequest(BaseModel):
    """Request body for refresh token (used by plugins)."""

    refresh_token: str | None = None


def _to_response(token_pair: TokenPairWithMetadata) -> TokenWithRefresh:
    """Convert TokenPairWithMetadata to HTTP response model."""
    return TokenWithRefresh(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an httpOnly cookie."""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path="/api/v1/auth",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path="/api/v1/auth",
    )


@router.post("/login")
@limiter.limit("5/minute")  # type: ignore[misc]
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    use_case: AuthenticateUserUseCase = Depends(
        inject_use_case(container.identity.authenticate_user_use_case)
    ),
) -> TokenWithRefresh:
    try:
        _, token_pair = await use_case.authenticate(form_data.username, form_data.password)
        set_refresh_cookie(response, token_pair.refresh_token)
        return _to_response(token_pair)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


@router.post("/refresh")
@limiter.limit("10/minute")  # type: ignore[misc]
async def refresh(
    request: Request,
    response: Response,
    body: RefreshTokenRequest | None = None,
    refresh_token: Annotated[str | None, Cookie()] = None,
    use_case: RefreshAccessTokenUseCase = Depends(
        inject_use_case(container.identity.refresh_access_token_use_case)
    ),
) -> TokenWithRefresh:
    token = refresh_token
    if not token and body and body.refresh_token:
        token = body.refresh_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    try:
        _, token_pair = await use_case.refresh_token(token)
        set_refresh_cookie(response, token_pair.refresh_token)
        return _to_response(token_pair)
    except InvalidCredentialsError:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    use_case: LogoutUseCase = Depends(
        inject_use_case(container.identity.logout_use_case)
    ),
) -> dict[str, str]:
    await use_case.logout(refresh_token)
    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}
```

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/identity/routers/auth.py`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add backend/src/infrastructure/identity/routers/auth.py
git commit -m "feat: update auth router for token rotation and logout revocation"
```

---

## Task 15: Update Users Router for Registration Response

**Files:**
- Modify: `backend/src/infrastructure/identity/routers/users.py`

The registration endpoint currently returns `TokenWithRefresh` directly from the use case. After our changes, the use case returns `TokenPairWithMetadata`, so the router must convert it.

- [ ] **Step 1: Update users.py**

In `backend/src/infrastructure/identity/routers/users.py`:

Replace the `TokenWithRefresh` import (line 27):

```python
from src.infrastructure.identity.services.token_service import TokenWithRefresh
```

with:

```python
from src.infrastructure.identity.routers.auth import _to_response
from src.infrastructure.identity.services.token_service import TokenWithRefresh
```

Update the `register` endpoint (line 52-55) — convert the result and remove the explicit `db.commit()` since repositories now self-commit:

Replace:
```python
        _, token_pair = await use_case.register_user(register_data.email, register_data.password)
        await db.commit()
        set_refresh_cookie(response, token_pair.refresh_token)
        return token_pair
```

With:
```python
        _, token_pair = await use_case.register_user(register_data.email, register_data.password)
        set_refresh_cookie(response, token_pair.refresh_token)
        return _to_response(token_pair)
```

Also remove the `db: DatabaseSession` parameter from the `register` function signature (line 40) and the `DatabaseSession` import (line 11) if it's no longer used by any other endpoint in this file. Check `update_me` — it still uses `db: DatabaseSession` (line 89), so keep the import but remove `db` from `register` only.

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/identity/routers/users.py`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add backend/src/infrastructure/identity/routers/users.py
git commit -m "feat: update users router for token rotation response type"
```

---

## Task 16: Run Full Test Suite and Fix Issues

- [ ] **Step 1: Run full test suite**

Run: `cd backend && uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 2: Run pyright on all changed files**

Run: `cd backend && uv run pyright`
Expected: 0 errors

- [ ] **Step 3: Run ruff**

Run: `cd backend && uv run ruff check src/`
Expected: No errors

- [ ] **Step 4: Fix any issues found**

If any tests fail or type errors appear, fix them before proceeding.

- [ ] **Step 5: Final commit (if fixes needed)**

```bash
git add -u
git commit -m "fix: resolve test/type errors from token rotation implementation"
```
