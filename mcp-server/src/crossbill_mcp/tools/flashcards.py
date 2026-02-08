"""Flashcard-related MCP tools."""

import json

from mcp.server.fastmcp import FastMCP

from crossbill_mcp.client import CrossbillClient


def register_flashcard_tools(server: FastMCP, client: CrossbillClient) -> None:
    """Register flashcard-related tools with the MCP server."""

    @server.tool()
    async def get_flashcards(book_id: int) -> str:
        """Get all flashcards for a book with their associated highlights.

        Args:
            book_id: The ID of the book
        """
        result = await client.get_flashcards(book_id)
        return json.dumps(result, indent=2, default=str)

    @server.tool()
    async def create_flashcard(
        book_id: int,
        question: str,
        answer: str,
        highlight_id: int | None = None,
    ) -> str:
        """Create a new flashcard for a book, optionally linked to a highlight.

        Args:
            book_id: The ID of the book
            question: The flashcard question
            answer: The flashcard answer
            highlight_id: Optional highlight ID to link the flashcard to
        """
        result = await client.create_flashcard(book_id, question, answer, highlight_id)
        return json.dumps(result, indent=2, default=str)

    @server.tool()
    async def update_flashcard(
        flashcard_id: int,
        question: str | None = None,
        answer: str | None = None,
    ) -> str:
        """Update a flashcard's question and/or answer.

        Args:
            flashcard_id: The ID of the flashcard
            question: New question text (optional)
            answer: New answer text (optional)
        """
        result = await client.update_flashcard(flashcard_id, question, answer)
        return json.dumps(result, indent=2, default=str)

    @server.tool()
    async def delete_flashcard(flashcard_id: int) -> str:
        """Delete a flashcard.

        Args:
            flashcard_id: The ID of the flashcard
        """
        result = await client.delete_flashcard(flashcard_id)
        return json.dumps(result, indent=2, default=str)
