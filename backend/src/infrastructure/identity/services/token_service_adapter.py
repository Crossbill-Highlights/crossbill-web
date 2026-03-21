from datetime import datetime

from src.infrastructure.identity.services import token_service
from src.infrastructure.identity.services.token_service import TokenWithRefresh


class TokenServiceAdapter:
    """Adapter wrapping token service functions for DI."""

    def create_token_pair(self, user_id: int) -> TokenWithRefresh:
        return token_service.create_token_pair(user_id)

    def verify_refresh_token(self, token: str) -> int | None:
        return token_service.verify_refresh_token(token)

    def hash_token(self, token: str) -> str:
        return token_service.hash_token(token)

    def get_refresh_token_expiry(self) -> datetime:
        return token_service.get_refresh_token_expiry()
