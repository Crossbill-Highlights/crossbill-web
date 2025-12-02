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

## Example docker-compose
An example `docker-compose.yml` for running Crossbill with PostgreSQL:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: crossbill-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: crossbill
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-crossbill_secure_password}
      POSTGRES_DB: crossbill
      PGDATA: /var/lib/postgresql/data/pgdata
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U crossbill"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - crossbill-network

  app:
    image: crossbill:latest # Replace with your built image or official image when available
    container_name: crossbill-app
    restart: unless-stopped
    pull_policy: always
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://crossbill:${POSTGRES_PASSWORD:-crossbill_secure_password}@postgres:5432/crossbill
      ENVIRONMENT: production
      ADMIN_USERNAME: ${ADMIN_USERNAME}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD}
      SECRET_KEY: ${SECRET_KEY}
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
      ALLOW_USER_REGISTRATIONS: false
      PORT: 8000
    volumes:
      - book_covers:/app/book-covers
      - type: bind
        source: /path/on/host/for/crossbill/book_covers
        target: /app/book-covers
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - crossbill-network

volumes:
  postgres_data:
    driver: local
  book_covers:
    driver: local

networks:
  crossbill-network:
    driver: bridge
```
