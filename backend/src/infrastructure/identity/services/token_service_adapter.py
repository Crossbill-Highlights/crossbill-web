"""Adapter wrapping token service functions for DI."""

from src.application.identity.dtos import RefreshTokenClaims, TokenPairWithMetadata
from src.infrastructure.identity.services import token_service


class TokenServiceAdapter:
    """Adapter wrapping token service functions for DI."""

    def create_token_pair(self, user_id: int, family_id: str) -> TokenPairWithMetadata:
        return token_service.create_token_pair(user_id, family_id)

    def verify_refresh_token(self, token: str) -> RefreshTokenClaims | None:
        return token_service.verify_refresh_token(token)
