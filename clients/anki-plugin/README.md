# Crossbill Anki Plugin

Import your reading highlights from Crossbill server into Anki as flashcards for spaced repetition learning.

## Features

- 🔍 Search and filter highlights (text, tags, chapters) ✓
- 📚 View highlights organized by books and chapters ✓
- 🎴 Convert highlights into Anki flashcards ✓
- ⚙️ Configurable server connection ✓
- 🏷️ Auto-tagging with book metadata ✓
- ✅ Duplicate detection and prevention ✓
- 🎯 Custom deck and note type selection ✓
- ⚡ Batch import entire books or chapters ✓
- 💤 Suspend cards on import (review before studying) ✓

## Current Status

**Stage 1: Foundation & Basic Setup** ✓
**Stage 2: Note Creation & Import** ✓
**Stage 3: Advanced Filtering & Batch Import** ✓

The plugin currently supports:
- ✅ Browsing books from your Crossbill server
- ✅ Viewing highlights with full details (text, notes, tags, page numbers)
- ✅ Configurable server URL and connection testing
- ✅ Creating Anki notes from highlights
- ✅ Multi-select highlights with checkboxes
- ✅ Deck and note type selection
- ✅ Duplicate detection (prevents re-importing)
- ✅ Auto-tagging with book, author, and highlight tags
- ✅ Visual import status (shows which highlights are imported)
- ✅ Batch import with progress tracking
- ✅ **Search highlights by text** (searches both highlight and notes)
- ✅ **Filter by tag** (dropdown of all unique tags)
- ✅ **Filter by chapter** (dropdown of all chapters)
- ✅ **Import all from book** (batch import entire book)
- ✅ **Import all from chapter** (batch import selected chapter)

**Coming Soon** (Stage 4):
- Cloze deletion support
- Advanced tag management
- Performance optimizations
- Comprehensive documentation

## Installation

### For Development/Testing

1. Clone or download the Crossbill repository

2. Locate your Anki add-ons directory:
   - **Windows**: `%APPDATA%\Anki2\addons21\`
   - **Mac**: `~/Library/Application Support/Anki2/addons21/`
   - **Linux**: `~/.local/share/Anki2/addons21/`

3. Create a symbolic link or copy the plugin folder:
   ```bash
   # Option 1: Symbolic link (recommended for development)
   ln -s /path/to/Crossbill/clients/anki-plugin /path/to/Anki2/addons21/crossbill

   # Option 2: Copy the folder
   cp -r /path/to/Crossbill/clients/anki-plugin /path/to/Anki2/addons21/crossbill
   ```

4. Restart Anki

5. The plugin should appear in Tools → Add-ons

### From AnkiWeb (Future)

Once published to AnkiWeb:
1. Open Anki → Tools → Add-ons → Get Add-ons
2. Enter the add-on code
3. Restart Anki

## Configuration

### Initial Setup

1. In Anki, go to **Tools → Crossbill Settings**
2. Enter your Crossbill server URL (e.g., `http://localhost:8000`)
3. Click **Test Connection** to verify it works
4. Click **Save**

### Configuration Options

Edit configuration via **Tools → Add-ons → Crossbill → Config** or **Tools → Crossbill Settings**:

- **server_host**: URL of your Crossbill server
- **default_deck**: Default Anki deck for imported notes
- **default_note_type**: Default note type to use (e.g., "Basic")
- **auto_tag**: Automatically add tags to imported notes
- **tag_prefix**: Prefix for auto-generated tags (default: "crossbill")
- **suspend_on_import**: Suspend imported cards so they don't appear in reviews until you manually unsuspend them (default: true)

See [config.md](config.md) for detailed configuration documentation.

## Usage

### Browse Highlights

1. Go to **Tools → Browse Crossbill Highlights**
2. Select a book from the books list at the top
3. Browse highlights in the middle section
4. Click on a highlight to see full details in the bottom section

