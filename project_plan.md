# Inkwell Highlights Upload - Implementation Plan

## Project Overview

Create a KOReader plugin and backend API to upload highlights from KOReader to the Inkwell database for later editing and management.

**Scope**: Backend API + KOReader Plugin (frontend excluded from this phase)

**Key Decisions**:
- No authentication initially (add later)
- Normalized database with Books and Highlights tables
- Current book sync only (batch sync later)
- Server-side deduplication based on (book_id, text, datetime)

---

## Phase 1: Database Schema & Migrations

### 1.1 Update Database Models (`backend/inkwell/models.py`)

**Add Book Model**:
```python
class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(500))
    isbn: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    highlights: Mapped[list["Highlight"]] = relationship(back_populates="book")
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="chapter")
```

**Update Highlight Model**:
```python
class Highlight(Base):
    __tablename__ = "highlights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    chapter: Mapped[str | None] = mapped_column(String(500))
    page: Mapped[int | None]
    note: Mapped[str | None] = mapped_column(Text)
    datetime: Mapped[str] = mapped_column(String(50))  # KOReader datetime string
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    book: Mapped["Book"] = relationship(back_populates="highlights")

    __table_args__ = (
        UniqueConstraint('book_id', 'text', 'datetime', name='uq_highlight_dedup'),
    )
```

**Update Chapter Model**:
```python
class Chapter(Base):
    __tablename__ = "chapters"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    name: Mapped[str | None] = mapped_column(String(500))
    note: Mapped[str | None] = mapped_column(Text)
    datetime: Mapped[str] = mapped_column(String(50))  # KOReader datetime string
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    book: Mapped["Book"] = relationship(back_populates="chapters")

    __table_args__ = (
        UniqueConstraint('book_id', 'name', name='uq_chapter_dedup'),
    )
```

### 1.2 Configure Alembic (`backend/alembic/env.py`)

Uncomment the target_metadata line:
```python
from inkwell.models import Base
target_metadata = Base.metadata
```

### 1.3 Create and Run Migration

```bash
cd backend
poetry run alembic revision --autogenerate -m "Add books, chapters table and update highlights"
poetry run alembic upgrade head
```

---

## Phase 2: Backend API Implementation

### 2.1 Create Pydantic Schemas (`backend/inkwell/schemas.py`)

**New file**: Create schemas for request/response validation

```python
from pydantic import BaseModel, Field
from datetime import datetime

class BookBase(BaseModel):
    title: str
    author: str | None = None
    isbn: str | None = None

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    
class ChapterBase(BaseModel):
   name: str
   note: str | None = None
   book: Book

class Chapter(ChapterBase):
   id: int
   created_at: datetime
   updated_at: datetime

   model_config = {"from_attributes": True}

class HighlightBase(BaseModel):
    text: str
    chapter: str | None = None
    page: int | None = None
    note: str | None = None
    datetime: str  # KOReader datetime format

class HighlightCreate(HighlightBase):
    pass

class Highlight(HighlightBase):
    id: int
    book_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class HighlightUploadRequest(BaseModel):
    book: BookCreate
    highlights: list[HighlightCreate]

class HighlightUploadResponse(BaseModel):
    success: bool
    message: str
    book_id: int
    highlights_created: int
    highlights_skipped: int  # duplicates
```

### 2.2 Implement CRUD Operations (`backend/inkwell/crud.py`)

**New file**: Database operations

```python
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from inkwell import models, schemas

def get_or_create_book(db: Session, book_data: schemas.BookCreate) -> models.Book:
    """Get existing book by file_path or create new one."""
    book = db.query(models.Book).filter(
        models.Book.file_path == book_data.file_path
    ).first()

    if book:
        # Update metadata in case it changed
        book.title = book_data.title
        book.author = book_data.author
        book.isbn = book_data.isbn
        db.commit()
        db.refresh(book)
        return book

    # Create new book
    book = models.Book(**book_data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

def create_highlight_if_not_exists(
    db: Session,
    book_id: int,
    highlight_data: schemas.HighlightCreate
) -> tuple[models.Highlight | None, bool]:
    """
    Create highlight if it doesn't exist.
    Returns (highlight, created) tuple.
    """
    try:
        highlight = models.Highlight(
            book_id=book_id,
            **highlight_data.model_dump()
        )
        db.add(highlight)
        db.commit()
        db.refresh(highlight)
        return highlight, True
    except IntegrityError:
        # Duplicate - unique constraint violated
        db.rollback()
        return None, False

def bulk_create_highlights(
    db: Session,
    book_id: int,
    highlights_data: list[schemas.HighlightCreate]
) -> tuple[int, int]:
    """
    Bulk create highlights with deduplication.
    Returns (created_count, skipped_count).
    """
    created = 0
    skipped = 0

    for highlight_data in highlights_data:
        _, was_created = create_highlight_if_not_exists(db, book_id, highlight_data)
        if was_created:
            created += 1
        else:
            skipped += 1

    return created, skipped
```

