from datetime import UTC, datetime
from typing import Any

import pytest

from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import ChapterId, PrereadingContentId
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
    PrereadingQuestion,
)


def _create(**overrides: Any) -> ChapterPrereadingContent:  # noqa: ANN401
    """Create ChapterPrereadingContent with sensible defaults."""
    defaults: dict[str, Any] = {
        "chapter_id": ChapterId(1),
        "summary": "This chapter covers the basics of testing.",
        "keypoints": [
            "Write tests first",
            "Keep tests simple",
            "Test behavior, not implementation",
        ],
        "questions": [
            PrereadingQuestion(question="What is testing?", answer="Verifying correctness."),
        ],
        "generated_at": datetime.now(UTC),
        "ai_model": "gpt-4",
    }
    defaults.update(overrides)
    return ChapterPrereadingContent.create(**defaults)  # type: ignore[arg-type]


def test_create_prereading_content() -> None:
    content = _create()
    assert content.chapter_id == ChapterId(1)
    assert "basics of testing" in content.summary
    assert len(content.keypoints) == 3
    assert content.ai_model == "gpt-4"


def test_create_strips_whitespace() -> None:
    content = _create(
        summary="  Summary with spaces  ",
        keypoints=["  Point 1  ", "Point 2"],
        ai_model="  gpt-4  ",
    )
    assert content.summary == "Summary with spaces"
    assert content.keypoints == ["Point 1", "Point 2"]
    assert content.ai_model == "gpt-4"


def test_create_with_id() -> None:
    now = datetime.now(UTC)
    content = ChapterPrereadingContent.create_with_id(
        id=PrereadingContentId(42),
        chapter_id=ChapterId(1),
        summary="Summary",
        keypoints=["Point 1"],
        questions=[],
        generated_at=now,
        ai_model="gpt-4",
    )
    assert content.id == PrereadingContentId(42)
    assert content.generated_at == now


def test_empty_summary_raises_error() -> None:
    with pytest.raises(DomainError, match="Summary cannot be empty"):
        _create(summary="")


def test_whitespace_only_summary_raises_error() -> None:
    with pytest.raises(DomainError, match="Summary cannot be empty"):
        _create(summary="   ")


def test_empty_keypoints_raises_error() -> None:
    with pytest.raises(DomainError, match="Keypoints list cannot be empty"):
        _create(keypoints=[])


def test_empty_keypoint_string_raises_error() -> None:
    with pytest.raises(DomainError, match="Keypoints cannot contain empty strings"):
        _create(keypoints=["Point 1", "", "Point 3"])


def test_empty_ai_model_raises_error() -> None:
    with pytest.raises(DomainError, match="AI model cannot be empty"):
        _create(ai_model="")
