# DETAILED MIGRATION GUIDE: Reading Module (Phase 1 & 2)

This guide provides step-by-step instructions for migrating the Reading module (highlights and reading sessions) to the DDD/hexagonal architecture. This serves as a proof of concept before migrating other modules.

## Why Start with Reading Module?

- ✅ Most isolated business logic (deduplication via content_hash)
- ✅ Clear aggregate boundaries (Highlight, ReadingSession)
- ✅ High value feature (core functionality)
- ✅ Good complexity for learning (not too simple, not too complex)
- ✅ Rich domain concepts (XPoint, ContentHash, highlight tags)

## Prerequisites

- Phase 0 complete: Base classes exist in `backend/src/domain/common/`
- Existing code: `models.py`, `HighlightService`, `ReadingSessionService`, `routers/highlights.py`
- Understanding of current flow: KOReader → POST /highlights/upload → HighlightService → Repository → DB

---

## PHASE 1: Foundation - Value Objects & IDs (4-6 hours)

### Goal

Create strongly-typed value objects that encapsulate business rules and prevent primitive obsession.

### Step 1.1: Create Common ID Value Objects

**File: `backend/src/domain/common/value_objects/ids.py`**

```python
"""
Strongly-typed ID value objects.

These prevent accidentally mixing up IDs (e.g., passing a BookId where HighlightId is expected).
"""
from dataclasses import dataclass
from typing import TypeVar, Generic
from ..entity import EntityId

@dataclass(frozen=True)
class BookId(EntityId):
    """Strongly-typed book identifier."""
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("BookId must be positive")

@dataclass(frozen=True)
class UserId(EntityId):
    """Strongly-typed user identifier."""
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("UserId must be positive")

@dataclass(frozen=True)
class HighlightId(EntityId):
    """Strongly-typed highlight identifier."""
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("HighlightId must be positive")

@dataclass(frozen=True)
class ChapterId(EntityId):
    """Strongly-typed chapter identifier."""
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("ChapterId must be positive")

@dataclass(frozen=True)
class ReadingSessionId(EntityId):
    """Strongly-typed reading session identifier."""
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("ReadingSessionId must be positive")

@dataclass(frozen=True)
class HighlightTagId(EntityId):
    """Strongly-typed highlight tag identifier."""
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("HighlightTagId must be positive")
```

**Test: `backend/tests/unit/domain/common/value_objects/test_ids.py`**

```python
import pytest
from backend.src.domain.common.value_objects.ids import BookId, HighlightId

def test_book_id_validation():
    """BookId must be positive."""
    BookId(1)  # Should work
    BookId(999)  # Should work

    with pytest.raises(ValueError, match="must be positive"):
        BookId(0)

    with pytest.raises(ValueError, match="must be positive"):
        BookId(-1)

def test_book_id_immutable():
    """BookId should be immutable."""
    book_id = BookId(1)

    with pytest.raises(AttributeError):
        book_id.value = 2

def test_book_id_equality():
    """BookIds with same value should be equal."""
    assert BookId(1) == BookId(1)
    assert BookId(1) != BookId(2)

def test_different_id_types_not_equal():
    """Different ID types should not be equal even with same value."""
    book_id = BookId(1)
    highlight_id = HighlightId(1)
    assert book_id != highlight_id
```

**Action:**

1. Create the file `backend/src/domain/common/value_objects/ids.py`
2. Create the test file
3. Run tests: `pytest backend/tests/unit/domain/common/value_objects/test_ids.py -v`

---

### Step 1.2: Create XPoint Value Objects

**Note:** XPoint represents KOReader's precise position format in EPUB documents. The primary way to create XPoint is from the string format (e.g., `/body/DocFragment[12]/body/div/p[88]/text().223`).

**File: `backend/src/domain/common/value_objects/xpoint.py`**

