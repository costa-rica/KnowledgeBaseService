"""Obsidian vault sync — one-way pull from Obsidian cloud via Obsidian Headless."""

import os
import subprocess

from loguru import logger


def sync_vault() -> None:
    """Pull the latest vault state from Obsidian cloud.

    Reads VAULT_PATH from the environment to determine the target directory.
    Uses the ``ob`` CLI (obsidian-headless) in mirror-remote mode so the local
    vault is a read-only replica — any local changes are reverted to match the
    remote state.

    Raises:
        SystemExit: If VAULT_PATH is missing or the sync command fails.
    """
    vault_path = os.environ.get("VAULT_PATH", "").strip()
    if not vault_path:
        logger.critical("VAULT_PATH environment variable is missing or empty")
        raise SystemExit(1)

    if not os.path.isdir(vault_path):
        logger.critical("VAULT_PATH does not exist: {}", vault_path)
        raise SystemExit(1)

    logger.info("Starting vault sync: {}", vault_path)

    try:
        result = subprocess.run(
            ["ob", "sync", "--path", vault_path],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            logger.error(
                "Vault sync failed (exit code {}): {}",
                result.returncode,
                result.stderr.strip(),
            )
            raise SystemExit(1)

        logger.info("Vault sync completed successfully")
        if result.stdout.strip():
            logger.debug("Sync output: {}", result.stdout.strip())

    except FileNotFoundError:
        logger.critical(
            "ob command not found. "
            "Install obsidian-headless: npm install -g obsidian-headless"
        )
        raise SystemExit(1)

    except subprocess.TimeoutExpired:
        logger.critical("Vault sync timed out after 300 seconds")
        raise SystemExit(1)
