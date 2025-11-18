# Crossbill Anki Plugin - Implementation Plan

## Overview

The Crossbill Anki Plugin allows users to import highlights from their Crossbill server directly into Anki as flashcards. This plugin bridges the gap between reading and note-taking in Crossbill with spaced repetition learning in Anki.

## User Flow

1. User installs Crossbill Anki plugin
2. User configures plugin with Crossbill API credentials (server URL)
3. Inside Anki, user can:
   - Browse/search their Crossbill highlights in a dialog
   - Select highlights and convert them to Anki notes/cards
   - Plugin creates notes using existing or custom note types
   - Track which highlights have already been imported to avoid duplicates

## Technical Architecture

### Technology Stack
- **Language**: Python 3.9+ (Anki 2.1.50+ requirement)
- **UI Framework**: PyQt6/Qt6 (imported via `aqt.qt` for compatibility)
- **HTTP Client**: Python's built-in `urllib.request`
- **Storage**: Anki's config system (`config.json`) and Anki's database for tracking imported highlights

### Core Components

1. **API Client** (`api.py`)
   - Handles all HTTP communication with Crossbill backend
   - Endpoints to implement:
     - `GET /api/v1/highlights/books` - List books with highlight counts
     - `GET /api/v1/book/{book_id}` - Get book details with chapters and highlights
   - Error handling for network issues and API errors

2. **Configuration** (`config.json`, `settings.py`)
   - Server URL/host configuration
   - Default note type preferences
   - UI preferences (dialog size, last selected book, etc.)
   - Manage user preferences through Anki's config system

3. **UI Components** (`ui/`)
   - **Settings Dialog**: Configure server URL and preferences
   - **Highlights Browser Dialog**: Main dialog for browsing and selecting highlights
     - Book list view
     - Highlight list view with search/filter
     - Preview pane showing highlight details
     - Selection controls (checkboxes)
     - Import button
   - **Import Progress Dialog**: Show progress during import

4. **Note Creation** (`note_creator.py`)
   - Convert highlights to Anki notes
   - Support for basic note types:
     - **Basic**: Front (highlight text) / Back (book title, author, context)
     - **Cloze**: Highlight with cloze deletions (future enhancement)
   - Handle note type selection
   - Validate and sanitize highlight text for Anki

5. **Import Tracking** (`import_tracker.py`)
   - Track which highlights have been imported
   - Store mapping of Crossbill highlight IDs to Anki note IDs
   - Prevent duplicate imports
   - Use Anki's note fields or tags to mark imported highlights

6. **Main Plugin** (`__init__.py`)
   - Entry point for the plugin
   - Register menu actions
   - Initialize components
   - Handle plugin lifecycle

## Implementation Stages

### Stage 1: Foundation & Basic Setup ✓ (Current Focus)
**Goal**: Get the plugin infrastructure in place and display highlights

**Tasks**:
1. Create plugin directory structure
2. Set up `manifest.json` with plugin metadata
3. Create `config.json` with default settings
4. Implement `__init__.py` with basic menu action
5. Implement `api.py` with Crossbill API client
   - Get books list
   - Get book details with highlights
6. Create basic settings dialog for server configuration
7. Create highlights browser dialog (read-only)
   - Display books in a list
   - Display highlights from selected book
   - Show highlight details (text, page, notes, tags)
8. Test fetching and displaying highlights

**Deliverables**:
- Working plugin that can be loaded in Anki
- Configuration dialog for server URL
- Browsable highlights interface (view-only)
- No note creation yet - just browsing

### Stage 2: Note Creation & Import
**Goal**: Enable users to create Anki notes from highlights

**Tasks**:
1. Implement note type detection and selection
2. Create `note_creator.py` module
   - Basic note type: highlight → front, context → back
   - Handle book title, author, page number
3. Add import functionality to highlights browser
   - Selection mechanism (checkboxes)
   - "Import Selected" button
4. Implement basic import tracking
   - Mark imported highlights in UI
   - Prevent duplicate imports
5. Add deck selection for imported notes
6. Test note creation with various highlight types

**Deliverables**:
- Ability to select highlights and create Anki notes
- Basic note type support
- Duplicate prevention
- Deck selection

### Stage 3: Enhanced Features
**Goal**: Improve user experience and add power features

**Tasks**:
1. Add search/filter functionality to highlights browser
   - Filter by book
   - Search highlight text
   - Filter by tags
2. Implement batch import
   - Import all highlights from a book
   - Import all highlights from a chapter
3. Add custom note type mapping
   - Allow users to map highlight fields to custom note types
   - Save mapping preferences
4. Implement sync tracking
   - Track last sync time
   - Show only new highlights since last sync
5. Add export/import of plugin settings
6. Error handling and user feedback improvements

**Deliverables**:
- Advanced filtering and search
- Batch import capabilities
- Custom note type support
- Sync tracking

### Stage 4: Polish & Advanced Features
**Goal**: Production-ready plugin with advanced features

**Tasks**:
1. Implement cloze deletion support
   - Auto-detect potential cloze deletions
   - Manual cloze creation interface
2. Add tags management
   - Import Crossbill tags as Anki tags
   - Custom tag mapping
3. Implement bi-directional sync
   - Track note updates in Anki
   - Option to push updates back to Crossbill (future)
4. Add statistics and insights
   - Show import statistics
   - Highlight usage analytics
5. Performance optimizations
   - Caching
   - Lazy loading for large libraries
6. Comprehensive testing
7. Documentation and user guide
8. Prepare for AnkiWeb distribution