```python
"""
XPoint value objects for EPUB position tracking.

XPoint = position within an EPUB document using KOReader format
Used by KOReader to identify precise locations in books.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing import Self

from src.exceptions import XPointParseError


class XPointDict(TypedDict):
    """Dictionary representation of XPoint for JSON serialization."""

    doc_fragment_index: int | None
    xpath: str
    text_node_index: int
    char_offset: int


class XPointRangeDict(TypedDict):
    """Dictionary representation of XPointRange for JSON serialization."""

    start: XPointDict
    end: XPointDict

# Regex pattern for parsing xpoint strings
# Format: /body/DocFragment[N]/body/.../text()[N].offset
_XPOINT_PATTERN = re.compile(
    r"^"
    r"(?:/body/DocFragment\[(\d+)\])?"  # Optional DocFragment[N]
    r"(/body(?:/[^/.\s()]+)*)"          # XPath: /body followed by /element segments
    r"(?:"                               # Optional offset section
    r"(?:/text\(\)(?:\[(\d+)\])?)?"     # Optional: text() with optional [N]
    r"\.(\d+)"                           # .offset
    r")?"
    r"$"
)

@dataclass(frozen=True)
class XPoint:
    """
    Parsed representation of a KOReader xpoint string.

    Attributes:
        doc_fragment_index: 1-based index into EPUB spine (None if not present)
        xpath: XPath to the element (without text() selector)
        text_node_index: 1-based index of text node within element (default 1)
        char_offset: 0-based character offset within text node (default 0)
    """
    doc_fragment_index: int | None
    xpath: str
    text_node_index: int
    char_offset: int

    @classmethod
    def parse(cls, xpoint: str) -> Self:
        """
        Parse an xpoint string into components.

        Formats supported:
        - /body/DocFragment[12]/body/div/p[88]/text().223
        - /body/div[1]/p[5]/text()[1].0
        - /body/DocFragment[14]/body/a (element boundary, defaults to offset 0)

        Args:
            xpoint: The xpoint string to parse

        Returns:
            XPoint with extracted components

        Raises:
            XPointParseError: If the format is invalid
        """
        match = _XPOINT_PATTERN.match(xpoint)
        if not match:
            raise XPointParseError(xpoint, "does not match expected xpoint format")

        doc_fragment_str, xpath, text_node_str, offset_str = match.groups()

        doc_fragment_index = int(doc_fragment_str) if doc_fragment_str else None
        text_node_index = int(text_node_str) if text_node_str else 1
        char_offset = int(offset_str) if offset_str else 0

        if doc_fragment_index is not None and doc_fragment_index < 1:
            raise XPointParseError(xpoint, "DocFragment index must be >= 1")
        if text_node_index < 1:
            raise XPointParseError(xpoint, "text node index must be >= 1")
        if char_offset < 0:
            raise XPointParseError(xpoint, "character offset must be >= 0")

        return cls(
            doc_fragment_index=doc_fragment_index,
            xpath=xpath,
            text_node_index=text_node_index,
            char_offset=char_offset,
        )

    def to_string(self) -> str:
        """Convert XPoint back to KOReader xpoint string format."""
        parts = []
        if self.doc_fragment_index is not None:
            parts.append(f"/body/DocFragment[{self.doc_fragment_index}]")
        parts.append(self.xpath)
        if self.text_node_index != 1 or self.char_offset != 0:
            if self.text_node_index != 1:
                parts.append(f"/text()[{self.text_node_index}]")
            else:
                parts.append("/text()")
            parts.append(f".{self.char_offset}")
        return "".join(parts)

    @classmethod
    def from_dict(cls, data: XPointDict) -> Self:
        """Create XPoint from dictionary (for JSON deserialization)."""
        return cls(
            doc_fragment_index=data.get("doc_fragment_index"),
            xpath=data["xpath"],
            text_node_index=data.get("text_node_index", 1),
            char_offset=data.get("char_offset", 0),
        )

    def to_dict(self) -> XPointDict:
        """Convert to dictionary for JSON serialization."""
        return {
            "doc_fragment_index": self.doc_fragment_index,
            "xpath": self.xpath,
            "text_node_index": self.text_node_index,
            "char_offset": self.char_offset,
        }

    def compare_to(self, other: "XPoint") -> int:
        """
        Compare this XPoint to another for ordering.

        Returns:
            -1 if self < other, 0 if equal, 1 if self > other
        """
        # Compare doc_fragment_index (None treated as 1)
        self_frag = self.doc_fragment_index if self.doc_fragment_index is not None else 1
        other_frag = other.doc_fragment_index if other.doc_fragment_index is not None else 1

        if self_frag != other_frag:
            return -1 if self_frag < other_frag else 1
        if self.xpath != other.xpath:
            return -1 if self.xpath < other.xpath else 1
        if self.text_node_index != other.text_node_index:
            return -1 if self.text_node_index < other.text_node_index else 1
        if self.char_offset != other.char_offset:
            return -1 if self.char_offset < other.char_offset else 1
        return 0

@dataclass(frozen=True)
class XPointRange:
    """
    Range between two XPoints for highlights.

    Represents the start and end position of highlighted text in an EPUB.
    """
    start: XPoint
    end: XPoint

    def __post_init__(self) -> None:
        """Validate that start comes before or at end position."""
        # Compare doc_fragment_index (treating None as 1)
        start_frag = self.start.doc_fragment_index if self.start.doc_fragment_index is not None else 1
        end_frag = self.end.doc_fragment_index if self.end.doc_fragment_index is not None else 1

        if start_frag > end_frag:
            raise ValueError("Start XPoint must come before end XPoint")

        # If same fragment, compare xpath and offsets
        if start_frag == end_frag:
            if self.start.xpath == self.end.xpath:
                # Same element - compare text node and character offset
                if self.start.text_node_index > self.end.text_node_index:
                    raise ValueError("Start text node must be <= end text node")
                if self.start.text_node_index == self.end.text_node_index:
                    if self.start.char_offset > self.end.char_offset:
                        raise ValueError("Start offset must be <= end offset in same element")

    @classmethod
    def parse(cls, start_xpoint_str: str, end_xpoint_str: str) -> Self:
        """Parse XPointRange from two xpoint strings."""
        return cls(
            start=XPoint.parse(start_xpoint_str),
            end=XPoint.parse(end_xpoint_str),
        )

    @classmethod
    def from_dict(cls, data: XPointRangeDict) -> Self:
        """Create XPointRange from dictionary (for JSON deserialization)."""
        return cls(
            start=XPoint.from_dict(data["start"]),
            end=XPoint.from_dict(data["end"]),
        )

    def to_dict(self) -> XPointRangeDict:
        """Convert to dictionary for JSON serialization."""
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
        }

    def contains(self, point: XPoint) -> bool:
        """Check if a point falls within this range (inclusive)."""
        # Point must be >= start and <= end
        cmp_start = point.compare_to(self.start)
        cmp_end = point.compare_to(self.end)
        return cmp_start >= 0 and cmp_end <= 0
```

