"""Rename book files from int IDs to UUIDs.

Revision ID: 052
Revises: 051
Create Date: 2026-04-08

Renames cover files ({int_id}.jpg -> {uuid}.jpg), epub/pdf files
({title}_{int_id}.ext -> {title}_{uuid}.ext) in both local filesystem
and S3, and updates the file_path column in the database.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, text

from alembic import op

revision: str = "052"
down_revision: str | None = "051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

logger = logging.getLogger(__name__)


def _get_book_mappings(conn: Connection) -> list[tuple[int, str, str | None]]:
    """Return [(old_int_id, uuid_str, file_path), ...] from books table."""
    result = conn.execute(text("SELECT id_old, id, file_path FROM books ORDER BY id_old"))
    return [(row[0], str(row[1]), row[2]) for row in result]


def _compute_new_filename(old_filename: str, int_id: int, uuid: str) -> str | None:
    """Replace _{int_id}.ext with _{uuid}.ext in a filename."""
    pattern = rf"^(.+)_{re.escape(str(int_id))}(\.\w+)$"
    match = re.match(pattern, old_filename)
    if not match:
        return None
    return f"{match.group(1)}_{uuid}{match.group(2)}"


# ---------------------------------------------------------------------------
# Filesystem
# ---------------------------------------------------------------------------


def _rename_covers_filesystem(books: list[tuple[int, str, str | None]]) -> None:
    book_files_dir = os.environ.get("BOOK_FILES_DIR", "book-files")
    covers_dir = Path(book_files_dir) / "book-covers"

    if not covers_dir.is_dir():
        logger.info("Covers dir %s not found — skipping filesystem covers", covers_dir)
        return

    for int_id, uuid, _file_path in books:
        for src in covers_dir.glob(f"{int_id}.*"):
            dst = covers_dir / f"{uuid}{src.suffix}"
            if not dst.exists():
                src.rename(dst)
                logger.info("Renamed cover: %s -> %s", src.name, dst.name)


def _rename_book_files_filesystem(
    books: list[tuple[int, str, str | None]],
    conn: Connection,
) -> None:
    book_files_dir = os.environ.get("BOOK_FILES_DIR", "book-files")
    epubs_dir = Path(book_files_dir) / "epubs"
    pdfs_dir = Path(book_files_dir) / "pdfs"

    for int_id, uuid, file_path in books:
        if not file_path:
            continue

        new_filename = _compute_new_filename(file_path, int_id, uuid)
        if new_filename is None:
            continue

        base_dir = epubs_dir if file_path.endswith(".epub") else pdfs_dir
        src = base_dir / file_path
        dst = base_dir / new_filename

        if src.exists() and not dst.exists():
            src.rename(dst)
            conn.execute(
                text("UPDATE books SET file_path = :fp WHERE id = :uid"),
                {"fp": new_filename, "uid": uuid},
            )
            logger.info("Renamed book file: %s -> %s", src.name, dst.name)


# ---------------------------------------------------------------------------
# S3
# ---------------------------------------------------------------------------


def _get_s3_client() -> tuple[Any, str] | tuple[None, None]:
    """Create S3 client from env vars. Returns (client, bucket) or (None, None)."""
    endpoint = os.environ.get("S3_ENDPOINT_URL")
    bucket = os.environ.get("S3_BUCKET_NAME")
    if not endpoint or not bucket:
        return None, None

    try:
        import boto3  # noqa: PLC0415
    except ImportError:
        return None, None

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("S3_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("S3_REGION", "us-east-1"),
    )
    return client, bucket


def _s3_key_exists(client: Any, bucket: str, key: str) -> bool:  # noqa: ANN401
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except client.exceptions.ClientError:
        return False


def _s3_rename(client: Any, bucket: str, src_key: str, dst_key: str) -> None:  # noqa: ANN401
    client.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": src_key}, Key=dst_key)
    client.delete_object(Bucket=bucket, Key=src_key)
    logger.info("Renamed S3 object: %s -> %s", src_key, dst_key)


def _rename_covers_s3(books: list[tuple[int, str, str | None]]) -> None:
    client, bucket = _get_s3_client()
    if client is None or bucket is None:
        logger.info("S3 not configured — skipping S3 covers")
        return

    for int_id, uuid, _file_path in books:
        prefix = f"book-covers/{int_id}."
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for obj in response.get("Contents", []):
            src_key = obj["Key"]
            ext = src_key.rsplit(".", 1)[-1] if "." in src_key else "jpg"
            dst_key = f"book-covers/{uuid}.{ext}"
            if not _s3_key_exists(client, bucket, dst_key):
                _s3_rename(client, bucket, src_key, dst_key)


def _rename_book_files_s3(
    books: list[tuple[int, str, str | None]],
    conn: Connection,
) -> None:
    client, bucket = _get_s3_client()
    if client is None or bucket is None:
        logger.info("S3 not configured — skipping S3 book files")
        return

    for int_id, uuid, file_path in books:
        if not file_path:
            continue

        new_filename = _compute_new_filename(file_path, int_id, uuid)
        if new_filename is None:
            continue

        if file_path.endswith(".epub"):
            s3_prefix = "epubs/"
        elif file_path.endswith(".pdf"):
            s3_prefix = "pdfs/"
        else:
            continue

        src_key = f"{s3_prefix}{file_path}"
        dst_key = f"{s3_prefix}{new_filename}"

        if _s3_key_exists(client, bucket, src_key) and not _s3_key_exists(
            client, bucket, dst_key
        ):
            _s3_rename(client, bucket, src_key, dst_key)
            conn.execute(
                text("UPDATE books SET file_path = :fp WHERE id = :uid"),
                {"fp": new_filename, "uid": uuid},
            )


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


def upgrade() -> None:
    conn = op.get_bind()
    books = _get_book_mappings(conn)
    logger.info("Renaming files for %d books", len(books))

    _rename_covers_filesystem(books)
    _rename_covers_s3(books)
    _rename_book_files_filesystem(books, conn)
    _rename_book_files_s3(books, conn)

    logger.info("File rename migration complete")


def downgrade() -> None:
    raise RuntimeError("Migration 052 is not reversible: files have been renamed.")
