"""Crossbill MCP Server — exposes Crossbill reading data to AI assistants."""

import logging
import os
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server

from crossbill_mcp.client import CrossbillClient
from crossbill_mcp.tools.bookmarks import register_bookmark_tools
from crossbill_mcp.tools.books import register_book_tools
from crossbill_mcp.tools.flashcards import register_flashcard_tools
from crossbill_mcp.tools.highlights import register_highlight_tools
from crossbill_mcp.tools.reading import register_reading_tools

logger = logging.getLogger(__name__)


def create_server() -> tuple[Server, CrossbillClient]:
    """Create and configure the MCP server."""
    url = os.environ.get("CROSSBILL_URL")
    email = os.environ.get("CROSSBILL_EMAIL")
    password = os.environ.get("CROSSBILL_PASSWORD")

    if not url or not email or not password:
        print(
            "Error: CROSSBILL_URL, CROSSBILL_EMAIL, and CROSSBILL_PASSWORD "
            "environment variables are required.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = CrossbillClient(url, email, password)
    server = Server("crossbill")

    # Register all tools
    register_book_tools(server, client)
    register_highlight_tools(server, client)
    register_flashcard_tools(server, client)
    register_reading_tools(server, client)
    register_bookmark_tools(server, client)

    return server, client


async def run() -> None:
    """Run the MCP server."""
    server, client = create_server()
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )
    finally:
        await client.close()


def main() -> None:
    """Entry point for the crossbill-mcp command."""
    import asyncio

    asyncio.run(run())


if __name__ == "__main__":
    main()