**Test: `backend/tests/unit/domain/common/value_objects/test_xpoint.py`**

```python
import pytest
from backend.src.domain.common.value_objects.xpoint import XPoint, XPointRange
from backend.src.exceptions import XPointParseError

def test_xpoint_parse():
    """XPoint.parse() parses KOReader xpoint strings."""
    # Full format with DocFragment
    xpoint = XPoint.parse("/body/DocFragment[12]/body/div/p[88]/text().223")
    assert xpoint.doc_fragment_index == 12
    assert xpoint.xpath == "/body/div/p[88]"
    assert xpoint.text_node_index == 1
    assert xpoint.char_offset == 223

    # Without DocFragment
    xpoint = XPoint.parse("/body/div[1]/p[5]/text()[2].42")
    assert xpoint.doc_fragment_index is None
    assert xpoint.xpath == "/body/div[1]/p[5]"
    assert xpoint.text_node_index == 2
    assert xpoint.char_offset == 42

    # Element boundary (no offset)
    xpoint = XPoint.parse("/body/DocFragment[14]/body/a")
    assert xpoint.doc_fragment_index == 14
    assert xpoint.xpath == "/body/a"
    assert xpoint.text_node_index == 1
    assert xpoint.char_offset == 0

def test_xpoint_parse_validation():
    """XPoint.parse() validates xpoint format."""
    with pytest.raises(XPointParseError):
        XPoint.parse("invalid")

    with pytest.raises(XPointParseError, match="DocFragment index"):
        XPoint.parse("/body/DocFragment[0]/body/div.0")

    with pytest.raises(XPointParseError, match="character offset"):
        XPoint.parse("/body/div.text().-1")

def test_xpoint_to_string():
    """XPoint.to_string() converts back to xpoint format."""
    original = "/body/DocFragment[12]/body/div/p[88]/text().223"
    xpoint = XPoint.parse(original)
    assert xpoint.to_string() == original

def test_xpoint_comparison():
    """XPoint.compare_to() orders xpoints correctly."""
    xp1 = XPoint.parse("/body/DocFragment[5]/body/p[1]/text().0")
    xp2 = XPoint.parse("/body/DocFragment[5]/body/p[1]/text().10")
    xp3 = XPoint.parse("/body/DocFragment[6]/body/p[1]/text().0")

    assert xp1.compare_to(xp2) < 0  # xp1 comes before xp2
    assert xp2.compare_to(xp1) > 0  # xp2 comes after xp1
    assert xp1.compare_to(xp1) == 0  # Same position
    assert xp1.compare_to(xp3) < 0  # Different fragments

def test_xpoint_range_parse():
    """XPointRange.parse() creates range from xpoint strings."""
    range_ = XPointRange.parse(
        "/body/div/p[1]/text().0",
        "/body/div/p[1]/text().50"
    )
    assert range_.start.char_offset == 0
    assert range_.end.char_offset == 50

def test_xpoint_range_validation():
    """XPointRange ensures start comes before end."""
    start = XPoint.parse("/body/div/p[1]/text().0")
    end = XPoint.parse("/body/div/p[1]/text().50")

    XPointRange(start, end)  # Valid

    # Invalid: start after end
    with pytest.raises(ValueError):
        XPointRange(end, start)

def test_xpoint_range_contains():
    """XPointRange.contains() works correctly."""
    range_ = XPointRange.parse(
        "/body/div/p[1]/text().10",
        "/body/div/p[1]/text().20"
    )

    assert range_.contains(XPoint.parse("/body/div/p[1]/text().10"))  # At start
    assert range_.contains(XPoint.parse("/body/div/p[1]/text().15"))  # In middle
    assert range_.contains(XPoint.parse("/body/div/p[1]/text().20"))  # At end
    assert not range_.contains(XPoint.parse("/body/div/p[1]/text().5"))   # Before
    assert not range_.contains(XPoint.parse("/body/div/p[1]/text().25"))  # After
```

**Action:**

1. Create `backend/src/domain/common/value_objects/xpoint.py`
2. Create tests
3. Run tests: `pytest backend/tests/unit/domain/common/value_objects/test_xpoint.py -v`

---

### Step 1.3: Create ContentHash Value Object

**File: `backend/src/domain/common/value_objects/content_hash.py`**

