"""Tests for PrereadingTaskHandler."""

from unittest.mock import AsyncMock

import pytest

from src.infrastructure.jobs.tasks.prereading_task_handler import PrereadingTaskHandler


@pytest.fixture
def generate_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def handler(generate_use_case: AsyncMock) -> PrereadingTaskHandler:
    return PrereadingTaskHandler(generate_prereading_use_case=generate_use_case)


class TestPrereadingTaskHandler:
    async def test_calls_use_case_with_correct_ids(
        self, handler: PrereadingTaskHandler, generate_use_case: AsyncMock
    ) -> None:
        ctx: dict[str, object] = {}
        await handler.generate(ctx, batch_id=1, book_id=42, chapter_id=7, user_id=1)

        generate_use_case.generate_prereading_content.assert_called_once()
        call_args = generate_use_case.generate_prereading_content.call_args
        assert call_args.kwargs["chapter_id"].value == 7
        assert call_args.kwargs["user_id"].value == 1
