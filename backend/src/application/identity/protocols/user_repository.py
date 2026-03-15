from typing import Protocol

from src.domain.common.value_objects.ids import UserId
from src.domain.identity.entities.user import User


class UserRepositoryProtocol(Protocol):
    async def find_by_id(self, user_id: UserId) -> User | None: ...

    async def find_by_email(self, email: str) -> User | None: ...

    async def save(self, user: User) -> User: ...
