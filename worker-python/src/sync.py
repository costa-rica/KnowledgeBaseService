"""Obsidian vault sync via Obsidian Headless."""

import os
import subprocess

from loguru import logger

SYNC_TIMEOUT_SECONDS = 300


def sync_vault() -> None:
    """Synchronize the vault with Obsidian cloud in bidirectional mode.

    Reads VAULT_PATH from the environment to determine the target directory.
    Uses the ``ob`` CLI (obsidian-headless), explicitly sets the vault to
    bidirectional mode, then runs a sync so server-side file updates can
    propagate to other Obsidian devices.

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

    logger.info("Starting bidirectional vault sync: {}", vault_path)

    _run_ob_command(
        ["ob", "sync-config", "--path", vault_path, "--mode", "bidirectional"],
        "Vault sync-config failed",
    )
    _run_ob_command(
        ["ob", "sync", "--path", vault_path],
        "Vault sync failed",
    )

    logger.info("Vault sync completed successfully")


def _run_ob_command(command: list[str], error_message: str) -> None:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=SYNC_TIMEOUT_SECONDS,
        )

        if result.returncode != 0:
            logger.error(
                "{} (exit code {}): {}",
                error_message,
                result.returncode,
                result.stderr.strip(),
            )
            raise SystemExit(1)

        if result.stdout.strip():
            logger.debug("ob output: {}", result.stdout.strip())
        if result.stderr.strip():
            logger.debug("ob stderr: {}", result.stderr.strip())

    except FileNotFoundError:
        logger.critical(
            "ob command not found. "
            "Install obsidian-headless: npm install -g obsidian-headless"
        )
        raise SystemExit(1)

    except subprocess.TimeoutExpired:
        logger.critical("ob command timed out after {} seconds", SYNC_TIMEOUT_SECONDS)
        raise SystemExit(1)