```python
"""
ContentHash value object for deduplication.

Used to detect duplicate highlights and reading sessions.
"""
from dataclasses import dataclass
import hashlib
from typing import Self

@dataclass(frozen=True)
class ContentHash:
    """
    SHA-256 hash for content deduplication.

    Used to identify duplicate highlights and reading sessions
    without comparing full text content.
    """
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("ContentHash cannot be empty")

        # Validate it's a valid hex string (SHA-256 is 64 chars)
        if len(self.value) != 64:
            raise ValueError("ContentHash must be 64 character hex string (SHA-256)")

        try:
            int(self.value, 16)
        except ValueError:
            raise ValueError("ContentHash must be valid hexadecimal string")

    @classmethod
    def compute(cls, content: str) -> Self:
        """
        Compute ContentHash from string content.

        Args:
            content: Text content to hash

        Returns:
            ContentHash instance with computed hash
        """
        if not content:
            raise ValueError("Cannot compute hash of empty content")

        hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()
        return cls(hash_value)

    @classmethod
    def compute_from_parts(cls, *parts: str) -> Self:
        """
        Compute ContentHash from multiple string parts.

        Useful for hashing composite content (e.g., highlight text + note).

        Args:
            *parts: String parts to concatenate and hash

        Returns:
            ContentHash instance
        """
        combined = "".join(parts)
        return cls.compute(combined)
```

**Test: `backend/tests/unit/domain/common/value_objects/test_content_hash.py`**

```python
import pytest
from backend.src.domain.common.value_objects.content_hash import ContentHash

def test_content_hash_compute():
    """ContentHash.compute() generates correct hash."""
    text = "This is a test highlight"
    hash1 = ContentHash.compute(text)
    hash2 = ContentHash.compute(text)

    # Same content produces same hash
    assert hash1 == hash2

    # Different content produces different hash
    hash3 = ContentHash.compute("Different text")
    assert hash1 != hash3

def test_content_hash_validation():
    """ContentHash validates hash format."""
    valid_hash = "a" * 64  # 64 hex chars
    ContentHash(valid_hash)  # Should work

    with pytest.raises(ValueError, match="64 character"):
        ContentHash("abc")  # Too short

    with pytest.raises(ValueError, match="hexadecimal"):
        ContentHash("z" * 64)  # Invalid hex

def test_content_hash_from_empty_content():
    """Cannot compute hash from empty content."""
    with pytest.raises(ValueError, match="empty content"):
        ContentHash.compute("")

def test_content_hash_compute_from_parts():
    """compute_from_parts() combines parts correctly."""
    hash1 = ContentHash.compute("Part1Part2Part3")
    hash2 = ContentHash.compute_from_parts("Part1", "Part2", "Part3")

    assert hash1 == hash2
```

**Action:**

1. Create `backend/src/domain/common/value_objects/content_hash.py`
2. Create tests
3. Run tests

---

### Step 1.4: Create Reading-Specific Value Objects

**File: `backend/src/domain/reading/value_objects/highlight_text.py`**

```python
"""
HighlightText value object with validation.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class HighlightText:
    """
    Validated highlight text with business constraints.

    Enforces:
    - Non-empty text
    - Maximum length limit
    """
    value: str

    MAX_LENGTH = 10000  # Reasonable limit for highlight text

    def __post_init__(self) -> None:
        stripped = self.value.strip()

        if not stripped:
            raise ValueError("Highlight text cannot be empty or whitespace")

        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(
                f"Highlight text exceeds maximum length of {self.MAX_LENGTH} characters"
            )

    def __len__(self) -> int:
        """Return length of text."""
        return len(self.value)

    def __str__(self) -> str:
        """Return the text value."""
        return self.value
```

**File: `backend/src/domain/reading/value_objects/__init__.py`**

```python
"""Reading module value objects."""
from .highlight_text import HighlightText

__all__ = ["HighlightText"]
```

**Test: `backend/tests/unit/domain/reading/value_objects/test_highlight_text.py`**

```python
import pytest
from backend.src.domain.reading.value_objects.highlight_text import HighlightText

def test_highlight_text_validation():
    """HighlightText validates content."""
    HighlightText("Valid highlight")  # OK

    with pytest.raises(ValueError, match="empty"):
        HighlightText("")

    with pytest.raises(ValueError, match="empty"):
        HighlightText("   ")  # Only whitespace

def test_highlight_text_max_length():
    """HighlightText enforces maximum length."""
    max_len = HighlightText.MAX_LENGTH

    HighlightText("a" * max_len)  # OK

    with pytest.raises(ValueError, match="exceeds maximum"):
        HighlightText("a" * (max_len + 1))
```

**Action:**

1. Create directory: `mkdir -p backend/src/domain/reading/value_objects`
2. Create the files
3. Create tests
4. Run tests

---

### Step 1.5: Update Common **init**.py Files

**File: `backend/src/domain/common/value_objects/__init__.py`**

```python
"""Common value objects shared across all modules."""
from .ids import (
    BookId,
    UserId,
    HighlightId,
    ChapterId,
    ReadingSessionId,
    HighlightTagId,
)
from .xpoint import XPoint, XPointRange
from .content_hash import ContentHash

__all__ = [
    "BookId",
    "UserId",
    "HighlightId",
    "ChapterId",
    "ReadingSessionId",
    "HighlightTagId",
    "XPoint",
    "XPointRange",
    "ContentHash",
]
```

**Action:**

1. Create `backend/src/domain/common/value_objects/__init__.py`
2. Verify imports work: `python -c "from backend.src.domain.common.value_objects import BookId, XPoint, ContentHash"`

