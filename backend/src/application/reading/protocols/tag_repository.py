from typing import Protocol

from src.domain.common.value_objects.ids import BookId, TagId, UserId
from src.domain.library.entities.tag import Tag


class TagRepositoryProtocol(Protocol):
    def find_tags_for_book(self, book_id: BookId, user_id: UserId) -> list[Tag]: ...

    def get_or_create_many(self, names: list[str], user_id: UserId) -> list[Tag]: ...

    def add_tags_to_book(self, book_id: BookId, tag_ids: list[TagId], user_id: UserId) -> None: ...

    def replace_book_tags(self, book_id: BookId, tag_ids: list[TagId], user_id: UserId) -> None: ...
