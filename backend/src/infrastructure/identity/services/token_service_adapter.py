from src.infrastructure.identity.services import token_service
from src.infrastructure.identity.services.token_service import TokenWithRefresh


class TokenServiceAdapter:
    """Adapter wrapping token service functions for DI."""

    def create_token_pair(self, user_id: int) -> TokenWithRefresh:
        return token_service.create_token_pair(user_id)

    def verify_refresh_token(self, token: str) -> int | None:
        return token_service.verify_refresh_token(token)