---

### Phase 1 Checklist

- [x] Created all ID value objects with validation
- [x] Created XPoint and XPointRange
- [x] Created ContentHash with compute methods
- [ ] Created HighlightText
- [x] All value objects are immutable (`frozen=True`)
- [x] All value objects have validation in `__post_init__`
- [x] Unit tests pass (aim for >90% coverage)
- [x] Can import all value objects: `from backend.src.domain.common.value_objects import *`

**Verification:**

```bash
pytest backend/tests/unit/domain/ -v --cov=backend/src/domain --cov-report=term-missing
```

---

## PHASE 2: Domain Entities - Reading Module (8-12 hours)

### Goal

Create rich domain entities (Highlight, ReadingSession) with encapsulated business logic.

### Step 2.1: Create Highlight Entity

**File: `backend/src/domain/reading/entities/highlight.py`**

```python
"""
Highlight aggregate root.

Encapsulates all business rules for managing highlights.
"""
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional

from ...common.aggregate_root import AggregateRoot
from ...common.value_objects import (
    HighlightId,
    BookId,
    ChapterId,
    UserId,
    ContentHash,
    XPointRange,
)
from ..value_objects import HighlightText
from ...common.exceptions import DomainError


@dataclass
class Highlight(AggregateRoot[HighlightId]):
    """
    Highlight aggregate root.

    Represents a text highlight from an e-reader with optional annotations.

    Business Rules:
    - Cannot have empty text
    - Content hash is computed from text (for deduplication)
    - Soft deletion is supported (deleted_at timestamp)
    - Tags can be added/removed
    - Notes can be updated
    """
    # Identity
    id: HighlightId
    user_id: UserId
    book_id: BookId

    # Content
    text: HighlightText
    content_hash: ContentHash

    # Position (optional - may not always be available from e-reader)
    chapter_id: Optional[ChapterId] = None
    xpoints: Optional[XPointRange] = None
    page: Optional[int] = None

    # Annotation
    note: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: Optional[datetime] = None

    # Relationships
    _tag_ids: list[int] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Validate invariants after initialization."""
        if self.page is not None and self.page < 0:
            raise DomainError("Page number cannot be negative")

    # Query methods

    def is_deleted(self) -> bool:
        """Check if this highlight has been soft-deleted."""
        return self.deleted_at is not None

    def has_note(self) -> bool:
        """Check if this highlight has an associated note."""
        return self.note is not None and len(self.note.strip()) > 0

    def has_position_info(self) -> bool:
        """Check if this highlight has position information (xpoints or page)."""
        return self.xpoints is not None or self.page is not None

    # Command methods (state changes)

    def soft_delete(self) -> None:
        """
        Soft delete this highlight.

        Raises:
            DomainError: If highlight is already deleted
        """
        if self.is_deleted():
            raise DomainError(f"Highlight {self.id} is already deleted")

        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """
        Restore a soft-deleted highlight.

        Raises:
            DomainError: If highlight is not deleted
        """
        if not self.is_deleted():
            raise DomainError(f"Highlight {self.id} is not deleted")

        self.deleted_at = None

    def update_note(self, note: Optional[str]) -> None:
        """
        Update the note attached to this highlight.

        Args:
            note: New note text, or None to remove note
        """
        self.note = note.strip() if note else None

    def associate_with_chapter(self, chapter_id: ChapterId) -> None:
        """Associate this highlight with a chapter."""
        self.chapter_id = chapter_id

    # Factory methods

    @classmethod
    def create(
        cls,
        user_id: UserId,
        book_id: BookId,
        text: str,
        chapter_id: Optional[ChapterId] = None,
        xpoints: Optional[XPointRange] = None,
        page: Optional[int] = None,
        note: Optional[str] = None,
    ) -> "Highlight":
        """
        Factory method for creating a new highlight.

        Args:
            user_id: User who created the highlight
            book_id: Book this highlight belongs to
            text: Highlighted text
            chapter_id: Optional chapter reference
            xpoints: Optional XPoint range for precise position
            page: Optional page number
            note: Optional note/annotation

        Returns:
            New Highlight instance

        Raises:
            ValueError: If text is invalid
        """
        # Validate and wrap text
        highlight_text = HighlightText(text)

        # Compute content hash for deduplication
        content_hash = ContentHash.compute(text)

        return cls(
            id=HighlightId.generate(),  # Generate new ID
            user_id=user_id,
            book_id=book_id,
            text=highlight_text,
            content_hash=content_hash,
            chapter_id=chapter_id,
            xpoints=xpoints,
            page=page,
            note=note.strip() if note else None,
            created_at=datetime.now(UTC),
            deleted_at=None,
            _tag_ids=[],
        )

    @classmethod
    def create_with_id(
        cls,
        id: HighlightId,
        user_id: UserId,
        book_id: BookId,
        text: str,
        content_hash: ContentHash,
        created_at: datetime,
        chapter_id: Optional[ChapterId] = None,
        xpoints: Optional[XPointRange] = None,
        page: Optional[int] = None,
        note: Optional[str] = None,
        deleted_at: Optional[datetime] = None,
    ) -> "Highlight":
        """
        Factory method for reconstituting highlight from persistence.

        Used by repositories when loading from database.
        """
        return cls(
            id=id,
            user_id=user_id,
            book_id=book_id,
            text=HighlightText(text),
            content_hash=content_hash,
            chapter_id=chapter_id,
            xpoints=xpoints,
            page=page,
            note=note,
            created_at=created_at,
            deleted_at=deleted_at,
            _tag_ids=[],
        )
```

