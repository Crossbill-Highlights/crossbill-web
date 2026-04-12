from typing import Protocol


class CoverImageServiceProtocol(Protocol):
    def process_cover(self, image_bytes: bytes) -> tuple[bytes, str]: ...
