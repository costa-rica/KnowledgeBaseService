"""Unit tests for src/sync.py."""

import subprocess
import pytest
from unittest.mock import patch, MagicMock

from src.sync import sync_vault


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Clear VAULT_PATH before each test."""
    monkeypatch.delenv("VAULT_PATH", raising=False)


class TestSyncVault:
    """Tests for sync_vault."""

    def test_missing_vault_path_exits(self):
        with pytest.raises(SystemExit):
            sync_vault()

    def test_empty_vault_path_exits(self, monkeypatch):
        monkeypatch.setenv("VAULT_PATH", "  ")
        with pytest.raises(SystemExit):
            sync_vault()

    def test_nonexistent_vault_path_exits(self, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path / "does_not_exist"))
        with pytest.raises(SystemExit):
            sync_vault()

    @patch("src.sync.subprocess.run")
    def test_successful_sync(self, mock_run, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_run.return_value = MagicMock(
            returncode=0, stdout="synced", stderr=""
        )
        sync_vault()  # should not raise
        mock_run.assert_called_once()
        args = mock_run.call_args
        assert "obsidianctl" in args[0][0]
        assert "--pull-only" in args[0][0]

    @patch("src.sync.subprocess.run")
    def test_sync_nonzero_exit_code_exits(self, mock_run, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="sync error"
        )
        with pytest.raises(SystemExit):
            sync_vault()

    @patch("src.sync.subprocess.run", side_effect=FileNotFoundError)
    def test_missing_obsidianctl_exits(self, mock_run, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        with pytest.raises(SystemExit):
            sync_vault()

    @patch(
        "src.sync.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="obsidianctl", timeout=300),
    )
    def test_sync_timeout_exits(self, mock_run, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        with pytest.raises(SystemExit):
            sync_vault()
