from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PrereadingResult:
    summary: str
    keypoints: list[str]


class AIPrereadingServiceProtocol(Protocol):
    async def generate_prereading(self, content: str) -> PrereadingResult: ...
