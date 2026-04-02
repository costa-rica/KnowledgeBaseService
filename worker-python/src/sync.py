"""Obsidian vault sync — one-way pull from Obsidian cloud."""

import os
import subprocess

from loguru import logger


def sync_vault() -> None:
    """Pull the latest vault state from Obsidian cloud.

    Reads VAULT_PATH from the environment to determine the target directory.
    Executes the Obsidian headless CLI to perform a one-way pull.
    The local vault is treated as a read-only replica.

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
            ["obsidianctl", "sync", "--vault", vault_path, "--pull-only"],
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
            "obsidianctl command not found. "
            "Ensure Obsidian CLI is installed and on PATH."
        )
        raise SystemExit(1)

    except subprocess.TimeoutExpired:
        logger.critical("Vault sync timed out after 300 seconds")
        raise SystemExit(1)