**Note:** The `HighlightId.generate()` method needs to be added to the EntityId base class:

**Update: `backend/src/domain/common/entity.py`**

Add this to the `EntityId` class:

```python
@classmethod
def generate(cls) -> Self:
    """
    Generate a new ID (placeholder - will be assigned by database).

    Returns a temporary ID of 0. The actual ID will be assigned
    by the database on insert and updated by the repository.
    """
    return cls(0)
```

---

### Step 2.2: Create HighlightTag Entity

**File: `backend/src/domain/reading/entities/highlight_tag.py`**

```python
"""
HighlightTag entity for categorizing highlights.
"""
from dataclasses import dataclass
from typing import Optional

from ...common.entity import Entity
from ...common.value_objects import HighlightTagId, BookId, UserId
from ...common.exceptions import DomainError


@dataclass
class HighlightTag(Entity[HighlightTagId]):
    """
    Tag for categorizing highlights within a book.

    Business Rules:
    - Tag names are scoped per book per user
    - Tags can optionally belong to groups
    """
    id: HighlightTagId
    user_id: UserId
    book_id: BookId
    name: str
    group_name: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.name or not self.name.strip():
            raise DomainError("Tag name cannot be empty")

    def rename(self, new_name: str) -> None:
        """
        Rename this tag.

        Args:
            new_name: New tag name

        Raises:
            DomainError: If new name is empty
        """
        if not new_name or not new_name.strip():
            raise DomainError("Tag name cannot be empty")

        self.name = new_name.strip()

    def set_group(self, group_name: Optional[str]) -> None:
        """Set or clear the group for this tag."""
        self.group_name = group_name.strip() if group_name else None
```

---

### Step 2.3: Create ReadingSession Entity

**File: `backend/src/domain/reading/entities/reading_session.py`**

```python
"""
ReadingSession aggregate root.
"""
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional

from ...common.aggregate_root import AggregateRoot
from ...common.value_objects import (
    ReadingSessionId,
    BookId,
    UserId,
    ContentHash,
    XPointRange,
)
from ...common.exceptions import DomainError


@dataclass
class ReadingSession(AggregateRoot[ReadingSessionId]):
    """
    Reading session aggregate root.

    Represents a continuous reading session recorded by an e-reader.

    Business Rules:
    - Start time must be before end time
    - Duration is computed from start/end times
    - Start page must be <= end page
    - Content hash prevents duplicate sessions
    """
    # Identity
    id: ReadingSessionId
    user_id: UserId
    book_id: BookId

    # Time tracking
    start_time: datetime
    end_time: datetime

    # Position tracking (optional)
    start_xpoint: Optional[XPointRange] = None
    start_page: Optional[int] = None
    end_page: Optional[int] = None

    # Metadata
    content_hash: ContentHash = field(init=True)
    device_id: Optional[str] = None
    ai_summary: Optional[str] = None

    # Related highlights (IDs only - don't load full services)
    _highlight_ids: list[int] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Validate invariants."""
        if self.end_time < self.start_time:
            raise DomainError("End time must be after start time")

        if self.start_page is not None and self.end_page is not None:
            if self.end_page < self.start_page:
                raise DomainError("End page must be >= start page")
            if self.start_page < 0 or self.end_page < 0:
                raise DomainError("Page numbers cannot be negative")

    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    @property
    def pages_read(self) -> int:
        """Calculate number of pages read."""
        if self.start_page is None or self.end_page is None:
            return 0
        return max(0, self.end_page - self.start_page)

    def set_ai_summary(self, summary: str) -> None:
        """Set AI-generated summary for this session."""
        self.ai_summary = summary.strip() if summary else None

    @classmethod
    def create(
        cls,
        user_id: UserId,
        book_id: BookId,
        start_time: datetime,
        end_time: datetime,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
        start_xpoint: Optional[XPointRange] = None,
        device_id: Optional[str] = None,
    ) -> "ReadingSession":
        """
        Factory method for creating a new reading session.

        Args:
            user_id: User who read
            book_id: Book that was read
            start_time: Session start time
            end_time: Session end time
            start_page: Optional starting page
            end_page: Optional ending page
            start_xpoint: Optional XPoint range
            device_id: Optional device identifier

        Returns:
            New ReadingSession instance
        """
        # Compute content hash for deduplication
        # Hash based on user, book, time range
        hash_content = f"{user_id.value}-{book_id.value}-{start_time.isoformat()}-{end_time.isoformat()}"
        content_hash = ContentHash.compute(hash_content)

        return cls(
            id=ReadingSessionId.generate(),
            user_id=user_id,
            book_id=book_id,
            start_time=start_time,
            end_time=end_time,
            start_page=start_page,
            end_page=end_page,
            start_xpoint=start_xpoint,
            content_hash=content_hash,
            device_id=device_id,
            ai_summary=None,
            _highlight_ids=[],
        )
```

