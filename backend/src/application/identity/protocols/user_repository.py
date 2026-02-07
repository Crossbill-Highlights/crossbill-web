from typing import Protocol

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User


class UserRepositoryProtocol(Protocol):
    def find_by_id(self, user_id: UserId) -> User | None: ...

    def find_by_email(self, email: str) -> User | None: ...

    def save(self, user: User) -> User: ...
