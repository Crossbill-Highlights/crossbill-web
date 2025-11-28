# Crossbill KOReader Plugin

Syncs your KOReader highlights to your crossbill server.

## Installation

1. Copy the `crossbill.koplugin` directory to your KOReader plugins folder:
   - **Device**: `koreader/plugins/`
   - **Desktop**: `.config/koreader/plugins/` (Linux/Mac) or `%APPDATA%\koreader\plugins\` (Windows)

2. Restart KOReader

3. Open any book and go to: Menu → crossbill Sync → Configure Server

4. Enter your crossbill server host URL (e.g., `http://192.168.1.100:8000`)

## Usage

1. Open a book with highlights
2. Menu → crossbill Sync → Sync Current Book
3. View your synced highlights on your crossbill server

## Features

- Syncs highlights from the currently open book
- Automatic deduplication - re-syncing won't create duplicates
- Extracts ISBN from book metadata when available
- Uploads book cover from ebook to the Crossbill
- Works with any book format supported by KOReader (EPUB, PDF, etc.)

## Requirements

- KOReader version 2021.04 or later
- Network connection to your crossbill server

## Tested devices
While the plugin *should* work on any device running KOReader, it has been specifically tested on:
* Pocketbook Era

## Server Configuration

The default server URL is `http://localhost:8000`. You'll need to change this to your actual crossbill server host address.

## Development
You can use `copy_to_pocketbook.sh` script to copy the plugin to a connected Pocketbook device for testing by creating `.env`file
with your unique path to the device's koreader plugins folder. The script copies the plugin both as a "production" version and
as a  "development" version letting you to use different server configuration for local testing and production.
