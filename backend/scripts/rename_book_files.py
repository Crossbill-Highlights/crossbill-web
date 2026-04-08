"""Script to rename epub/pdf files from {title}_{int_id}.ext to {title}_{uuid}.ext.

Also updates the file_path column in the books table.

Run this after the cover file rename script and after both migrations (050 + 051).

Usage:
    cd backend && uv run python -m scripts.rename_book_files
    cd backend && uv run python -m scripts.rename_book_files --dry-run
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import EPUBS_DIR, PDFS_DIR, get_settings

logger = logging.getLogger(__name__)


def _sync_db_url(async_url: str) -> str:
    """Convert an async postgresql+asyncpg:// URL to a plain psycopg2 URL."""
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


def fetch_books_with_files() -> list[tuple[int, str, str | None]]:
    """Return [(old_int_id, uuid, file_path), ...] for books that have files.

    Works after migration 051 (columns: id_old + id, where id is the UUID).
    """
    settings = get_settings()
    db_url = _sync_db_url(settings.DATABASE_URL)
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'books' AND column_name IN ('uuid', 'id_old') "
                "ORDER BY column_name"
            )
            columns = {row[0] for row in cur.fetchall()}

            if "id_old" in columns:
                cur.execute(
                    "SELECT id_old, id, file_path FROM books "
                    "WHERE file_path IS NOT NULL ORDER BY id_old"
                )
            elif "uuid" in columns:
                cur.execute(
                    "SELECT id, uuid, file_path FROM books "
                    "WHERE file_path IS NOT NULL ORDER BY id"
                )
            else:
                raise RuntimeError(
                    "Cannot determine column layout. "
                    "Expected either 'uuid' (post-050) or 'id_old' (post-051) column."
                )

            return [(row[0], str(row[1]), row[2]) for row in cur.fetchall()]
    finally:
        conn.close()


def update_file_path(book_uuid: str, new_file_path: str) -> None:
    """Update the file_path column for a book."""
    settings = get_settings()
    db_url = _sync_db_url(settings.DATABASE_URL)
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE books SET file_path = %s WHERE id = %s::uuid",
                (new_file_path, book_uuid),
            )
        conn.commit()
    finally:
        conn.close()


def _compute_new_filename(old_filename: str, int_id: int, uuid: str) -> str | None:
    """Replace _{int_id}.ext with _{uuid}.ext in a filename.

    Returns None if the pattern doesn't match.
    """
    pattern = rf"^(.+)_{re.escape(str(int_id))}(\.\w+)$"
    match = re.match(pattern, old_filename)
    if not match:
        return None
    return f"{match.group(1)}_{uuid}{match.group(2)}"


def rename_book_files_filesystem(
    books: list[tuple[int, str, str | None]],
    *,
    dry_run: bool,
) -> dict[str, int]:
    """Rename epub/pdf files on the local filesystem and update DB."""
    summary: dict[str, int] = {
        "renamed": 0,
        "skipped_no_source": 0,
        "skipped_target_exists": 0,
        "skipped_already_migrated": 0,
        "errors": 0,
    }

    for int_id, uuid, file_path in books:
        if not file_path:
            continue

        new_filename = _compute_new_filename(file_path, int_id, uuid)
        if new_filename is None:
            # file_path doesn't contain the old int id — possibly already migrated
            if uuid in file_path:
                logger.debug("File already uses UUID, skipping: %s", file_path)
                summary["skipped_already_migrated"] += 1
            else:
                logger.warning(
                    "Cannot parse filename for book id_old=%s: %s", int_id, file_path
                )
                summary["errors"] += 1
            continue

        # Determine which directory the file is in
        if file_path.endswith(".epub"):
            base_dir = EPUBS_DIR
        elif file_path.endswith(".pdf"):
            base_dir = PDFS_DIR
        else:
            logger.warning("Unknown file type for book id_old=%s: %s", int_id, file_path)
            summary["errors"] += 1
            continue

        src = base_dir / file_path
        dst = base_dir / new_filename

        if not src.exists():
            logger.debug("Source file not found: %s — skipping", src)
            summary["skipped_no_source"] += 1
            continue

        if dst.exists():
            logger.info("Target already exists, skipping: %s -> %s", src.name, dst.name)
            summary["skipped_target_exists"] += 1
            continue

        if dry_run:
            logger.info("[DRY RUN] Would rename: %s -> %s", src.name, dst.name)
            logger.info("[DRY RUN] Would update file_path: %s -> %s", file_path, new_filename)
            summary["renamed"] += 1
            continue

        try:
            src.rename(dst)
            update_file_path(uuid, new_filename)
            logger.info("Renamed: %s -> %s", src.name, dst.name)
            summary["renamed"] += 1
        except Exception as exc:
            logger.error("Failed to rename %s -> %s: %s", src.name, dst.name, exc)
            summary["errors"] += 1

    return summary