---

### Step 2.4: Create Domain Exceptions

**File: `backend/src/domain/reading/exceptions.py`**

```python
"""Reading module domain exceptions."""
from ..common.exceptions import DomainError


class HighlightNotFound(DomainError):
    """Raised when a highlight cannot be found."""

    def __init__(self, highlight_id: int):
        super().__init__(f"Highlight {highlight_id} not found")


class HighlightAlreadyDeleted(DomainError):
    """Raised when trying to delete an already-deleted highlight."""

    def __init__(self, highlight_id: int):
        super().__init__(f"Highlight {highlight_id} is already deleted")


class DuplicateHighlight(DomainError):
    """Raised when attempting to create a duplicate highlight."""

    def __init__(self, content_hash: str):
        super().__init__(f"Duplicate highlight with hash {content_hash}")
```

---

### Step 2.5: Create Domain Service - Deduplication

**File: `backend/src/domain/reading/services/deduplication_service.py`**

```python
"""
Domain service for highlight deduplication logic.

This is a pure domain service with no infrastructure dependencies.
"""
from typing import List, Tuple, Set

from ..entities.highlight import Highlight
from ...common.value_objects import ContentHash


class HighlightDeduplicationService:
    """
    Domain service for identifying duplicate highlights.

    Deduplication is based on content_hash - highlights with
    the same hash are considered duplicates.
    """

    def find_duplicates(
        self,
        new_highlights: List[Highlight],
        existing_hashes: Set[ContentHash],
    ) -> Tuple[List[Highlight], List[Highlight]]:
        """
        Separate new highlights into unique and duplicates.

        Args:
            new_highlights: List of highlights to check
            existing_hashes: Set of content hashes that already exist

        Returns:
            Tuple of (unique_highlights, duplicate_highlights)
        """
        unique: List[Highlight] = []
        duplicates: List[Highlight] = []

        # Track hashes we've seen in this batch
        seen_in_batch: Set[ContentHash] = set(existing_hashes)

        for highlight in new_highlights:
            if highlight.content_hash in seen_in_batch:
                duplicates.append(highlight)
            else:
                unique.append(highlight)
                seen_in_batch.add(highlight.content_hash)

        return unique, duplicates

    def find_duplicate_pairs(
        self,
        highlights: List[Highlight],
    ) -> List[Tuple[Highlight, Highlight]]:
        """
        Find pairs of duplicates within a list of highlights.

        Useful for cleanup operations.

        Args:
            highlights: List of highlights to check

        Returns:
            List of duplicate pairs
        """
        hash_to_highlights: dict[ContentHash, List[Highlight]] = {}

        for highlight in highlights:
            if highlight.content_hash not in hash_to_highlights:
                hash_to_highlights[highlight.content_hash] = []
            hash_to_highlights[highlight.content_hash].append(highlight)

        pairs: List[Tuple[Highlight, Highlight]] = []
        for highlights_group in hash_to_highlights.values():
            if len(highlights_group) > 1:
                # Create pairs from duplicates
                for i in range(len(highlights_group) - 1):
                    pairs.append((highlights_group[i], highlights_group[i + 1]))

        return pairs
```

---

### Step 2.6: Create **init** files

**File: `backend/src/domain/reading/entities/__init__.py`**

```python
"""Reading module services."""
from .highlight import Highlight
from .highlight_tag import HighlightTag
from .reading_session import ReadingSession

__all__ = [
    "Highlight",
    "HighlightTag",
    "ReadingSession",
]
```

**File: `backend/src/domain/reading/services/__init__.py`**

```python
"""Reading module domain services."""
from .deduplication_service import HighlightDeduplicationService

__all__ = ["HighlightDeduplicationService"]
```

**File: `backend/src/domain/reading/__init__.py`**

```python
"""Reading module domain layer."""
from .entities import Highlight, HighlightTag, ReadingSession
from .services import HighlightDeduplicationService
from .value_objects import HighlightText

__all__ = [
    "Highlight",
    "HighlightTag",
    "ReadingSession",
    "HighlightDeduplicationService",
    "HighlightText",
]
```

---

### Step 2.7: Write Domain Entity Tests

**File: `backend/tests/unit/domain/reading/entities/test_highlight.py`**

