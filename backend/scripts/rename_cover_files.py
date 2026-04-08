"""Script to rename book cover files from {int_id}.ext to {uuid}.ext.

Run this after Alembic migration 050 (which added the uuid column to books)
and before migration 051 (which drops the int id columns).

Usage:
    cd backend && uv run python -m scripts.rename_cover_files
    cd backend && uv run python -m scripts.rename_cover_files --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

import psycopg2

# ---------------------------------------------------------------------------
# Config import — path constants and settings live in src.config
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import BOOK_COVERS_DIR, get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def _sync_db_url(async_url: str) -> str:
    """Convert an async postgresql+asyncpg:// URL to a plain psycopg2 URL."""
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


def fetch_book_id_uuid_pairs() -> list[tuple[int, str]]:
    """Return [(id, uuid), ...] for every row in books."""
    settings = get_settings()
    db_url = _sync_db_url(settings.DATABASE_URL)
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, uuid FROM books ORDER BY id")
            rows: list[tuple[int, str]] = cur.fetchall()
        return rows
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Filesystem rename
# ---------------------------------------------------------------------------


def rename_covers_filesystem(
    books: list[tuple[int, str]],
    covers_dir: Path,
    *,
    dry_run: bool,
) -> dict[str, int]:
    """Rename cover files on the local filesystem.

    Returns a summary dict with counts: renamed, skipped_no_source,
    skipped_target_exists, errors.
    """
    summary: dict[str, int] = {
        "renamed": 0,
        "skipped_no_source": 0,
        "skipped_target_exists": 0,
        "errors": 0,
    }

    if not covers_dir.is_dir():
        logger.warning(
            "Covers directory does not exist: %s — skipping filesystem rename", covers_dir
        )
        return summary

    for int_id, uuid in books:
        # Find all files matching {int_id}.*
        matches = list(covers_dir.glob(f"{int_id}.*"))

        if not matches:
            logger.debug("No source file found for book id=%s (uuid=%s) — skipping", int_id, uuid)
            summary["skipped_no_source"] += 1
            continue

        for src in matches:
            suffix = src.suffix
            dst = covers_dir / f"{uuid}{suffix}"

            if dst.exists():
                logger.info(
                    "Target already exists, skipping: %s -> %s",
                    src.name,
                    dst.name,
                )
                summary["skipped_target_exists"] += 1
                continue

            if dry_run:
                logger.info("[DRY RUN] Would rename: %s -> %s", src.name, dst.name)
                summary["renamed"] += 1
                continue

            try:
                src.rename(dst)
                logger.info("Renamed: %s -> %s", src.name, dst.name)
                summary["renamed"] += 1
            except OSError as exc:
                logger.error("Failed to rename %s -> %s: %s", src.name, dst.name, exc)
                summary["errors"] += 1

    return summary


# ---------------------------------------------------------------------------
# S3 rename (secondary / best-effort)
# ---------------------------------------------------------------------------


def rename_covers_s3(
    books: list[tuple[int, str]],
    *,
    dry_run: bool,
) -> dict[str, int]:
    """Rename cover objects in S3 by copying then deleting.

    Returns a summary dict with counts: renamed, skipped_no_source,
    skipped_target_exists, errors.
    """
    summary: dict[str, int] = {
        "renamed": 0,
        "skipped_no_source": 0,
        "skipped_target_exists": 0,
        "errors": 0,
    }

    settings = get_settings()
    if not settings.s3_enabled:
        logger.info("S3 not configured — skipping S3 rename")
        return summary

    try:
        import boto3  # type: ignore[import-untyped]  # noqa: PLC0415
    except ImportError:
        logger.warning("boto3 not installed — skipping S3 rename")
        return summary

    assert settings.S3_ENDPOINT_URL is not None  # satisfied by s3_enabled check
    assert settings.S3_BUCKET_NAME is not None

    client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
    )
    bucket = settings.S3_BUCKET_NAME
    prefix = "book-covers/"

    def _list_keys(pattern_prefix: str) -> list[str]:
        response = client.list_objects_v2(Bucket=bucket, Prefix=pattern_prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]

    def _key_exists(key: str) -> bool:
        try:
            client.head_object(Bucket=bucket, Key=key)
            return True
        except client.exceptions.ClientError:
            return False

    for int_id, uuid in books:
        # List all objects whose key starts with book-covers/{int_id}.
        candidate_prefix = f"{prefix}{int_id}."
        src_keys = _list_keys(candidate_prefix)

        if not src_keys:
            logger.debug("No S3 object found for book id=%s (uuid=%s) — skipping", int_id, uuid)
            summary["skipped_no_source"] += 1
            continue

        for src_key in src_keys:
            # Derive the extension from the source key basename
            src_basename = src_key.split("/")[-1]
            try:
                suffix = "." + src_basename.split(".", 1)[1]
            except IndexError:
                suffix = ""
            dst_key = f"{prefix}{uuid}{suffix}"

            if _key_exists(dst_key):
                logger.info("S3 target already exists, skipping: %s -> %s", src_key, dst_key)
                summary["skipped_target_exists"] += 1
                continue

            if dry_run:
                logger.info("[DRY RUN] Would rename S3 object: %s -> %s", src_key, dst_key)
                summary["renamed"] += 1
                continue

            try:
                # S3 has no rename — copy then delete
                client.copy_object(
                    Bucket=bucket,
                    CopySource={"Bucket": bucket, "Key": src_key},
                    Key=dst_key,
                )
                client.delete_object(Bucket=bucket, Key=src_key)
                logger.info("Renamed S3 object: %s -> %s", src_key, dst_key)
                summary["renamed"] += 1
            except Exception as exc:
                logger.error("Failed to rename S3 object %s -> %s: %s", src_key, dst_key, exc)
                summary["errors"] += 1

    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename book cover files from {int_id}.ext to {uuid}.ext"
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

    logger.info("Fetching book id/uuid pairs from database …")
    try:
        books = fetch_book_id_uuid_pairs()
    except Exception as exc:
        logger.error("Failed to query database: %s", exc)
        sys.exit(1)

    logger.info("Found %d books", len(books))

    # --- Filesystem ---
    logger.info("Processing filesystem covers in: %s", BOOK_COVERS_DIR)
    fs_summary = rename_covers_filesystem(books, BOOK_COVERS_DIR, dry_run=dry_run)
    logger.info(
        "Filesystem summary — renamed=%d skipped_no_source=%d skipped_target_exists=%d errors=%d",
        fs_summary["renamed"],
        fs_summary["skipped_no_source"],
        fs_summary["skipped_target_exists"],
        fs_summary["errors"],
    )

    # --- S3 ---
    logger.info("Processing S3 covers …")
    s3_summary = rename_covers_s3(books, dry_run=dry_run)
    logger.info(
        "S3 summary — renamed=%d skipped_no_source=%d skipped_target_exists=%d errors=%d",
        s3_summary["renamed"],
        s3_summary["skipped_no_source"],
        s3_summary["skipped_target_exists"],
        s3_summary["errors"],
    )

    total_errors = fs_summary["errors"] + s3_summary["errors"]
    if total_errors:
        logger.error("%d error(s) occurred — review output above", total_errors)
        sys.exit(1)

    logger.info("Done.")


if __name__ == "__main__":
    main()
