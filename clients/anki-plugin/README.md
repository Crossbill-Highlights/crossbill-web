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

## Configuration

### Initial Setup

1. In Anki, go to **Tools → Crossbill Settings**
2. Enter your Crossbill server URL (e.g., `http://localhost:8000`)
3. Click **Test Connection** to verify it works
4. Click **Save**

See [config.md](config.md) for detailed configuration documentation.

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

## Development

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

## Contributing

Contributions are welcome! Please see the main [Crossbill repository](https://github.com/Tumetsu/Crossbill) for contribution guidelines.

## License

See the main Crossbill repository for details.

## Support

For issues and feature requests, please visit the [Crossbill repository](https://github.com/Tumetsu/Crossbill/issues).

## Acknowledgments

- Built for [Anki](https://apps.ankiweb.net/), the powerful spaced repetition software
- Part of the [Crossbill](https://github.com/Tumetsu/Crossbill) project
