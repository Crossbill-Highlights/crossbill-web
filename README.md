<p align="center">

<img width="96" height="96" alt="image" src="https://github.com/user-attachments/assets/6461072f-2265-443b-a018-db7ae26cb42f" />
</p>

# Crossbill

[![CI](https://github.com/Tumetsu/Crossbill/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Tumetsu/Crossbill/actions/workflows/ci.yml)
[![Docker Image Version](https://img.shields.io/docker/v/tumetsu/crossbill?sort=semver)](https://hub.docker.com/r/tumetsu/crossbill)

A self-hosted web application for syncing, managing, creating flash cards and viewing book highlights from KOReader.

## Overview

Crossbill helps you centralize and manage your ebook highlights by providing:

- **Backend API**: FastAPI server with PostgreSQL database for storing highlights
- **Web Frontend**: Modern React interface for browsing, editing, and organizing your highlights
- **[KOReader Plugin](https://github.com/Crossbill-Highlights/koreader-plugin)**: Syncs highlights directly from your KOReader e-reader
- **[Obsidian Plugin](https://github.com/Crossbill-Highlights/obsidian-plugin)**: Integrate highlights into your Obsidian notes
- [**Anki Plugin**](https://github.com/Crossbill-Highlights/anki-addon): Integrate highlights into your Anki flash cards

## Features

- Sync highlights from KOReader with automatic deduplication
- Web interface for viewing and managing highlights by book
- Organize highlights with notes and metadata
- Create flash cards from your highlights and sync them to Anki or get AI suggestions from highlights.
- Create AI summaries from your reading sessions. Ollama, OpenAI, Anthropic and Gemini supported.
- Self-hosted - your data stays on your server
- Multi-user support

## Screenshots

<img width="250" alt="image" src="https://github.com/user-attachments/assets/262ba290-ed79-47ff-a8b3-aa6b3f3b59a3" />
<img width="250" alt="image" src="https://github.com/user-attachments/assets/397be7cd-541d-49be-975b-d5db3caab2c3" />
<img width="250" alt="image" src="https://github.com/user-attachments/assets/de548aa4-c721-4ff7-b008-3c6aa8de0bdd" />

## Installation

Easiest way to install and run Crossbill is by using sample `docker-compose.yml` on top level of this repository.

Then install the Koreader [plugin on your e-reader](clients/koreader-plugin/crossbill.koplugin/README.md).

## Development

Each component has its own installation instructions for development:

- **Backend**: See [backend/README.md](backend/README.md)
- **Frontend**: See [frontend/README.md](frontend/README.md)
- **KOReader Plugin**: See [clients/koreader-plugin/crossbill.koplugin/README.md](clients/koreader-plugin/crossbill.koplugin/README.md)
- **Obsidian Plugin**: See [clients/obsidian-plugin/README.md](clients/obsidian-plugin/README.md)

API documentation can be found from URL `<backend host>/api/v1/docs` when running the backend server.

## Contributions

Contributions are welcome. Few guide lines:

- Check if there is an issue you would like to work on and comment on it to discuss
- Add first issue about the feature etc. you'd like to see in the application (and work on if possible!)
- AI-assisted coding is welcome as long as you review your contributions before submitting them to the review.
