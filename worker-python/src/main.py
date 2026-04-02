"""Main orchestrator — runs vault sync then scan + embed."""

import os
import sys

from loguru import logger

from src.logger import setup_logger
from src.sync import sync_vault
from src.scanner import scan_vault
from src.embedder import generate_embeddings
from db_models.database import get_engine, get_session_factory


def run() -> None:
    """Execute the full worker pipeline.

    1. Initialize logging.
    2. Sync the Obsidian vault (one-way pull).
    3. Scan the vault for new/modified files.
    4. Generate and upsert embeddings.
    5. Commit the database transaction.
    """
    setup_logger()
    logger.info("Worker started")

    # Job 1: Vault sync.
    sync_vault()

    # Job 2: Scan and embed.
    vault_path = os.environ.get("VAULT_PATH", "").strip()
    if not vault_path:
        logger.critical("VAULT_PATH environment variable is missing or empty")
        sys.exit(1)

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        logger.critical("DATABASE_URL environment variable is missing or empty")
        sys.exit(1)

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
            counts = generate_embeddings(
                session, vault_path, new_files, modified_files
            )

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