### Search and Filter Highlights

1. Select a book to load its highlights
2. Use the **Search** box to filter highlights by text (searches highlight text and your notes)
3. Use the **Tag** dropdown to filter by specific tags
4. Use the **Chapter** dropdown to filter by chapter
5. Click **Clear Filters** to reset all filters
6. Status bar shows filtered count (e.g., "Showing 5 of 20 highlights (filtered)")

**Tips:**
- Filters work together (search AND tag AND chapter)
- Search is case-insensitive
- Filters persist until you change books or clear them

### Create Flashcards (Individual Import)

1. Open the highlights browser (**Tools → Browse Crossbill Highlights**)
2. Select a book to see its highlights
3. (Optional) Use search/filters to find specific highlights
4. Use checkboxes to select highlights you want to import:
   - Click individual checkboxes, or
   - Use "Select All" to select all (currently visible) highlights, or
   - Use "Deselect All" to clear selections
5. Choose your target **Deck** from the dropdown
6. Choose your **Note Type** (e.g., "Basic", "Basic (and reversed card)")
7. Click **Import Selected**
8. Confirm the import
9. Wait for the import to complete (progress dialog will show)

### Batch Import

Import many highlights at once without selecting them individually:

**Import All from Book:**
1. Select a book
2. Choose your **Deck** and **Note Type**
3. Click **Import All from Book**
4. Review the confirmation (shows new vs already imported counts)
5. Click "Yes" to import all highlights from the book

**Import All from Chapter:**
1. Select a book
2. Select a chapter from the **Chapter** filter dropdown
3. Choose your **Deck** and **Note Type**
4. Click **Import All from Chapter**
5. Review the confirmation
6. Click "Yes" to import all highlights from that chapter

**Notes:**
- Already imported highlights are marked with "✓ Imported" and grayed out
- Duplicate detection prevents re-importing the same highlight
- Each highlight creates one note with:
  - **Front**: The highlight text
  - **Back**: Book title, author, chapter, page, and your notes
- Tags are automatically added (book name, author, Crossbill tags)
- You can import to any deck and use any note type in your collection
- Batch import shows progress dialog and detailed statistics
- **By default, imported cards are suspended** - they won't appear in your reviews until you unsuspend them. This lets you review and edit cards before studying. You can disable this in Settings.

## Prerequisites

### Crossbill Server

You need a running Crossbill server with highlights. The server must be accessible from your computer where Anki is installed.

### CORS Configuration

The Crossbill backend must allow CORS requests from Anki. By default, the backend allows all origins (`*`), which works for desktop applications.

If you need to restrict CORS:
```bash
# In backend/.env
CORS_ORIGINS=*  # Recommended for desktop apps
```

## Troubleshooting

### "Failed to connect to server"

1. Check that your Crossbill server is running
2. Verify the server URL in settings (include `http://` or `https://`)
3. Check firewall settings
4. Try the **Test Connection** button in settings

### "No books found"

1. Make sure you have books with highlights in your Crossbill library
2. Check that the API endpoints are working:
   - `http://your-server:8000/api/v1/highlights/books`
3. Check server logs for errors

### Plugin doesn't appear in Anki

1. Verify the plugin is in the correct add-ons directory
2. Check the folder name is `crossbill`
3. Restart Anki completely
4. Check **Tools → Add-ons** for error messages

### Import errors (for development)

If you see Python import errors:
1. Make sure all `.py` files are in the plugin directory
2. Check that `__init__.py` exists in the plugin root and `ui/` folder
3. Restart Anki to reload the plugin

## Development

### Project Structure

```
clients/anki-plugin/
├── __init__.py              # Plugin entry point
├── manifest.json            # Plugin metadata
├── config.json              # Default configuration
├── config.md                # Config documentation
├── README.md                # This file
├── implementation_plan.md   # Development plan
├── api.py                   # Crossbill API client
├── models.py                # Data models
└── ui/
    ├── __init__.py
    ├── settings_dialog.py   # Settings dialog
    └── browser_dialog.py    # Highlights browser
```

