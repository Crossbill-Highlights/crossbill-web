"""
Crossbill API Client

Handles communication with the Crossbill backend server.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable

from models import (
    BookDetails,
    BooksListResponse,
    BookWithHighlightCount,
    ChapterWithHighlights,
    FlashcardsResponse,
    FlashcardWithHighlight,
    Highlight,
    HighlightTag,
)


class CrossbillAPIError(Exception):
    """Raised when API request fails"""


class CrossbillAPI:
    """Client for communicating with Crossbill backend"""

    def __init__(
        self,
        server_host: str,
        bearer_token: str | None = None,
        email: str | None = None,
        password: str | None = None,
        refresh_token: str | None = None,
        token_expires_at: float | None = None,
    ) -> None:
        """
        Initialize API client

        Args:
            server_host: Base URL of Crossbill server (e.g., 'http://localhost:8000')
            bearer_token: Optional JWT bearer token for authentication
            email: Optional email for automatic login
            password: Optional password for automatic login
            refresh_token: Optional refresh token for token renewal
            token_expires_at: Optional timestamp when access token expires
        """
        self.server_host = server_host.rstrip("/")
        self.bearer_token = bearer_token or ""
        self.email = email or ""
        self.password = password or ""
        self.refresh_token = refresh_token or ""
        self.token_expires_at = token_expires_at
        self.on_token_update: Callable[[str, str, float], None] | None = None

    def set_credentials(self, email: str, password: str) -> None:
        """Update email and password credentials"""
        self.email = email
        self.password = password

    def set_bearer_token(
        self, token: str, refresh_token: str = "", expires_at: float | None = None
    ) -> None:
        """Update bearer token and optionally refresh token"""
        self.bearer_token = token
        if refresh_token:
            self.refresh_token = refresh_token
        if expires_at is not None:
            self.token_expires_at = expires_at

    def set_on_token_update(self, callback: Callable[[str, str, float], None]) -> None:
        """Set callback to be called when token is updated (token, refresh_token, expires_at)"""
        self.on_token_update = callback

    def _is_token_expired(self) -> bool:
        """Check if the current access token is expired (with 60s buffer)"""
        if not self.token_expires_at:
            return True
        return time.time() > (self.token_expires_at - 60)

    def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using the stored refresh token

        Returns:
            True if refresh succeeded, False otherwise
        """
        if not self.refresh_token:
            return False

        url = f"{self.server_host}/api/v1/auth/refresh"

        # Send refresh token in request body (for plugin clients)
        body = json.dumps({"refresh_token": self.refresh_token})

        try:
            request = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
            request.add_header("Content-Type", "application/json")
            request.add_header("Accept", "application/json")

            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                self.bearer_token = data["access_token"]
                self.refresh_token = data.get("refresh_token", self.refresh_token)
                if "expires_in" in data:
                    self.token_expires_at = time.time() + data["expires_in"]

                # Notify callback if set
                if self.on_token_update:
                    self.on_token_update(
                        self.bearer_token, self.refresh_token, self.token_expires_at or 0
                    )

                return True

        except Exception:
            # Refresh failed, clear tokens
            self.refresh_token = ""
            self.token_expires_at = None
            return False

    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token"""
        # Check if we have a valid (non-expired) token
        if self.bearer_token and not self._is_token_expired():
            return

        # Try to refresh the token if we have a refresh token
        if self.refresh_token and self._refresh_access_token():
            return

        # Fall back to full login
        if not self.email or not self.password:
            raise CrossbillAPIError(
                "No credentials provided. Please set email and password in settings."
            )

        self.login(self.email, self.password)

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate with Crossbill server

        Args:
            email: User email
            password: User password

        Returns:
            Login response with access_token, refresh_token, and expires_in

        Raises:
            CrossbillAPIError: If login fails
        """
        url = f"{self.server_host}/api/v1/auth/login"

        # Prepare form data (OAuth2 password flow)
        form_data = urllib.parse.urlencode(
            {
                "username": email,  # Backend uses 'username' field for email
                "password": password,
            }
        )

        try:
            request = urllib.request.Request(url, data=form_data.encode("utf-8"), method="POST")
            request.add_header("Content-Type", "application/x-www-form-urlencoded")
            request.add_header("Accept", "application/json")

            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                self.bearer_token = data["access_token"]
                self.refresh_token = data.get("refresh_token", "")
                if "expires_in" in data:
                    self.token_expires_at = time.time() + data["expires_in"]

                # Notify callback if set
                if self.on_token_update:
                    self.on_token_update(
                        self.bearer_token, self.refresh_token, self.token_expires_at or 0
                    )

                return data

        except urllib.error.HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                if "detail" in error_data:
                    error_msg += f" - {error_data['detail']}"
            except Exception:
                pass
            raise CrossbillAPIError(f"Login failed: {error_msg}") from e

        except Exception as e:
            raise CrossbillAPIError(f"Login failed: {e}") from e

    def _make_request(self, endpoint: str, retry_on_401: bool = True) -> dict:
        """
        Make authenticated HTTP GET request to API endpoint

        Args:
            endpoint: API endpoint path (e.g., '/api/v1/books')
            retry_on_401: Whether to retry with fresh login on 401 error

        Returns:
            Parsed JSON response

        Raises:
            CrossbillAPIError: If request fails
        """
        # Ensure we're authenticated before making the request
        self._ensure_authenticated()

        url = f"{self.server_host}{endpoint}"

        try:
            request = urllib.request.Request(url)
            request.add_header("Accept", "application/json")

            # Add authentication header
            if self.bearer_token:
                request.add_header("Authorization", f"Bearer {self.bearer_token}")

            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            # Handle 401 Unauthorized - token expired
            if e.code == 401 and retry_on_401:
                # Try refresh first, then fall back to login
                self.bearer_token = ""
                if self.refresh_token and self._refresh_access_token():
                    return self._make_request(endpoint, retry_on_401=False)
                # Refresh failed, try full login
                self._ensure_authenticated()
                return self._make_request(endpoint, retry_on_401=False)

            error_msg = f"HTTP {e.code}: {e.reason}"
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                if "detail" in error_data:
                    error_msg += f" - {error_data['detail']}"
            except Exception:
                pass
            raise CrossbillAPIError(f"Failed to fetch {endpoint}: {error_msg}") from e

        except urllib.error.URLError as e:
            raise CrossbillAPIError(f"Network error: {e.reason}") from e

        except json.JSONDecodeError as e:
            raise CrossbillAPIError(f"Invalid JSON response from {endpoint}: {e}") from e

        except Exception as e:
            raise CrossbillAPIError(f"Unexpected error: {e}") from e

    def get_books(self, limit: int = 1000, offset: int = 0) -> BooksListResponse:
        """
        Fetch list of books with highlight counts

        Args:
            limit: Maximum number of books to fetch
            offset: Number of books to skip

        Returns:
            BooksListResponse containing list of books

        Raises:
            CrossbillAPIError: If request fails
        """
        endpoint = f"/api/v1/books/?limit={limit}&offset={offset}"
        data = self._make_request(endpoint)

        books = []
        for book_data in data.get("books", []):
            book = BookWithHighlightCount(
                id=book_data["id"],
                title=book_data["title"],
                author=book_data.get("author"),
                isbn=book_data.get("isbn"),
                created_at=book_data["created_at"],
                updated_at=book_data["updated_at"],
                highlight_count=book_data["highlight_count"],
                flashcard_count=book_data.get("flashcard_count", 0),
            )
            books.append(book)

        return BooksListResponse(
            books=books,
            total=data.get("total", len(books)),
            offset=data.get("offset", 0),
            limit=data.get("limit", limit),
        )

    def get_book_details(self, book_id: int) -> BookDetails:
        """
        Fetch book details including all chapters and highlights

        Args:
            book_id: ID of the book to fetch

        Returns:
            BookDetails with chapters and highlights

        Raises:
            CrossbillAPIError: If request fails
        """
        endpoint = f"/api/v1/books/{book_id}"
        data = self._make_request(endpoint)

        # Parse chapters with highlights
        chapters = []
        for chapter_data in data.get("chapters", []):
            # Parse highlights for this chapter
            highlights = []
            for hl_data in chapter_data.get("highlights", []):
                # Parse tags
                tags = []
                for tag_data in hl_data.get("highlight_tags", []):
                    tags.append(HighlightTag(id=tag_data["id"], name=tag_data["name"]))

                highlight = Highlight(
                    id=hl_data["id"],
                    book_id=hl_data["book_id"],
                    chapter_id=hl_data.get("chapter_id"),
                    text=hl_data["text"],
                    chapter=hl_data.get("chapter"),
                    page=hl_data.get("page"),
                    note=hl_data.get("note"),
                    datetime=hl_data["datetime"],
                    highlight_tags=tags,
                    created_at=hl_data["created_at"],
                    updated_at=hl_data["updated_at"],
                )
                highlights.append(highlight)

            chapter = ChapterWithHighlights(
                id=chapter_data["id"],
                book_id=data["id"],  # Use book ID from parent response
                name=chapter_data["name"],
                created_at=chapter_data["created_at"],
                updated_at=chapter_data["updated_at"],
                highlights=highlights,
            )
            chapters.append(chapter)

        return BookDetails(
            id=data["id"],
            title=data["title"],
            author=data.get("author"),
            isbn=data.get("isbn"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            chapters=chapters,
        )

    def get_flashcards(self, book_id: int) -> FlashcardsResponse:
        """
        Fetch all flashcards for a book with their embedded highlight data

        Args:
            book_id: ID of the book to fetch flashcards for

        Returns:
            FlashcardsResponse containing list of flashcards

        Raises:
            CrossbillAPIError: If request fails
        """
        endpoint = f"/api/v1/books/{book_id}/flashcards"
        data = self._make_request(endpoint)

        flashcards = []
        for fc_data in data.get("flashcards", []):
            # Parse embedded highlight if present
            highlight = None
            hl_data = fc_data.get("highlight")
            if hl_data:
                # Parse tags
                tags = []
                for tag_data in hl_data.get("highlight_tags", []):
                    tags.append(HighlightTag(id=tag_data["id"], name=tag_data["name"]))

                highlight = Highlight(
                    id=hl_data["id"],
                    book_id=hl_data["book_id"],
                    chapter_id=hl_data.get("chapter_id"),
                    text=hl_data["text"],
                    chapter=hl_data.get("chapter"),
                    page=hl_data.get("page"),
                    note=hl_data.get("note"),
                    datetime=hl_data.get("datetime", ""),
                    highlight_tags=tags,
                    created_at=hl_data["created_at"],
                    updated_at=hl_data["updated_at"],
                )

            flashcard = FlashcardWithHighlight(
                id=fc_data["id"],
                book_id=fc_data["book_id"],
                highlight_id=fc_data.get("highlight_id"),
                question=fc_data["question"],
                answer=fc_data["answer"],
                created_at=fc_data["created_at"],
                updated_at=fc_data["updated_at"],
                highlight=highlight,
            )
            flashcards.append(flashcard)

        return FlashcardsResponse(flashcards=flashcards)

    def test_connection(self) -> tuple[bool, str]:
        """
        Test if connection to Crossbill server is working

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.get_books(limit=1)
            return True, "Connection successful"
        except CrossbillAPIError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {e}"
