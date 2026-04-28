"""Unit tests for src/sync.py."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

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
    def test_successful_sync_sets_bidirectional_mode_then_syncs(
        self, mock_run, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_run.return_value = MagicMock(returncode=0, stdout="synced", stderr="")

        sync_vault()

        assert mock_run.call_count == 2
        config_call = mock_run.call_args_list[0]
        sync_call = mock_run.call_args_list[1]
        assert config_call.args[0] == [
            "ob",
            "sync-config",
            "--path",
            str(tmp_path),
            "--mode",
            "bidirectional",
        ]
        assert sync_call.args[0] == ["ob", "sync", "--path", str(tmp_path)]

    @patch("src.sync.subprocess.run")
    def test_sync_config_nonzero_exit_code_exits(self, mock_run, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="config error")

        with pytest.raises(SystemExit):
            sync_vault()

    @patch("src.sync.subprocess.run")
    def test_sync_nonzero_exit_code_exits(self, mock_run, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="sync error"),
        ]

        with pytest.raises(SystemExit):
            sync_vault()

    @patch("src.sync.subprocess.run", side_effect=FileNotFoundError)
    def test_missing_ob_exits(self, mock_run, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        with pytest.raises(SystemExit):
            sync_vault()

    @patch(
        "src.sync.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="ob", timeout=300),
    )
    def test_sync_timeout_exits(self, mock_run, monkeypatch, tmp_path):
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        with pytest.raises(SystemExit):
            sync_vault()
