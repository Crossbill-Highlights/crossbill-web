"""Identity infrastructure layer."""

from src.infrastructure.identity.dependencies import get_current_user, oauth2_scheme
from src.infrastructure.identity.repositories.user_repository import UserRepository

__all__ = [
    "UserRepository",
    "get_current_user",
    "oauth2_scheme",
]
