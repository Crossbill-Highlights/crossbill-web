"""Tests for PrereadingTaskHandler."""

from unittest.mock import AsyncMock

import pytest

from src.infrastructure.jobs.tasks.prereading_task_handler import PrereadingTaskHandler


@pytest.fixture
def use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def handler(use_case: AsyncMock) -> PrereadingTaskHandler:
    return PrereadingTaskHandler(generate_from_text_use_case=use_case)


class TestPrereadingTaskHandler:
    async def test_calls_use_case_with_correct_args(
        self, handler: PrereadingTaskHandler, use_case: AsyncMock
    ) -> None:
        ctx: dict[str, object] = {}
        await handler.generate(
            ctx,  # pyright: ignore[reportArgumentType]
            batch_id=1,
            chapter_id=7,
            user_id=1,
            chapter_text="Some chapter content here",
        )

        use_case.execute.assert_called_once()
        call_kwargs = use_case.execute.call_args.kwargs
        assert call_kwargs["chapter_id"].value == 7
        assert call_kwargs["user_id"].value == 1
        assert call_kwargs["chapter_text"] == "Some chapter content here"
