"""Protocol for token service."""

from typing import Protocol

from src.application.identity.dtos import RefreshTokenClaims, TokenPairWithMetadata


class TokenServiceProtocol(Protocol):
    def create_token_pair(self, user_id: int, family_id: str) -> TokenPairWithMetadata: ...

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims | None: ...