def _get_s3_prefix(file_path: str) -> str | None:
    """Return the S3 prefix for a given file type, or None if unknown."""
    if file_path.endswith(".epub"):
        return "epubs/"
    if file_path.endswith(".pdf"):
        return "pdfs/"
    return None


def _create_s3_client() -> tuple[Any, str] | tuple[None, None]:
    """Create and return an S3 client and bucket name, or None if unavailable."""
    settings = get_settings()
    if not settings.s3_enabled:
        return None, None

    try:
        import boto3  # type: ignore[import-untyped]  # noqa: PLC0415
    except ImportError:
        return None, None

    assert settings.S3_ENDPOINT_URL is not None
    assert settings.S3_BUCKET_NAME is not None

    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
    )
    return client, settings.S3_BUCKET_NAME


def rename_book_files_s3(
    books: list[tuple[int, str, str | None]],
    *,
    dry_run: bool,
) -> dict[str, int]:
    """Rename epub/pdf objects in S3 and update DB."""
    summary: dict[str, int] = {
        "renamed": 0,
        "skipped_no_source": 0,
        "skipped_target_exists": 0,
        "skipped_already_migrated": 0,
        "errors": 0,
    }

    client, bucket = _create_s3_client()
    if client is None:
        logger.info("S3 not available — skipping S3 rename")
        return summary

    def _key_exists(key: str) -> bool:
        try:
            client.head_object(Bucket=bucket, Key=key)
            return True
        except client.exceptions.ClientError:
            return False

    for int_id, uuid, file_path in books:
        if not file_path:
            continue

        new_filename = _compute_new_filename(file_path, int_id, uuid)
        if new_filename is None:
            summary["skipped_already_migrated" if uuid in file_path else "errors"] += 1
            continue

        prefix = _get_s3_prefix(file_path)
        if prefix is None:
            summary["errors"] += 1
            continue

        src_key = f"{prefix}{file_path}"
        dst_key = f"{prefix}{new_filename}"

        if not _key_exists(src_key):
            summary["skipped_no_source"] += 1
            continue

        if _key_exists(dst_key):
            summary["skipped_target_exists"] += 1
            continue

        if dry_run:
            logger.info("[DRY RUN] Would rename S3 object: %s -> %s", src_key, dst_key)
            summary["renamed"] += 1
            continue

        try:
            client.copy_object(
                Bucket=bucket, CopySource={"Bucket": bucket, "Key": src_key}, Key=dst_key,
            )
            client.delete_object(Bucket=bucket, Key=src_key)
            update_file_path(uuid, new_filename)
            logger.info("Renamed S3 object: %s -> %s", src_key, dst_key)
            summary["renamed"] += 1
        except Exception as exc:
            logger.error("Failed to rename S3 object %s -> %s: %s", src_key, dst_key, exc)
            summary["errors"] += 1

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename book epub/pdf files from {title}_{int_id}.ext to {title}_{uuid}.ext"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without making any changes",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )

    dry_run: bool = args.dry_run
    if dry_run:
        logger.info("=== DRY RUN MODE — no files will be changed ===")

    logger.info("Fetching books with files from database …")
    try:
        books = fetch_books_with_files()
    except Exception as exc:
        logger.error("Failed to query database: %s", exc)
        sys.exit(1)

    logger.info("Found %d books with files", len(books))

    # --- Filesystem ---
    logger.info("Processing filesystem book files …")
    fs_summary = rename_book_files_filesystem(books, dry_run=dry_run)
    logger.info(
        "Filesystem summary — renamed=%d skipped_no_source=%d "
        "skipped_target_exists=%d skipped_already_migrated=%d errors=%d",
        fs_summary["renamed"],
        fs_summary["skipped_no_source"],
        fs_summary["skipped_target_exists"],
        fs_summary["skipped_already_migrated"],
        fs_summary["errors"],
    )

    # --- S3 ---
    logger.info("Processing S3 book files …")
    s3_summary = rename_book_files_s3(books, dry_run=dry_run)
    logger.info(
        "S3 summary — renamed=%d skipped_no_source=%d "
        "skipped_target_exists=%d skipped_already_migrated=%d errors=%d",
        s3_summary["renamed"],
        s3_summary["skipped_no_source"],
        s3_summary["skipped_target_exists"],
        s3_summary["skipped_already_migrated"],
        s3_summary["errors"],
    )

    total_errors = fs_summary["errors"] + s3_summary["errors"]
    if total_errors:
        logger.error("%d error(s) occurred — review output above", total_errors)
        sys.exit(1)

    logger.info("Done.")


if __name__ == "__main__":
    main()