### 2.3 Create API Endpoint (`backend/inkwell/routers/highlights.py`)

**New file**: API routes for highlights

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from inkwell import schemas, crud
from inkwell.database import get_db

router = APIRouter(prefix="/highlights", tags=["highlights"])

@router.post("/upload", response_model=schemas.HighlightUploadResponse)
def upload_highlights(
    request: schemas.HighlightUploadRequest,
    db: Session = Depends(get_db)
) -> schemas.HighlightUploadResponse:
    """
    Upload highlights from KOReader.

    Creates or updates book record and adds highlights with deduplication.
    """
    try:
        # Get or create book
        book = crud.get_or_create_book(db, request.book)

        # Bulk create highlights
        created, skipped = crud.bulk_create_highlights(
            db,
            book.id,
            request.highlights
        )

        return schemas.HighlightUploadResponse(
            success=True,
            message=f"Successfully synced highlights for '{book.title}'",
            book_id=book.id,
            highlights_created=created,
            highlights_skipped=skipped
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
```

### 2.4 Register Router (`backend/inkwell/main.py`)

Update main.py to include the highlights router:

```python
from inkwell.routers import highlights

# Add to create_app() function
app.include_router(highlights.router, prefix="/api/v1")
```

### 2.5 Error Handling & Logging

Add logging to CRUD operations and endpoints:
```python
import logging

logger = logging.getLogger(__name__)

# In endpoints/CRUD functions
logger.info(f"Creating book: {book_data.title}")
logger.error(f"Failed to create highlight: {e}")
```

---

## Phase 3: KOReader Plugin Development
You can see examples fo koreader highlights file in `clients/koreader-plugin/examples/metadata.epub.lua`

### 3.1 Plugin Structure

Create directory: `clients/koreader-plugin/inkwell.koplugin/`

**File structure**:
```
inkwell.koplugin/
├── _meta.lua           # Plugin metadata
├── main.lua            # Main plugin logic
└── README.md           # Installation & usage instructions
```

### 3.2 Plugin Metadata (`_meta.lua`)

```lua
local _ = require("gettext")
return {
    name = "inkwell",
    fullname = _("Inkwell Sync"),
    description = _([[Syncs your highlights to Inkwell server for editing and management.]]),
}
```

### 3.3 Main Plugin Logic (`main.lua`)

```lua
local WidgetContainer = require("ui/widget/container")
local UIManager = require("ui/uimanager")
local InfoMessage = require("ui/widget/infomessage")
local InputDialog = require("ui/widget/inputdialog")
local DocSettings = require("docsettings")
local https = require("ssl.https")
local ltn12 = require("ltn12")
local socketutil = require("socketutil")
local JSON = require("json")
local _ = require("gettext")

local InkwellSync = WidgetContainer:extend{
    name = "inkwell",
    is_doc_only = true,  -- Only show when document is open
}

function InkwellSync:init()
    -- Load settings
    self.settings = G_reader_settings:readSetting("inkwell_sync") or {
        api_url = "http://localhost:8000/api/v1/highlights/upload",
    }

    self.ui.menu:registerToMainMenu(self)
end

function InkwellSync:addToMainMenu(menu_items)
    menu_items.inkwell_sync = {
        text = _("Inkwell Sync"),
        sub_item_table = {
            {
                text = _("Sync Current Book"),
                callback = function()
                    self:syncCurrentBook()
                end,
            },
            {
                text = _("Configure Server"),
                callback = function()
                    self:configureServer()
                end,
            },
        },
    }
end

function InkwellSync:configureServer()
    local input_dialog
    input_dialog = InputDialog:new{
        title = _("Inkwell Server URL"),
        input = self.settings.api_url,
        input_type = "text",
        buttons = {
            {
                {
                    text = _("Cancel"),
                    callback = function()
                        UIManager:close(input_dialog)
                    end,
                },
                {
                    text = _("Save"),
                    is_enter_default = true,
                    callback = function()
                        self.settings.api_url = input_dialog:getInputText()
                        G_reader_settings:saveSetting("inkwell_sync", self.settings)
                        UIManager:close(input_dialog)
                        UIManager:show(InfoMessage:new{
                            text = _("Server URL saved"),
                        })
                    end,
                },
            },
        },
    }
    UIManager:show(input_dialog)
    input_dialog:onShowKeyboard()
end

function InkwellSync:syncCurrentBook()
    UIManager:show(InfoMessage:new{
        text = _("Syncing highlights..."),
        timeout = 2,
    })

    -- Get book metadata
    local book_props = self.ui.doc_props
    local doc_path = self.ui.document.file

    local book_data = {
        title = book_props.display_title or self:getFilename(doc_path),
        author = book_props.authors or "Unknown",
        isbn = book_props.isbn or nil,
        file_path = doc_path,
    }

    -- Get highlights
    local highlights = self:getHighlights(doc_path)

    if not highlights or #highlights == 0 then
        UIManager:show(InfoMessage:new{
            text = _("No highlights found in this book"),
        })
        return
    end

    -- Send to server
    self:sendToServer(book_data, highlights)
end

function InkwellSync:getHighlights(doc_path)
    local doc_settings = DocSettings:open(doc_path)
    local results = {}

    -- Try modern annotations format first
    local annotations = doc_settings:readSetting("annotations")
    if annotations then
        for _, annotation in ipairs(annotations) do
            table.insert(results, {
                text = annotation.text or "",
                note = annotation.note or "",
                datetime = annotation.datetime or "",
                page = annotation.page,
                chapter = annotation.chapter or "",
            })
        end
        return results
    end

    -- Fallback to legacy format
    local highlights = doc_settings:readSetting("highlight")
    if not highlights then
        return nil
    end

    local bookmarks = doc_settings:readSetting("bookmarks") or {}

    for page, items in pairs(highlights) do
        for _, item in ipairs(items) do
            local note = ""

            -- Find matching bookmark for note
            for _, bookmark in pairs(bookmarks) do
                if bookmark.datetime == item.datetime then
                    note = bookmark.text or ""
                    break
                end
            end

            table.insert(results, {
                text = item.text or "",
                note = note,
                datetime = item.datetime or "",
                page = item.page,
                chapter = item.chapter or "",
            })
        end
    end

    return results
end

function InkwellSync:sendToServer(book_data, highlights)
    local payload = {
        book = book_data,
        highlights = highlights,
    }

    local body_json = JSON.encode(payload)
    local response_body = {}

    local request = {
        url = self.settings.api_url,
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json",
            ["Accept"] = "application/json",
            ["Content-Length"] = tostring(#body_json),
        },
        source = ltn12.source.string(body_json),
        sink = ltn12.sink.table(response_body),
    }

    local code, headers, status = socket.skip(1, https.request(request))
    socketutil:reset_timeout()

    if code == 200 then
        local response_text = table.concat(response_body)
        local response_data = JSON.decode(response_text)

        UIManager:show(InfoMessage:new{
            text = string.format(
                _("Synced successfully!\n%d new, %d duplicates"),
                response_data.highlights_created or 0,
                response_data.highlights_skipped or 0
            ),
            timeout = 3,
        })
    else
        UIManager:show(InfoMessage:new{
            text = _("Sync failed: ") .. tostring(code),
            timeout = 3,
        })
    end
end

function InkwellSync:getFilename(path)
    return path:match("^.+/(.+)$") or path
end

return InkwellSync
```

### 3.4 Plugin README (`README.md`)

```markdown
# Inkwell KOReader Plugin

Syncs your KOReader highlights to your Inkwell server.

## Installation

1. Copy the `inkwell.koplugin` directory to your KOReader plugins folder:
   - **Device**: `koreader/plugins/`
   - **Desktop**: `.config/koreader/plugins/` (Linux/Mac) or `%APPDATA%\koreader\plugins\` (Windows)

2. Restart KOReader

3. Open any book and go to: Menu → Inkwell Sync → Configure Server

4. Enter your Inkwell server URL (e.g., `http://192.168.1.100:8000/api/v1/highlights/upload`)

## Usage

1. Open a book with highlights
2. Menu → Inkwell Sync → Sync Current Book
3. View your synced highlights on your Inkwell server

## Requirements

- KOReader version 2021.04 or later
- Network connection to your Inkwell server
```

---

## Phase 4: Testing & Documentation

### 4.1 Backend Tests (`backend/tests/test_highlights.py`)

**New file**: Test the highlights upload endpoint

```python
import pytest
from fastapi.testclient import TestClient
from inkwell.main import app
from tests.conftest import TestingSessionLocal

client = TestClient(app)

def test_upload_highlights():
    payload = {
        "book": {
            "title": "Test Book",
            "author": "Test Author",
            "file_path": "/path/to/book.epub"
        },
        "highlights": [
            {
                "text": "Test highlight",
                "chapter": "Chapter 1",
                "page": 10,
                "note": "Test note",
                "datetime": "2024-01-15 14:30:22"
            }
        ]
    }

    response = client.post("/api/v1/highlights/upload", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["highlights_created"] == 1
    assert data["highlights_skipped"] == 0

def test_upload_duplicate_highlights():
    # Upload same highlight twice
    payload = {
        "book": {
            "title": "Test Book",
            "author": "Test Author",
            "file_path": "/path/to/book.epub"
        },
        "highlights": [
            {
                "text": "Duplicate highlight",
                "datetime": "2024-01-15 15:00:00"
            }
        ]
    }

    # First upload
    response1 = client.post("/api/v1/highlights/upload", json=payload)
    assert response1.json()["highlights_created"] == 1

    # Second upload (should skip duplicate)
    response2 = client.post("/api/v1/highlights/upload", json=payload)
    assert response2.json()["highlights_created"] == 0
    assert response2.json()["highlights_skipped"] == 1
```

### 4.2 Plugin Testing

**Manual testing steps**:
1. Install plugin in KOReader emulator (`kodev run`)
2. Open sample book with highlights
3. Test sync functionality
4. Verify data appears in database
5. Test error cases (network failure, invalid URL)

### 4.3 Documentation

**Update `backend/README.md`**:
- Add API endpoint documentation
- Add example curl commands
- Add KOReader plugin installation instructions

**Example curl command**:
```bash
curl -X POST http://localhost:8000/api/v1/highlights/upload \
  -H "Content-Type: application/json" \
  -d '{
    "book": {
      "title": "Example Book",
      "author": "John Doe",
      "file_path": "/books/example.epub"
    },
    "highlights": [
      {
        "text": "Highlighted text",
        "chapter": "Chapter 1",
        "page": 42,
        "note": "My note",
        "datetime": "2024-01-15 14:30:22"
      }
    ]
  }'
```

---

## Implementation Checklist

### Backend
- [ ] Update `models.py` with Book and updated Highlight models
- [ ] Configure Alembic in `env.py`
- [ ] Create and run database migration
- [ ] Create `schemas.py` with Pydantic models
- [ ] Create `crud.py` with database operations
- [ ] Create `routers/highlights.py` with upload endpoint
- [ ] Update `main.py` to include router
- [ ] Add logging
- [ ] Write tests in `test_highlights.py`
- [ ] Run tests: `poetry run pytest`
- [ ] Update README with API docs

### KOReader Plugin
- [ ] Create `clients/koreader/inkwell.koplugin/` directory
- [ ] Create `_meta.lua`
- [ ] Create `main.lua` with sync logic
- [ ] Create `README.md` with installation instructions
- [ ] Test in KOReader emulator
- [ ] Test with real device (optional)
- [ ] Handle both legacy and modern highlight formats
- [ ] Test error scenarios

### Integration Testing
- [ ] Start backend server
- [ ] Configure plugin with server URL
- [ ] Sync highlights from test book
- [ ] Verify in database
- [ ] Test duplicate handling
- [ ] Test with books containing no highlights
- [ ] Test network error handling

---

## Future Enhancements (Post-MVP)

1. **Authentication**
   - User registration/login
   - JWT tokens
   - Associate highlights with users

2. **Batch Sync**
   - Sync all books with highlights
   - Progress indicators
   - Background sync

3. **Incremental Sync**
   - Track last sync time
   - Only upload new/modified highlights
   - Conflict resolution

4. **Enhanced Metadata**
   - Extract ISBN from ebooks
   - Cover images
   - Reading progress

5. **Frontend**
   - View all highlights
   - Edit/delete highlights
   - Search and filter
   - Export options

---

## Technical Notes

### Database Deduplication Strategy
Using unique constraint on `(book_id, text, datetime)` ensures:
- Same text at same time = duplicate (skipped)
- Same text at different time = different highlight (allowed)
- Handles re-sync gracefully without creating duplicates

### KOReader Compatibility
- Plugin supports both legacy and modern annotation formats
- Uses `is_doc_only = true` to only show when book is open
- HTTP requests use ssl.https for secure connections
- Error handling with user-friendly messages

### Performance Considerations
- Bulk insert with individual dedup checks (can optimize later)
- Database indexes on foreign keys and file_path
- Could add batch endpoint for syncing multiple books in future
