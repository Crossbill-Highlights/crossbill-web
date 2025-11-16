# Crossbill

A self-hosted web application for syncing, managing, and viewing book highlights from KOReader.

## Overview

Crossbill helps you centralize and manage your ebook highlights by providing:

- **Backend API**: FastAPI server with PostgreSQL database for storing highlights
- **Web Frontend**: Modern React interface for browsing, editing, and organizing your highlights
- **KOReader Plugin**: Syncs highlights directly from your KOReader e-reader
- **Obsidian Plugin**: Integrate highlights into your Obsidian notes

## Features

- Sync highlights from KOReader with automatic deduplication
- Web interface for viewing and managing highlights by book
- Organize highlights with notes and metadata
- Export highlights to various formats
- Self-hosted - your data stays on your server

## Installation

Each component has its own installation instructions:

- **Backend**: See [backend/README.md](backend/README.md)
- **Frontend**: See [frontend/README.md](frontend/README.md)
- **KOReader Plugin**: See [clients/koreader-plugin/crossbill.koplugin/README.md](clients/koreader-plugin/crossbill.koplugin/README.md)
- **Obsidian Plugin**: See [clients/obsidian-plugin/README.md](clients/obsidian-plugin/README.md)

## Quick Start

1. Set up the backend (requires Python 3.11+ and Docker)
2. Set up the frontend (requires Node.js 18+)
3. Install the KOReader plugin on your e-reader device
4. Start syncing your highlights!

