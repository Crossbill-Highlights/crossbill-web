"""Rename book files from int IDs to UUIDs.

Revision ID: 052
Revises: 051
Create Date: 2026-04-08

Renames cover files ({int_id}.jpg -> {uuid}.jpg), epub/pdf files
({title}_{int_id}.ext -> {title}_{uuid}.ext) in both local filesystem
and S3, and updates the file_path column in the database.
"""

from __future__ import annotations

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


def _log(msg: str) -> None:
    """Print to stdout so output is visible during alembic upgrade."""
    print(f"  [052] {msg}")


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
        _log(f"Covers dir {covers_dir} not found — skipping filesystem covers")
        return

    renamed = 0
    for int_id, uuid, _file_path in books:
        for src in covers_dir.glob(f"{int_id}.*"):
            dst = covers_dir / f"{uuid}{src.suffix}"
            if dst.exists():
                _log(f"  Cover target exists, skipping: {src.name}")
                continue
            src.rename(dst)
            _log(f"  Renamed cover: {src.name} -> {dst.name}")
            renamed += 1

    _log(f"Filesystem covers: {renamed} renamed")


def _rename_book_files_filesystem(
    books: list[tuple[int, str, str | None]],
    conn: Connection,
) -> None:
    book_files_dir = os.environ.get("BOOK_FILES_DIR", "book-files")
    epubs_dir = Path(book_files_dir) / "epubs"
    pdfs_dir = Path(book_files_dir) / "pdfs"

    renamed = 0
    for int_id, uuid, file_path in books:
        if not file_path:
            continue

        new_filename = _compute_new_filename(file_path, int_id, uuid)
        if new_filename is None:
            continue

        base_dir = epubs_dir if file_path.endswith(".epub") else pdfs_dir
        src = base_dir / file_path
        dst = base_dir / new_filename

        if not src.exists():
            continue
        if dst.exists():
            _log(f"  Book file target exists, skipping: {src.name}")
            continue

        src.rename(dst)
        conn.execute(
            text("UPDATE books SET file_path = :fp WHERE id = :uid"),
            {"fp": new_filename, "uid": uuid},
        )
        _log(f"  Renamed book file: {src.name} -> {dst.name}")
        renamed += 1

    _log(f"Filesystem book files: {renamed} renamed")


# ---------------------------------------------------------------------------
# S3
# ---------------------------------------------------------------------------


def _get_s3_client() -> tuple[Any, str] | tuple[None, None]:
    """Create S3 client from app settings. Returns (client, bucket) or (None, None)."""
    from src.config import get_settings  # noqa: PLC0415

    settings = get_settings()
    if not settings.s3_enabled:
        return None, None

    assert settings.S3_BUCKET_NAME is not None  # guaranteed by s3_enabled

    try:
        import boto3  # noqa: PLC0415
    except ImportError:
        return None, None

    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
    )
    return client, settings.S3_BUCKET_NAME


def _s3_key_exists(client: Any, bucket: str, key: str) -> bool:  # noqa: ANN401
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def _s3_rename(client: Any, bucket: str, src_key: str, dst_key: str) -> None:  # noqa: ANN401
    client.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": src_key}, Key=dst_key)
    client.delete_object(Bucket=bucket, Key=src_key)


def _rename_covers_s3(books: list[tuple[int, str, str | None]]) -> None:
    client, bucket = _get_s3_client()
    if client is None or bucket is None:
        _log("S3 not configured — skipping S3 covers")
        return

    renamed = 0
    for int_id, uuid, _file_path in books:
        prefix = f"book-covers/{int_id}."
        _log(f"  Looking for S3 covers with prefix: {prefix}")
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        contents = response.get("Contents", [])
        _log(f"  Found {len(contents)} objects")

        for obj in contents:
            src_key = obj["Key"]
            ext = src_key.rsplit(".", 1)[-1] if "." in src_key else "jpg"
            dst_key = f"book-covers/{uuid}.{ext}"

            if _s3_key_exists(client, bucket, dst_key):
                _log(f"  Target exists, skipping: {src_key}")
                continue

            _s3_rename(client, bucket, src_key, dst_key)
            _log(f"  Renamed: {src_key} -> {dst_key}")
            renamed += 1

    _log(f"S3 covers: {renamed} renamed")


def _rename_book_files_s3(
    books: list[tuple[int, str, str | None]],
    conn: Connection,
) -> None:
    client, bucket = _get_s3_client()
    if client is None or bucket is None:
        _log("S3 not configured — skipping S3 book files")
        return

    renamed = 0
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

        _log(f"  Checking: {src_key}")

        if not _s3_key_exists(client, bucket, src_key):
            _log(f"  Source not found: {src_key}")
            continue
        if _s3_key_exists(client, bucket, dst_key):
            _log(f"  Target exists, skipping: {dst_key}")
            continue

        _s3_rename(client, bucket, src_key, dst_key)
        conn.execute(
            text("UPDATE books SET file_path = :fp WHERE id = :uid"),
            {"fp": new_filename, "uid": uuid},
        )
        _log(f"  Renamed: {src_key} -> {dst_key}")
        renamed += 1

    _log(f"S3 book files: {renamed} renamed")


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


def upgrade() -> None:
    conn = op.get_bind()
    books = _get_book_mappings(conn)
    _log(f"Found {len(books)} books to process")
    for int_id, uuid, file_path in books:
        _log(f"  id_old={int_id} uuid={uuid} file_path={file_path}")

    _rename_covers_filesystem(books)
    _rename_covers_s3(books)
    _rename_book_files_filesystem(books, conn)
    _rename_book_files_s3(books, conn)

    _log("File rename migration complete")


def downgrade() -> None:
    raise RuntimeError("Migration 052 is not reversible: files have been renamed.")
