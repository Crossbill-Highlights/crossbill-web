"""Unit tests for S3FileRepository."""

from unittest.mock import MagicMock

import pytest

from src.domain.common.value_objects.ids import BookId
from src.infrastructure.library.repositories.s3_file_repository import S3FileRepository


@pytest.fixture
def book_id() -> BookId:
    return BookId(42)


@pytest.fixture
def s3_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def repo(s3_client: MagicMock) -> S3FileRepository:
    return S3FileRepository(s3_client=s3_client, bucket_name="test-bucket")


# ---------------------------------------------------------------------------
# save_epub
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_epub_uploads_with_correct_key(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}  # no existing epub

    filename = await repo.save_epub(book_id, b"epub-bytes", "My Book Title")

    s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="epubs/My_Book_Title_42.epub",
        Body=b"epub-bytes",
    )
    assert filename == "My_Book_Title_42.epub"


@pytest.mark.asyncio
async def test_save_epub_deletes_existing_before_saving(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    existing_key = "epubs/Old_Title_42.epub"
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": existing_key}]}

    await repo.save_epub(book_id, b"epub-bytes", "New Title")

    s3_client.delete_object.assert_called_once_with(Bucket="test-bucket", Key=existing_key)
    s3_client.put_object.assert_called_once()


@pytest.mark.asyncio
async def test_save_epub_sanitizes_title(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}

    filename = await repo.save_epub(book_id, b"bytes", 'Title: With "Special" <Chars>')

    assert filename == "Title_With_Special_Chars_42.epub"
    put_call_key = s3_client.put_object.call_args.kwargs["Key"]
    assert put_call_key == "epubs/Title_With_Special_Chars_42.epub"


# ---------------------------------------------------------------------------
# save_pdf
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_pdf_uploads_with_correct_key(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    filename = await repo.save_pdf(book_id, b"pdf-bytes", "My PDF Book")

    s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="pdfs/My_PDF_Book_42.pdf",
        Body=b"pdf-bytes",
    )
    assert filename == "My_PDF_Book_42.pdf"


@pytest.mark.asyncio
async def test_save_pdf_sanitizes_title(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    filename = await repo.save_pdf(book_id, b"bytes", "Title With Spaces")

    assert filename == "Title_With_Spaces_42.pdf"


# ---------------------------------------------------------------------------
# save_cover
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_cover_uploads_with_correct_key(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    filename = await repo.save_cover(book_id, b"image-bytes")

    s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="book-covers/42.jpg",
        Body=b"image-bytes",
    )
    assert filename == "42.jpg"


# ---------------------------------------------------------------------------
# get_epub
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_epub_returns_bytes_when_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "epubs/My_Book_42.epub"}]}
    body_mock = MagicMock()
    body_mock.read.return_value = b"epub-content"
    s3_client.get_object.return_value = {"Body": body_mock}

    result = await repo.get_epub(book_id)

    assert result == b"epub-content"
    s3_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="epubs/My_Book_42.epub")


@pytest.mark.asyncio
async def test_get_epub_returns_none_when_not_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}

    result = await repo.get_epub(book_id)

    assert result is None
    s3_client.get_object.assert_not_called()


# ---------------------------------------------------------------------------
# get_pdf
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_pdf_returns_bytes_when_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "pdfs/My_Book_42.pdf"}]}
    body_mock = MagicMock()
    body_mock.read.return_value = b"pdf-content"
    s3_client.get_object.return_value = {"Body": body_mock}

    result = await repo.get_pdf(book_id)

    assert result == b"pdf-content"


@pytest.mark.asyncio
async def test_get_pdf_returns_none_when_not_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}

    result = await repo.get_pdf(book_id)

    assert result is None


# ---------------------------------------------------------------------------
# get_cover
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cover_returns_bytes_when_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "book-covers/42.jpg"}]}
    body_mock = MagicMock()
    body_mock.read.return_value = b"cover-content"
    s3_client.get_object.return_value = {"Body": body_mock}

    result = await repo.get_cover(book_id)

    assert result == b"cover-content"


@pytest.mark.asyncio
async def test_get_cover_returns_none_when_not_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}

    result = await repo.get_cover(book_id)

    assert result is None


# ---------------------------------------------------------------------------
# delete_epub
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_epub_returns_true_when_deleted(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "epubs/My_Book_42.epub"}]}

    result = await repo.delete_epub(book_id)

    assert result is True
    s3_client.delete_object.assert_called_once_with(
        Bucket="test-bucket", Key="epubs/My_Book_42.epub"
    )


@pytest.mark.asyncio
async def test_delete_epub_returns_false_when_not_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}

    result = await repo.delete_epub(book_id)

    assert result is False
    s3_client.delete_object.assert_not_called()


@pytest.mark.asyncio
async def test_delete_epub_returns_false_on_exception(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "epubs/My_Book_42.epub"}]}
    s3_client.delete_object.side_effect = Exception("S3 error")

    result = await repo.delete_epub(book_id)

    assert result is False


# ---------------------------------------------------------------------------
# delete_pdf
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_pdf_returns_true_when_deleted(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "pdfs/My_Book_42.pdf"}]}

    result = await repo.delete_pdf(book_id)

    assert result is True
    s3_client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="pdfs/My_Book_42.pdf")


@pytest.mark.asyncio
async def test_delete_pdf_returns_false_when_not_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}

    result = await repo.delete_pdf(book_id)

    assert result is False


@pytest.mark.asyncio
async def test_delete_pdf_returns_false_on_exception(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "pdfs/My_Book_42.pdf"}]}
    s3_client.delete_object.side_effect = Exception("S3 error")

    result = await repo.delete_pdf(book_id)

    assert result is False


# ---------------------------------------------------------------------------
# delete_cover
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_cover_returns_true_when_deleted(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "book-covers/42.jpg"}]}

    result = await repo.delete_cover(book_id)

    assert result is True
    s3_client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="book-covers/42.jpg")


@pytest.mark.asyncio
async def test_delete_cover_returns_false_when_not_found(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}

    result = await repo.delete_cover(book_id)

    assert result is False


@pytest.mark.asyncio
async def test_delete_cover_returns_false_on_exception(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "book-covers/42.jpg"}]}
    s3_client.delete_object.side_effect = Exception("S3 error")

    result = await repo.delete_cover(book_id)

    assert result is False


# ---------------------------------------------------------------------------
# has_cover
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_has_cover_returns_true_when_cover_exists(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {"Contents": [{"Key": "book-covers/42.jpg"}]}

    result = await repo.has_cover(book_id)

    assert result is True


@pytest.mark.asyncio
async def test_has_cover_returns_false_when_no_cover(
    repo: S3FileRepository, s3_client: MagicMock, book_id: BookId
) -> None:
    s3_client.list_objects_v2.return_value = {}

    result = await repo.has_cover(book_id)

    assert result is False
