# Crossbill Plugin for Obsidian

This plugin allows you to import highlights from your Crossbill server directly into your Obsidian notes.

## Features

- Browse books from your Crossbill library
- Select chapters from your books
- Import all highlights from a chapter into your current note
- Configurable server host

## Installation

### For Development

1. Clone this repository or copy the plugin folder to your Obsidian vault's plugins directory:
   ```bash
   cd /path/to/your/vault/.obsidian/plugins/
   cp -r /path/to/Crossbill/clients/obsidian-plugin ./crossbill
   ```

2. Install dependencies:
   ```bash
   cd crossbill
   npm install
   ```

3. Build the plugin:
   ```bash
   npm run build
   ```

4. Enable the plugin in Obsidian:
   - Open Settings → Community Plugins
   - Disable "Safe Mode" if it's enabled
   - Click "Browse" and find "Crossbill" in the list
   - Enable the plugin

### From Release (Future)

Once this plugin is published:
1. Open Settings → Community Plugins
2. Click "Browse" and search for "Crossbill"
3. Click Install, then Enable

## Prerequisites

### Backend CORS Configuration

The Crossbill backend must allow CORS requests from the Obsidian plugin. By default, the backend allows all origins (`*`), which works for desktop applications like Obsidian.

If you need to restrict CORS origins, set the `CORS_ORIGINS` environment variable in your backend:

```bash
# In backend/.env or as environment variable
CORS_ORIGINS=*  # Allow all origins (default, recommended for Obsidian)

# Or specify multiple origins (comma-separated):
# CORS_ORIGINS=http://localhost:3000,http://localhost:8000,app://obsidian.md
```

After changing CORS settings, restart your Crossbill backend server.

## Configuration

Before using the plugin, you need to configure your Crossbill server:

1. Open Settings → Crossbill
2. Set the "Server Host" to your Crossbill server URL (e.g., `http://localhost:8000`)
3. Save settings

## Usage

1. Open a note where you want to import highlights
2. Open the Command Palette (Ctrl/Cmd + P)
3. Search for "Import highlights from Crossbill"
4. Select the command
5. Choose a book from the list
6. Choose a chapter from the book
7. The highlights will be inserted at your cursor position

## Highlight Format

Highlights are imported in the following format:

```markdown
## Book Title
**Author:** Author Name
**Chapter:** Chapter Name

### Highlight 1
> Highlighted text here

**Note:** Any notes you made on the highlight

*Page 42*

---
```

## Development

### Building

```bash
# Development build with watch mode
npm run dev

# Production build
npm run build
```

### Project Structure

- `main.ts` - Main plugin code including API client, modals, and settings
- `manifest.json` - Plugin metadata
- `styles.css` - Plugin styles
- `esbuild.config.mjs` - Build configuration
- `tsconfig.json` - TypeScript configuration

## API Reference

This plugin uses the following Crossbill API endpoints:

- `GET /api/v1/highlights/books` - Fetch list of books with highlight counts
- `GET /api/v1/book/{book_id}` - Fetch book details including chapters and highlights

## License

MIT

## Support

For issues and feature requests, please visit the [Crossbill repository](https://github.com/Tumetsu/Crossbill).
