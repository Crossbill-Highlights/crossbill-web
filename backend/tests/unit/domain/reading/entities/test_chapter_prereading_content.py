from datetime import UTC, datetime

import pytest

from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import ChapterId, PrereadingContentId
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
)


def test_create_prereading_content() -> None:
    """Test creating valid prereading content."""
    content = ChapterPrereadingContent.create(
        chapter_id=ChapterId(1),
        summary="This chapter covers the basics of testing.",
        keypoints=[
            "Write tests first",
            "Keep tests simple",
            "Test behavior, not implementation",
        ],
        generated_at=datetime.now(UTC),
        ai_model="gpt-4",
    )

    assert content.chapter_id == ChapterId(1)
    assert "basics of testing" in content.summary
    assert len(content.keypoints) == 3
    assert content.ai_model == "gpt-4"


def test_create_strips_whitespace() -> None:
    """Test that create factory strips whitespace from fields."""
    content = ChapterPrereadingContent.create(
        chapter_id=ChapterId(1),
        summary="  Summary with spaces  ",
        keypoints=["  Point 1  ", "Point 2"],
        generated_at=datetime.now(UTC),
        ai_model="  gpt-4  ",
    )

    assert content.summary == "Summary with spaces"
    assert content.keypoints == ["Point 1", "Point 2"]
    assert content.ai_model == "gpt-4"


def test_create_with_id() -> None:
    """Test reconstituting from persistence."""
    now = datetime.now(UTC)
    content = ChapterPrereadingContent.create_with_id(
        id=PrereadingContentId(42),
        chapter_id=ChapterId(1),
        summary="Summary",
        keypoints=["Point 1"],
        generated_at=now,
        ai_model="gpt-4",
    )

    assert content.id == PrereadingContentId(42)
    assert content.generated_at == now


def test_empty_summary_raises_error() -> None:
    """Test that empty summary raises DomainError."""
    with pytest.raises(DomainError, match="Summary cannot be empty"):
        ChapterPrereadingContent.create(
            chapter_id=ChapterId(1),
            summary="",
            keypoints=["Point 1"],
            generated_at=datetime.now(UTC),
            ai_model="gpt-4",
        )


def test_whitespace_only_summary_raises_error() -> None:
    """Test that whitespace-only summary raises DomainError."""
    with pytest.raises(DomainError, match="Summary cannot be empty"):
        ChapterPrereadingContent.create(
            chapter_id=ChapterId(1),
            summary="   ",
            keypoints=["Point 1"],
            generated_at=datetime.now(UTC),
            ai_model="gpt-4",
        )


def test_empty_keypoints_raises_error() -> None:
    """Test that empty keypoints list raises DomainError."""
    with pytest.raises(DomainError, match="Keypoints list cannot be empty"):
        ChapterPrereadingContent.create(
            chapter_id=ChapterId(1),
            summary="Summary",
            keypoints=[],
            generated_at=datetime.now(UTC),
            ai_model="gpt-4",
        )


def test_empty_keypoint_string_raises_error() -> None:
    """Test that keypoints with empty strings raise DomainError."""
    with pytest.raises(DomainError, match="Keypoints cannot contain empty strings"):
        ChapterPrereadingContent.create(
            chapter_id=ChapterId(1),
            summary="Summary",
            keypoints=["Point 1", "", "Point 3"],
            generated_at=datetime.now(UTC),
            ai_model="gpt-4",
        )


def test_empty_ai_model_raises_error() -> None:
    """Test that empty AI model raises DomainError."""
    with pytest.raises(DomainError, match="AI model cannot be empty"):
        ChapterPrereadingContent.create(
            chapter_id=ChapterId(1),
            summary="Summary",
            keypoints=["Point 1"],
            generated_at=datetime.now(UTC),
            ai_model="",
        )
