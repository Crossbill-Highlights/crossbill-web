<p align="center">

<img width="96" height="96" alt="image" src="https://github.com/user-attachments/assets/6461072f-2265-443b-a018-db7ae26cb42f" />
</p>

# Crossbill

[![CI](https://github.com/Tumetsu/Crossbill/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Tumetsu/Crossbill/actions/workflows/ci.yml)
[![Docker Image Version](https://img.shields.io/docker/v/tumetsu/crossbill?sort=semver)](https://hub.docker.com/r/tumetsu/crossbill)

A self-hosted web application for syncing, managing, and viewing book highlights from KOReader.

## Overview

Crossbill helps you centralize and manage your ebook highlights by providing:

- **Backend API**: FastAPI server with PostgreSQL database for storing highlights
- **Web Frontend**: Modern React interface for browsing, editing, and organizing your highlights
- **KOReader Plugin**: Syncs highlights directly from your KOReader e-reader
- **Obsidian Plugin**: Integrate highlights into your Obsidian notes
- [**Anki Plugin**: Integrate highlights into your Anki flash cards](https://ankiweb.net/shared/info/1205712943)

## Features

- Sync highlights from KOReader with automatic deduplication
- Web interface for viewing and managing highlights by book
- Organize highlights with notes and metadata
- Export highlights to various apps
- Self-hosted - your data stays on your server
- Multi-user support

## Screenshots

<img width="250" alt="image" src="https://github.com/user-attachments/assets/262ba290-ed79-47ff-a8b3-aa6b3f3b59a3" />
<img width="250" alt="image" src="https://github.com/user-attachments/assets/397be7cd-541d-49be-975b-d5db3caab2c3" />
<img width="250" alt="image" src="https://github.com/user-attachments/assets/de548aa4-c721-4ff7-b008-3c6aa8de0bdd" />

## Installation
Easiest way to install and run Crossbill is by using  `docker-compose.yml` with PostgreSQL:

```yaml
services:
  postgres:
    image: postgres:18-alpine
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
    image: tumetsu/crossbill:latest
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
      CORS_ORIGINS: "https://yourdomain.com"
      SECRET_KEY: ${SECRET_KEY}
      ACCESS_TOKEN_EXPIRE_MINUTES: 15
      REFRESH_TOKEN_EXPIRE_DAYS: 30
      REFRESH_TOKEN_SECRET_KEY: ${REFRESH_TOKEN_SECRET_KEY}
COOKIE_SECURE=true
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

Then install the Koreader [plugin on your e-reader](clients/koreader-plugin/crossbill.koplugin/README.md).

## Development
Each component has its own installation instructions for development:

- **Backend**: See [backend/README.md](backend/README.md)
- **Frontend**: See [frontend/README.md](frontend/README.md)
- **KOReader Plugin**: See [clients/koreader-plugin/crossbill.koplugin/README.md](clients/koreader-plugin/crossbill.koplugin/README.md)
- **Obsidian Plugin**: See [clients/obsidian-plugin/README.md](clients/obsidian-plugin/README.md)

API documentation can be found from URL `<backend host>/api/v1/docs` when running the backend server.
