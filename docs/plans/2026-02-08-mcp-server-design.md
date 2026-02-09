# Crossbill MCP Server Design

## Overview

An MCP (Model Context Protocol) server that exposes the Crossbill REST API to AI assistants like Claude. Users can explore their reading library, manage highlights and flashcards, read EPUB chapter content, and leverage AI-augmented workflows — all through natural language conversation.

## Goals

- **Read-only exploration**: Search books, browse highlights, review flashcards, view reading sessions
- **Full read/write access**: Create flashcards, annotate highlights, tag highlights, manage bookmarks
- **AI-augmented workflows**: Combine reading data with Claude's intelligence (e.g., "create flashcards for all highlights in chapter 3", "find themes across my highlights")
- **EPUB content access**: Read chapter text directly, enabling Claude to discuss and analyze book content

## Architecture

### Standalone Process Calling REST API

The MCP server is a **standalone Python process** that communicates with Crossbill via its existing REST API. It is launched as a subprocess by the AI client (Claude Code, Claude Desktop) and communicates over **stdio**.

```
┌──────────────┐     stdio      ┌──────────────────┐     HTTP/REST     ┌──────────────────┐
│  Claude Code │ ◄────────────► │  Crossbill MCP   │ ◄───────────────► │  Crossbill API   │
│  / Desktop   │                │  Server (Python)  │                   │  (FastAPI)       │
└──────────────┘                └──────────────────┘                   └──────────────────┘
```

**Why this approach:**
- Zero changes to existing backend (except one new endpoint)
- Works with any Crossbill deployment (local, remote, Docker)
- Clear separation of concerns
- Easy to distribute independently

### Authentication

The MCP server authenticates with Crossbill using **email/password** via environment variables. It handles the JWT token lifecycle internally:

1. Logs in with email/password on first API call
2. Stores access token and refresh token in memory
3. Auto-refreshes access token when it expires
4. Re-authenticates if refresh token also expires

## Backend Change: Chapter Content Endpoint

One new endpoint is required in the Crossbill backend to support reading EPUB chapter content.

### `GET /api/v1/chapters/{chapter_id}/content`

**Auth:** Required

**Response:**
```json
{
  "chapter_id": 1,
  "chapter_name": "Chapter 1: Introduction",
  "book_id": 1,
  "content": "The full text content of the chapter..."
}
```

**Errors:**
- 404: Chapter not found
- 400: Book has no EPUB uploaded

**Implementation:**
- Follows the existing hexagonal/DDD architecture
- Reuses existing EPUB text extraction logic (already used by pre-reading and AI summary features)
- Extracts text between the chapter's `start_xpoint` and the next chapter's start
- Ownership check: verify the book belongs to the authenticated user

## MCP Server Project Structure

```
mcp-server/
├── pyproject.toml
├── src/
│   └── crossbill_mcp/
│       ├── __init__.py
│       ├── server.py           # MCP server setup, tool registration
│       ├── client.py           # Crossbill REST API client
│       └── tools/
│           ├── __init__.py
│           ├── books.py        # list_books, get_book, get_recently_viewed
│           ├── highlights.py   # get_highlights, update_note, tag/untag
│           ├── flashcards.py   # CRUD flashcards
│           ├── reading.py      # get_reading_sessions, get_chapter_content
│           └── bookmarks.py    # create/delete bookmark
```

### Components

**`client.py`** — `CrossbillClient` class that handles all HTTP communication:
- Login with email/password
- JWT token storage and auto-refresh
- Typed methods for each API endpoint (e.g., `get_books()`, `get_book(id)`)
- Uses `httpx` for async HTTP

**`server.py`** — Entry point:
- Creates MCP `Server` instance
- Reads config from environment variables
- Registers all tools from `tools/` modules
- Runs stdio transport

**`tools/`** — Each module registers tools with the server. Tools are thin wrappers that validate input, call the client, and format the response for the AI.

### Dependencies

- `mcp` — Python MCP SDK
- `httpx` — Async HTTP client
- `pydantic` — Tool input validation (used by MCP SDK)

## Tool Reference

### Read Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_books` | List/search books in library | `search?`, `limit?`, `offset?` |
| `get_book` | Get detailed book info with chapters and highlights | `book_id` |
| `get_recently_viewed_books` | Get recently viewed books | `limit?` |
| `get_highlights` | Get highlights for a book with optional filtering | `book_id`, `search?`, `chapter_id?` |
| `get_flashcards` | Get flashcards for a book with highlight context | `book_id` |
| `get_reading_sessions` | Get reading sessions for a book | `book_id`, `limit?` |
| `get_chapter_content` | Get the full text content of a chapter from EPUB | `chapter_id` |

### Write Operations

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_flashcard` | Create a flashcard for a book or highlight | `book_id`, `question`, `answer`, `highlight_id?` |
| `update_flashcard` | Update flashcard question and/or answer | `flashcard_id`, `question?`, `answer?` |
| `delete_flashcard` | Delete a flashcard | `flashcard_id` |
| `update_highlight_note` | Add or update a note on a highlight | `highlight_id`, `note` |
| `tag_highlight` | Add a tag to a highlight (creates tag if needed) | `book_id`, `highlight_id`, `tag_name` |
| `untag_highlight` | Remove a tag from a highlight | `book_id`, `highlight_id`, `tag_id` |
| `create_bookmark` | Bookmark a highlight | `book_id`, `highlight_id` |
| `delete_bookmark` | Remove a bookmark | `book_id`, `bookmark_id` |

### Design Decisions

- **`tag_highlight` uses `tag_name`** (not ID) so the AI can say "tag this as important" without looking up tag IDs. The API supports create-or-get by name.
- **No book creation/deletion** — that's an e-reader sync concern, not an AI workflow.
- **No highlight creation/deletion** — highlights come from KOReader. Deleting through AI is risky.
- **`get_book` returns chapters with highlights inline** — gives the AI full context in one call.

## Configuration

### Environment Variables

```
CROSSBILL_URL=http://localhost:8000
CROSSBILL_EMAIL=user@example.com
CROSSBILL_PASSWORD=yourpassword
```

### Claude Code Configuration

`~/.claude/claude_code_config.json`:
```json
{
  "mcpServers": {
    "crossbill": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-server", "crossbill-mcp"],
      "env": {
        "CROSSBILL_URL": "http://localhost:8000",
        "CROSSBILL_EMAIL": "user@example.com",
        "CROSSBILL_PASSWORD": "yourpassword"
      }
    }
  }
}
```

### Claude Desktop Configuration

`claude_desktop_config.json` uses the same format.

## Example Workflows

**Exploring a book:**
> "What books do I have about software architecture?"
> "Show me the highlights from Clean Architecture chapter 5"
> "What's the actual text of that chapter?"

**Creating study materials:**
> "Create flashcards for all the highlights in chapter 3 of Domain-Driven Design"
> "Tag all highlights mentioning 'bounded context' as 'DDD-core'"

**Research across books:**
> "Find all my highlights that mention testing across all books"
> "What notes have I written on highlights in the last month?"

**Reading comprehension:**
> "Read chapter 7 and explain the main argument"
> "Compare what the author says in chapter 3 vs chapter 8"
