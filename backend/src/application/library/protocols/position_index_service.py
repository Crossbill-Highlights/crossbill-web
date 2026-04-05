from typing import Protocol

from src.domain.common.value_objects.position_index import PositionIndex


class PositionIndexServiceProtocol(Protocol):
    def build_position_index(self, epub_content: bytes) -> PositionIndex: ...