### Testing

1. Make changes to the plugin code
2. Restart Anki to reload the plugin
3. Test functionality through the UI
4. Check Anki's console for error messages (Tools → Add-ons → View Files)

### Debugging

Enable Anki's debug console:
1. Help → About → Copy Debug Info (to see Python version and Anki version)
2. Tools → Add-ons → [Select Crossbill] → View Files (to see plugin directory)
3. Check `~/.local/share/Anki2/addons21/crossbill/` for log files

## API Reference

This plugin uses the Crossbill API:

- **GET /api/v1/highlights/books**: List books with highlight counts
- **GET /api/v1/book/{book_id}**: Get book with chapters and highlights

## Roadmap

See [implementation_plan.md](implementation_plan.md) for the complete development roadmap.

### Stage 2: Note Creation ✓
- [x] Create Anki notes from highlights
- [x] Basic note type support
- [x] Duplicate prevention
- [x] Deck selection

### Stage 3: Enhanced Features ✓
- [x] Search and filter highlights (text, tags, chapters)
- [x] Batch import entire books/chapters
- [x] Chapter information display

### Stage 4: Polish (Next)
- [ ] Cloze deletion support
- [ ] Advanced tag management
- [ ] Custom note type field mapping
- [ ] Performance optimizations
- [ ] Comprehensive documentation

## Contributing

Contributions are welcome! Please see the main [Crossbill repository](https://github.com/Tumetsu/Crossbill) for contribution guidelines.

## License

MIT License - See the main Crossbill repository for details.

## Support

For issues and feature requests, please visit the [Crossbill repository](https://github.com/Tumetsu/Crossbill/issues).

## Acknowledgments

- Built for [Anki](https://apps.ankiweb.net/), the powerful spaced repetition software
- Part of the [Crossbill](https://github.com/Tumetsu/Crossbill) project
- Inspired by the Crossbill Obsidian plugin

## Changelog

### v0.3.0 (Stage 3) - Current

- ✅ **Search functionality** - Filter highlights by text (searches highlight text and notes)
- ✅ **Tag filter** - Dropdown of all unique tags from current book
- ✅ **Chapter filter** - Dropdown of all chapters with highlights
- ✅ **Clear Filters button** - Reset all filters at once
- ✅ **Import All from Book** - Batch import all highlights from current book
- ✅ **Import All from Chapter** - Batch import all highlights from selected chapter
- ✅ **Smart batch import** - Shows new vs already imported counts before confirming
- ✅ **Filter status** - Shows "Showing X of Y highlights (filtered)" in status bar
- ✅ **Real-time filtering** - Filters update as you type/select
- ✅ **Suspend on import** - Cards are suspended by default so they don't appear in reviews until you're ready (configurable)
- ✅ **Smart button states** - Import buttons intelligently enable/disable based on current selection
- ✅ **Improved UI layout** - Import controls moved to bottom, better window management for tiling WMs

### v0.2.0 (Stage 2)

- ✅ Create Anki notes from highlights
- ✅ Multi-select highlights with checkboxes
- ✅ Deck and note type selection
- ✅ Duplicate detection and prevention
- ✅ Auto-tagging (book, author, highlight tags)
- ✅ Visual import status (shows imported highlights)
- ✅ Batch import with progress tracking
- ✅ Support for Basic and custom note types
- ✅ Import statistics (created/skipped/failed)

### v0.1.0 (Stage 1)

- ✅ Initial plugin structure
- ✅ Server configuration dialog
- ✅ Browse books and highlights
- ✅ View highlight details
- ✅ Connection testing
- ✅ Vertical layout with full-width sections

### Planned for v0.4.0 (Stage 4)

- Cloze deletion support
- Advanced tag management
- Custom note type field mapping
- Performance optimizations
