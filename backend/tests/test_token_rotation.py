"""Tests for refresh token rotation and reuse detection."""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.identity.use_cases.authentication.authenticate_user_use_case import (
    AuthenticateUserUseCase,
)
from src.application.identity.use_cases.authentication.logout_use_case import LogoutUseCase
from src.application.identity.use_cases.authentication.refresh_access_token_use_case import (
    RefreshAccessTokenUseCase,
)
from src.domain.common.value_objects.ids import RefreshTokenId, UserId
from src.domain.identity.entities.refresh_token import RefreshToken
from src.domain.identity.entities.user import User
from src.domain.identity.exceptions import (
    InvalidCredentialsError,
    RefreshTokenReuseError,
)
from src.infrastructure.identity.services.token_service import TokenWithRefresh


# --- Fixtures ---


@pytest.fixture
def domain_user() -> User:
    return User.create_with_id(
        id=UserId(1),
        email="test@example.com",
        hashed_password="hashed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_user_repo(domain_user: User) -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_id.return_value = domain_user
    repo.find_by_email.return_value = domain_user
    return repo


@pytest.fixture
def mock_password_service() -> MagicMock:
    svc = MagicMock()
    svc.verify_password.return_value = True
    svc.get_dummy_hash.return_value = "dummy"
    return svc


@pytest.fixture
def token_pair() -> TokenWithRefresh:
    return TokenWithRefresh(
        access_token="new-access",
        refresh_token="new-refresh",
        token_type="bearer",
        expires_in=900,
    )


@pytest.fixture
def mock_token_service(token_pair: TokenWithRefresh) -> MagicMock:
    svc = MagicMock()
    svc.verify_refresh_token.return_value = 1
    svc.create_token_pair.return_value = token_pair
    svc.hash_token.side_effect = lambda t: hashlib.sha256(t.encode()).hexdigest()
    svc.get_refresh_token_expiry.return_value = datetime.now(UTC) + timedelta(days=30)
    return svc


@pytest.fixture
def family_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def active_token_record(family_id: str) -> RefreshToken:
    return RefreshToken(
        id=RefreshTokenId(1),
        user_id=UserId(1),
        token_hash=hashlib.sha256(b"old-refresh").hexdigest(),
        family_id=family_id,
        expires_at=datetime.now(UTC) + timedelta(days=30),
        revoked_at=None,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def revoked_token_record(family_id: str) -> RefreshToken:
    return RefreshToken(
        id=RefreshTokenId(2),
        user_id=UserId(1),
        token_hash=hashlib.sha256(b"stolen-refresh").hexdigest(),
        family_id=family_id,
        expires_at=datetime.now(UTC) + timedelta(days=30),
        revoked_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_refresh_repo(active_token_record: RefreshToken) -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_token_hash.return_value = active_token_record
    repo.save.return_value = active_token_record
    repo.revoke_family.return_value = None
    repo.revoke_all_for_user.return_value = None
    return repo


@pytest.fixture
def refresh_use_case(
    mock_user_repo: AsyncMock,
    mock_token_service: MagicMock,
    mock_refresh_repo: AsyncMock,
) -> RefreshAccessTokenUseCase:
    return RefreshAccessTokenUseCase(
        user_repository=mock_user_repo,
        token_service=mock_token_service,
        refresh_token_repository=mock_refresh_repo,
    )


@pytest.fixture
def auth_use_case(
    mock_user_repo: AsyncMock,
    mock_password_service: MagicMock,
    mock_token_service: MagicMock,
    mock_refresh_repo: AsyncMock,
) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(
        user_repository=mock_user_repo,
        password_service=mock_password_service,
        token_service=mock_token_service,
        refresh_token_repository=mock_refresh_repo,
    )


@pytest.fixture
def logout_use_case(
    mock_token_service: MagicMock,
    mock_refresh_repo: AsyncMock,
) -> LogoutUseCase:
    return LogoutUseCase(
        token_service=mock_token_service,
        refresh_token_repository=mock_refresh_repo,
    )


# --- Refresh token rotation tests ---


class TestRefreshTokenRotation:
    async def test_successful_rotation_returns_new_token_pair(
        self,
        refresh_use_case: RefreshAccessTokenUseCase,
    ) -> None:
        user, pair = await refresh_use_case.refresh_token("old-refresh")

        assert pair.access_token == "new-access"
        assert pair.refresh_token == "new-refresh"
        assert user.id == UserId(1)

    async def test_rotation_revokes_old_family(
        self,
        refresh_use_case: RefreshAccessTokenUseCase,
        mock_refresh_repo: AsyncMock,
        family_id: str,
    ) -> None:
        await refresh_use_case.refresh_token("old-refresh")

        mock_refresh_repo.revoke_family.assert_called_once_with(family_id)

    async def test_rotation_saves_new_token_in_same_family(
        self,
        refresh_use_case: RefreshAccessTokenUseCase,
        mock_refresh_repo: AsyncMock,
        family_id: str,
    ) -> None:
        await refresh_use_case.refresh_token("old-refresh")

        saved = mock_refresh_repo.save.call_args[0][0]
        assert isinstance(saved, RefreshToken)
        assert saved.family_id == family_id
        assert saved.revoked_at is None

    async def test_invalid_jwt_raises_credentials_error(
        self,
        refresh_use_case: RefreshAccessTokenUseCase,
        mock_token_service: MagicMock,
    ) -> None:
        mock_token_service.verify_refresh_token.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await refresh_use_case.refresh_token("garbage")

    async def test_unknown_token_hash_raises_credentials_error(
        self,
        refresh_use_case: RefreshAccessTokenUseCase,
        mock_refresh_repo: AsyncMock,
    ) -> None:
        mock_refresh_repo.find_by_token_hash.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await refresh_use_case.refresh_token("unknown-token")

    async def test_deleted_user_raises_credentials_error(
        self,
        refresh_use_case: RefreshAccessTokenUseCase,
        mock_user_repo: AsyncMock,
    ) -> None:
        mock_user_repo.find_by_id.return_value = None

        with pytest.raises(InvalidCredentialsError):
            await refresh_use_case.refresh_token("old-refresh")


class TestRefreshTokenReuseDetection:
    async def test_revoked_token_triggers_reuse_error(
        self,
        refresh_use_case: RefreshAccessTokenUseCase,
        mock_refresh_repo: AsyncMock,
        revoked_token_record: RefreshToken,
    ) -> None:
        mock_refresh_repo.find_by_token_hash.return_value = revoked_token_record

        with pytest.raises(RefreshTokenReuseError):
            await refresh_use_case.refresh_token("stolen-refresh")

    async def test_reuse_revokes_entire_family(
        self,
        refresh_use_case: RefreshAccessTokenUseCase,
        mock_refresh_repo: AsyncMock,
        revoked_token_record: RefreshToken,
        family_id: str,
    ) -> None:
        mock_refresh_repo.find_by_token_hash.return_value = revoked_token_record

        with pytest.raises(RefreshTokenReuseError):
            await refresh_use_case.refresh_token("stolen-refresh")

        mock_refresh_repo.revoke_family.assert_called_once_with(family_id)


# --- Authentication with token storage tests ---


class TestAuthenticateWithTokenStorage:
    async def test_login_stores_refresh_token_record(
        self,
        auth_use_case: AuthenticateUserUseCase,
        mock_refresh_repo: AsyncMock,
    ) -> None:
        await auth_use_case.authenticate("test@example.com", "password")

        mock_refresh_repo.save.assert_called_once()
        saved = mock_refresh_repo.save.call_args[0][0]
        assert isinstance(saved, RefreshToken)
        assert saved.user_id == UserId(1)
        assert saved.revoked_at is None

    async def test_login_creates_new_family(
        self,
        auth_use_case: AuthenticateUserUseCase,
        mock_refresh_repo: AsyncMock,
    ) -> None:
        await auth_use_case.authenticate("test@example.com", "password")

        saved = mock_refresh_repo.save.call_args[0][0]
        # family_id should be a valid UUID
        uuid.UUID(saved.family_id)

    async def test_login_invalid_credentials_does_not_store_token(
        self,
        auth_use_case: AuthenticateUserUseCase,
        mock_password_service: MagicMock,
        mock_refresh_repo: AsyncMock,
    ) -> None:
        mock_password_service.verify_password.return_value = False

        with pytest.raises(InvalidCredentialsError):
            await auth_use_case.authenticate("test@example.com", "wrong")

        mock_refresh_repo.save.assert_not_called()


# --- Logout tests ---


class TestLogout:
    async def test_logout_revokes_token_family(
        self,
        logout_use_case: LogoutUseCase,
        mock_refresh_repo: AsyncMock,
        family_id: str,
    ) -> None:
        await logout_use_case.logout("old-refresh")

        mock_refresh_repo.revoke_family.assert_called_once_with(family_id)

    async def test_logout_with_invalid_jwt_is_noop(
        self,
        logout_use_case: LogoutUseCase,
        mock_token_service: MagicMock,
        mock_refresh_repo: AsyncMock,
    ) -> None:
        mock_token_service.verify_refresh_token.return_value = None

        await logout_use_case.logout("invalid-token")

        mock_refresh_repo.find_by_token_hash.assert_not_called()

    async def test_logout_with_unknown_hash_is_noop(
        self,
        logout_use_case: LogoutUseCase,
        mock_refresh_repo: AsyncMock,
    ) -> None:
        mock_refresh_repo.find_by_token_hash.return_value = None

        await logout_use_case.logout("unknown-token")

        mock_refresh_repo.revoke_family.assert_not_called()


# --- Domain entity tests ---


class TestRefreshTokenEntity:
    def test_is_revoked(self, revoked_token_record: RefreshToken) -> None:
        assert revoked_token_record.is_revoked is True

    def test_is_not_revoked(self, active_token_record: RefreshToken) -> None:
        assert active_token_record.is_revoked is False

    def test_is_expired(self, family_id: str) -> None:
        token = RefreshToken(
            id=RefreshTokenId(1),
            user_id=UserId(1),
            token_hash="hash",
            family_id=family_id,
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert token.is_expired is True

    def test_is_not_expired(self, active_token_record: RefreshToken) -> None:
        assert active_token_record.is_expired is False

    def test_revoke_sets_timestamp(self, active_token_record: RefreshToken) -> None:
        assert active_token_record.revoked_at is None
        active_token_record.revoke()
        assert active_token_record.revoked_at is not None

    def test_create_factory(self) -> None:
        token = RefreshToken.create(
            user_id=UserId(1),
            token_hash="abc123",
            family_id="fam-1",
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        assert token.id == RefreshTokenId(0)  # placeholder
        assert token.user_id == UserId(1)
        assert token.revoked_at is None
