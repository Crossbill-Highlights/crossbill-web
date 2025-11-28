# Crossbill Plugin for Obsidian

This plugin allows you to import highlights from your Crossbill server directly into your Obsidian notes.

## Features

- Browse books from your Crossbill library
- Import highlights from books.
  - Individual highlights
  - All highlights from a chapter
  - All highlights from a book

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
   - In plugin settings fill in server login details.

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

The plugin provides commands to import highlights into your notes. Search them from command palette with "Crossbill" search word.

## Support

For issues and feature requests, please visit the [Crossbill repository](https://github.com/Tumetsu/Crossbill).
