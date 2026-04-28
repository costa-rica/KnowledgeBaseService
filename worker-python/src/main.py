"""Main orchestrator — syncs vault, prepares daily files, then scans + embeds."""

import os
import sys

from loguru import logger

from db_models.database import get_engine, get_session_factory
from src.daily_files import prepare_daily_root_files
from src.embedder import generate_embeddings
from src.logger import setup_logger
from src.scanner import scan_vault
from src.sync import sync_vault


def run() -> None:
    """Execute the full worker pipeline.

    1. Initialize logging.
    2. Validate required environment.
    3. Run bidirectional Obsidian sync to pull latest remote state.
    4. Prepare root-level daily/messages/journal files.
    5. Run bidirectional Obsidian sync again to push file operations.
    6. Scan the vault for new/modified files.
    7. Generate and upsert embeddings.
    8. Commit the database transaction.
    """
    setup_logger()
    logger.info("Worker started")

    vault_path = os.environ.get("VAULT_PATH", "").strip()
    if not vault_path:
        logger.critical("VAULT_PATH environment variable is missing or empty")
        sys.exit(1)

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        logger.critical("DATABASE_URL environment variable is missing or empty")
        sys.exit(1)

    # Job 1: Pull latest remote state before local file operations.
    sync_vault()

    # Job 2: Prepare root-level daily working files and archive/delete yesterday.
    prepare_daily_root_files(vault_path)

    # Job 3: Push created/moved/deleted files to other Obsidian devices.
    sync_vault()

    # Job 4: Scan and embed.
    engine = get_engine(database_url)
    Session = get_session_factory(engine)
    session = Session()

    try:
        # Scan vault for changes.
        results = scan_vault(session, vault_path)

        new_files = results["new"]
        modified_files = results["modified"]

        if not new_files and not modified_files:
            logger.info("No new or modified files — nothing to embed")
        else:
            # Generate embeddings for changed files.
            generate_embeddings(session, vault_path, new_files, modified_files)

        session.commit()
        logger.info("Database transaction committed successfully")

    except SystemExit:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        logger.critical("Unhandled error during worker run: {}", exc)
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()

    logger.info("Worker finished successfully")