**Deliverables**:
- Production-ready plugin
- Complete documentation
- Ready for public release

## Data Models

### Crossbill API Models (from Obsidian plugin)
```python
Book {
    id: int
    title: str
    author: str | None
    isbn: str | None
    created_at: str
    updated_at: str
}

Highlight {
    id: int
    book_id: int
    chapter_id: int | None
    text: str
    chapter: str | None
    page: int | None
    note: str | None
    datetime: str
    highlight_tags: HighlightTag[]
    created_at: str
    updated_at: str
}

Chapter {
    id: int
    book_id: int
    name: str
    created_at: str
    updated_at: str
}
```

### Plugin Internal Models
```python
ImportedHighlight {
    highlight_id: int  # Crossbill highlight ID
    note_id: int       # Anki note ID
    imported_at: str   # Timestamp
}

PluginConfig {
    server_host: str
    default_deck: str
    default_note_type: str
    last_sync: str | None
    auto_tag: bool
}
```

## File Structure

```
clients/anki-plugin/
├── __init__.py              # Plugin entry point
├── manifest.json            # Plugin metadata
├── config.json              # Default configuration
├── config.md                # Config documentation for users
├── README.md                # User documentation
├── implementation_plan.md   # This file
├── api.py                   # Crossbill API client
├── settings.py              # Settings/preferences management
├── note_creator.py          # Note creation logic
├── import_tracker.py        # Import tracking
├── models.py                # Data models
├── ui/
│   ├── __init__.py
│   ├── settings_dialog.py  # Settings configuration dialog
│   ├── browser_dialog.py   # Main highlights browser
│   ├── progress_dialog.py  # Import progress
│   └── widgets.py          # Reusable UI components
└── tests/
    ├── __init__.py
    ├── test_api.py
    └── test_note_creator.py
```

## API Endpoints

### Crossbill Backend APIs (from existing implementation)
1. **GET /api/v1/highlights/books**
   - Query params: `limit`, `offset`
   - Returns: List of books with highlight counts

2. **GET /api/v1/book/{book_id}**
   - Returns: Book details with chapters and all highlights

## Note Type Formats

### Basic Note Type
- **Front**:
  ```
  [Highlight Text]
  ```

- **Back**:
  ```
  Book: [Book Title]
  Author: [Author]
  Chapter: [Chapter Name]
  Page: [Page Number]

  [User's note on highlight]

  Tags: [tag1, tag2, ...]
  ```

### Cloze Note Type (Stage 4)
- **Text**:
  ```
  {{c1::[highlighted portion]}}

  Source: [Book Title] by [Author]
  ```

## Configuration Schema

```json
{
  "server_host": "http://localhost:8000",
  "default_deck": "Default",
  "default_note_type": "Basic",
  "auto_tag": true,
  "tag_prefix": "crossbill",
  "last_sync": null,
  "ui_preferences": {
    "dialog_width": 900,
    "dialog_height": 600,
    "last_selected_book": null
  }
}
```

## Testing Strategy

1. **Unit Tests**
   - API client functionality
   - Note creation logic
   - Import tracking

2. **Integration Tests**
   - Full import workflow
   - Settings persistence
   - Error handling

3. **Manual Testing**
   - UI responsiveness
   - Large library performance
   - Various highlight formats

## Security Considerations

1. **API Authentication**: Currently using server URL only; consider adding API key support in future
2. **Input Sanitization**: Sanitize highlight text to prevent HTML/script injection in Anki cards
3. **CORS**: Backend must allow Anki desktop app (similar to Obsidian plugin)
4. **Error Messages**: Don't expose sensitive information in error messages

## Future Enhancements

1. **Cloud Sync**: Sync plugin settings across devices
2. **Advanced Filtering**: Complex queries on highlights
3. **Custom Templates**: User-defined note templates
4. **Image Support**: Import images from highlights
5. **Bi-directional Sync**: Push Anki edits back to Crossbill
6. **Mobile Support**: Consider AnkiDroid/AnkiMobile compatibility
7. **Scheduling Intelligence**: Suggest optimal review intervals based on highlight age

## Success Criteria

### Stage 1 (MVP)
- [x] Plugin loads successfully in Anki
- [x] User can configure server URL
- [x] User can browse highlights from Crossbill
- [x] UI is responsive and intuitive

### Stage 2
- [ ] User can create notes from highlights
- [ ] No duplicate imports
- [ ] Notes are properly formatted

### Stage 3
- [ ] Search and filter works efficiently
- [ ] Batch import handles large sets
- [ ] Custom note types supported

### Stage 4
- [ ] Ready for public release
- [ ] Documentation complete
- [ ] Positive user feedback

## Timeline Estimate

- **Stage 1**: 2-3 days (Current focus)
- **Stage 2**: 3-4 days
- **Stage 3**: 4-5 days
- **Stage 4**: 5-7 days

**Total**: ~3-4 weeks for full implementation

## Dependencies

- Anki 2.1.50 or higher
- Python 3.9 or higher
- PyQt6 (bundled with Anki)
- Crossbill backend server (accessible via HTTP)

## Resources

- [Anki Add-on Development Guide](https://addon-docs.ankiweb.net/)
- [Anki Source Code](https://github.com/ankitects/anki)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Crossbill API Documentation](../README.md)

## Notes

- This plugin follows similar architecture to the Obsidian plugin for consistency
- Focus on simplicity and reliability over feature richness in early stages
- User feedback will drive feature prioritization in later stages
- Consider creating a demo video for Stage 2 to gather early feedback