```python
import pytest
from datetime import datetime, UTC

from backend.src.domain.reading.entities import Highlight
from backend.src.domain.common.value_objects import (
    HighlightId, UserId, BookId, ContentHash, XPoint, XPointRange
)
from backend.src.domain.common.exceptions import DomainError


class TestHighlightCreation:
    """Tests for Highlight.create() factory method."""

    def test_create_minimal_highlight(self):
        """Can create highlight with just required fields."""
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(10),
            text="This is a test highlight",
        )

        assert highlight.id == HighlightId(0)  # Temporary ID
        assert highlight.user_id == UserId(1)
        assert highlight.book_id == BookId(10)
        assert str(highlight.text) == "This is a test highlight"
        assert highlight.content_hash is not None
        assert highlight.chapter_id is None
        assert highlight.page is None
        assert highlight.note is None
        assert not highlight.is_deleted()

    def test_create_full_highlight(self):
        """Can create highlight with all optional fields."""
        xpoints = XPointRange(
            start=XPoint(0, "/body/p[1]", 0),
            end=XPoint(0, "/body/p[1]", 10),
        )

        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(10),
            text="Full highlight",
            xpoints=xpoints,
            page=42,
            note="Important!",
        )

        assert highlight.xpoints == xpoints
        assert highlight.page == 42
        assert highlight.note == "Important!"
        assert highlight.has_note()
        assert highlight.has_position_info()

    def test_create_computes_content_hash(self):
        """Content hash is computed from text."""
        text = "Test content for hashing"
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(10),
            text=text,
        )

        expected_hash = ContentHash.compute(text)
        assert highlight.content_hash == expected_hash

    def test_create_with_empty_text_fails(self):
        """Cannot create highlight with empty text."""
        with pytest.raises(ValueError, match="empty"):
            Highlight.create(
                user_id=UserId(1),
                book_id=BookId(10),
                text="",
            )


class TestHighlightDeletion:
    """Tests for highlight soft deletion."""

    def test_soft_delete(self):
        """Can soft delete a highlight."""
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(10),
            text="To be deleted",
        )

        assert not highlight.is_deleted()

        highlight.soft_delete()

        assert highlight.is_deleted()
        assert highlight.deleted_at is not None

    def test_cannot_delete_twice(self):
        """Cannot soft delete an already-deleted highlight."""
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(10),
            text="To be deleted",
        )

        highlight.soft_delete()

        with pytest.raises(DomainError, match="already deleted"):
            highlight.soft_delete()

    def test_restore(self):
        """Can restore a deleted highlight."""
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(10),
            text="To be deleted and restored",
        )

        highlight.soft_delete()
        assert highlight.is_deleted()

        highlight.restore()
        assert not highlight.is_deleted()
        assert highlight.deleted_at is None


class TestHighlightNotes:
    """Tests for note management."""

    def test_update_note(self):
        """Can update note on highlight."""
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(10),
            text="Highlighted text",
        )

        assert not highlight.has_note()

        highlight.update_note("This is important")

        assert highlight.has_note()
        assert highlight.note == "This is important"

    def test_remove_note(self):
        """Can remove note by setting to None."""
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(10),
            text="Highlighted text",
            note="Initial note",
        )

        highlight.update_note(None)

        assert not highlight.has_note()
        assert highlight.note is None
```

---

### Phase 2 Checklist

- [x] Created Highlight aggregate root with factory methods
- [x] Created HighlightTag entity
- [x] Created ReadingSession aggregate root
- [x] Created domain exceptions (HighlightNotFound, etc.)
- [x] Created HighlightDeduplicationService
- [x] All entities are dataclasses
- [x] State changes go through methods (not direct assignment)
- [x] Factory methods for creation (`create()`)
- [x] Reconstitution factory for repository (`create_with_id()`)
- [x] Unit tests pass with high coverage

**Verification:**

```bash
pytest backend/tests/unit/domain/reading/ -v --cov=backend/src/domain/reading
```

---

## Summary of Phase 1 & 2

### What You've Built

After completing these phases, you'll have:

1. **Strongly-typed value objects**: BookId, HighlightId, XPoint, ContentHash, HighlightText
2. **Rich domain entities**: Highlight, ReadingSession with encapsulated business logic
3. **Domain services**: HighlightDeduplicationService for pure domain logic
4. **Validation**: All business rules enforced at domain level
5. **Testability**: 100% testable without any infrastructure

### What's Next

**Phase 3**: Infrastructure layer

- Create ORM models (HighlightORM, ReadingSessionORM)
- Create mappers (HighlightMapper)
- Implement repository adapters (PostgresHighlightRepository)

**Phase 4**: Application layer

- Create use cases (UploadHighlightsUseCase)
- Create DTOs for input/output
- Wire up dependency injection

**Phase 5**: HTTP layer

- Refactor routers to use use cases
- Update FastAPI dependencies

---

## Tips for Implementation

1. **Work incrementally**: Complete one value object at a time, test it, then move to the next
2. **Test-driven**: Write tests first or immediately after each component
3. **Use type hints**: Leverage Python's type system - run `mypy backend/src/domain/reading/` to catch errors
4. **Keep domain pure**: No imports from `infrastructure/` or `application/` in domain layer
5. **Ask questions**: If business rules are unclear, document assumptions in code comments

---

## Common Pitfalls to Avoid

1. ❌ **Don't** put SQLAlchemy decorators on domain entities
2. ❌ **Don't** import from infrastructure/application in domain layer
3. ❌ **Don't** make value objects mutable (always use `frozen=True`)
4. ❌ **Don't** skip validation in `__post_init__`
5. ❌ **Don't** use primitive types (int, str) - wrap in value objects
6. ✅ **Do** keep domain logic in domain layer
7. ✅ **Do** use factory methods for object creation
8. ✅ **Do** raise domain exceptions for business rule violations
9. ✅ **Do** write comprehensive unit tests

Good luck with the migration! Remember: the goal is to learn DDD patterns, so take your time and really understand each piece before moving on.
