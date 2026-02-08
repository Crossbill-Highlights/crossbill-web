from typing import Protocol


class AITextSummaryServiceProtocol(Protocol):
    async def generate_summary(self, content: str) -> str: ...
