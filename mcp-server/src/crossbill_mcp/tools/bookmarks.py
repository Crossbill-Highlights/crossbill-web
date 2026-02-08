"""Bookmark-related MCP tools."""

import json

from mcp.server import Server

from crossbill_mcp.client import CrossbillClient


def register_bookmark_tools(server: Server, client: CrossbillClient) -> None:
    """Register bookmark-related tools with the MCP server."""

    @server.tool()
    async def create_bookmark(book_id: int, highlight_id: int) -> str:
        """Create a bookmark for a highlight.

        Args:
            book_id: The ID of the book
            highlight_id: The ID of the highlight to bookmark
        """
        result = await client.create_bookmark(book_id, highlight_id)
        return json.dumps(result, indent=2, default=str)

    @server.tool()
    async def delete_bookmark(book_id: int, bookmark_id: int) -> str:
        """Delete a bookmark.

        Args:
            book_id: The ID of the book
            bookmark_id: The ID of the bookmark to delete
        """
        result = await client.delete_bookmark(book_id, bookmark_id)
        return json.dumps(result, indent=2, default=str)
