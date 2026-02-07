from typing import Protocol

from src.infrastructure.identity.services.token_service import TokenWithRefresh


class TokenServiceProtocol(Protocol):
    def create_token_pair(self, user_id: int) -> TokenWithRefresh: ...

    def verify_refresh_token(self, token: str) -> int | None: ...
