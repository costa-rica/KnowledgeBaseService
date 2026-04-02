"""File scanner — walks the vault and diffs against the database."""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from db_models.models.markdown_files import MarkdownFile


def _file_mtime_utc(path: Path) -> datetime:
    """Return the file's mtime as a timezone-aware UTC datetime."""
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def scan_vault(session: Session, vault_path: str) -> dict:
    """Scan the vault for new and modified markdown files.

    Walks the vault directory recursively, compares each file's mtime
    against the database, and classifies files as new, modified, or
    unchanged.

    New files are inserted into markdown_files. Modified files have
    their updated_at refreshed. Unchanged files are skipped.

    Args:
        session: An open SQLAlchemy session.
        vault_path: Absolute path to the Obsidian vault root.

    Returns:
        A dict with lists of MarkdownFile records keyed by status:
        {"new": [...], "modified": [...], "unchanged": [...], "errors": [...]}.
    """
    vault = Path(vault_path)
    if not vault.is_dir():
        logger.critical("Vault path does not exist: {}", vault_path)
        raise SystemExit(1)

    # Build a lookup of existing files by their relative path.
    existing_records = session.query(MarkdownFile).all()
    db_lookup: dict[str, MarkdownFile] = {
        record.file_path: record for record in existing_records
    }

    results: dict[str, list] = {
        "new": [],
        "modified": [],
        "unchanged": [],
        "errors": [],
    }

    md_files = list(vault.rglob("*.md"))
    logger.info("Found {} markdown files in vault", len(md_files))

    for md_file in md_files:
        try:
            relative_path = str(md_file.relative_to(vault))
            file_name = md_file.name
            mtime = _file_mtime_utc(md_file)

            if relative_path not in db_lookup:
                # New file.
                record = MarkdownFile(
                    id=uuid.uuid4(),
                    file_name=file_name,
                    file_path=relative_path,
                    updated_at=mtime,
                )
                session.add(record)
                results["new"].append(record)
            else:
                record = db_lookup[relative_path]
                # Compare mtimes. If the record's updated_at is naive,
                # treat it as UTC for comparison.
                db_time = record.updated_at
                if db_time.tzinfo is None:
                    db_time = db_time.replace(tzinfo=timezone.utc)

                if mtime > db_time:
                    # Modified file.
                    record.updated_at = mtime
                    results["modified"].append(record)
                else:
                    # Unchanged.
                    results["unchanged"].append(record)

        except Exception as exc:
            logger.error("Error processing {}: {}", md_file, exc)
            results["errors"].append(str(md_file))

    session.flush()

    logger.info(
        "Scan complete: {} new, {} modified, {} unchanged, {} errors",
        len(results["new"]),
        len(results["modified"]),
        len(results["unchanged"]),
        len(results["errors"]),
    )

    return results
