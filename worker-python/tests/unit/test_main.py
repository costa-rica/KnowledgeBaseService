"""Unit tests for src/main.py."""

import pytest
from unittest.mock import patch, MagicMock


class TestRun:
    """Tests for the run() orchestrator."""

    @patch("src.main.get_session_factory")
    @patch("src.main.get_engine")
    @patch("src.main.generate_embeddings")
    @patch("src.main.scan_vault")
    @patch("src.main.sync_vault")
    @patch("src.main.setup_logger")
    def test_full_pipeline_no_changes(
        self,
        mock_setup_logger,
        mock_sync_vault,
        mock_scan_vault,
        mock_generate_embeddings,
        mock_get_engine,
        mock_get_session_factory,
        monkeypatch,
    ):
        monkeypatch.setenv("VAULT_PATH", "/tmp/vault")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")

        mock_session = MagicMock()
        mock_get_session_factory.return_value = MagicMock(return_value=mock_session)
        mock_scan_vault.return_value = {
            "new": [],
            "modified": [],
            "unchanged": [],
            "errors": [],
        }

        from src.main import run
        run()

        mock_setup_logger.assert_called_once()
        mock_sync_vault.assert_called_once()
        mock_scan_vault.assert_called_once_with(mock_session, "/tmp/vault")
        mock_generate_embeddings.assert_not_called()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("src.main.get_session_factory")
    @patch("src.main.get_engine")
    @patch("src.main.generate_embeddings")
    @patch("src.main.scan_vault")
    @patch("src.main.sync_vault")
    @patch("src.main.setup_logger")
    def test_full_pipeline_with_new_files(
        self,
        mock_setup_logger,
        mock_sync_vault,
        mock_scan_vault,
        mock_generate_embeddings,
        mock_get_engine,
        mock_get_session_factory,
        monkeypatch,
    ):
        monkeypatch.setenv("VAULT_PATH", "/tmp/vault")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")

        mock_session = MagicMock()
        mock_get_session_factory.return_value = MagicMock(return_value=mock_session)

        new_record = MagicMock()
        mock_scan_vault.return_value = {
            "new": [new_record],
            "modified": [],
            "unchanged": [],
            "errors": [],
        }
        mock_generate_embeddings.return_value = {"embedded": 1, "errors": 0}

        from src.main import run
        run()

        mock_generate_embeddings.assert_called_once_with(
            mock_session, "/tmp/vault", [new_record], []
        )
        mock_session.commit.assert_called_once()

    @patch("src.main.setup_logger")
    def test_missing_vault_path_exits(self, mock_setup_logger, monkeypatch):
        monkeypatch.delenv("VAULT_PATH", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")

        # sync_vault also checks VAULT_PATH, so mock it to isolate this test.
        with patch("src.main.sync_vault"):
            from src.main import run
            with pytest.raises(SystemExit):
                run()

    @patch("src.main.setup_logger")
    def test_missing_database_url_exits(self, mock_setup_logger, monkeypatch):
        monkeypatch.setenv("VAULT_PATH", "/tmp/vault")
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with patch("src.main.sync_vault"):
            from src.main import run
            with pytest.raises(SystemExit):
                run()

    @patch("src.main.get_session_factory")
    @patch("src.main.get_engine")
    @patch("src.main.scan_vault", side_effect=RuntimeError("db error"))
    @patch("src.main.sync_vault")
    @patch("src.main.setup_logger")
    def test_exception_rolls_back_and_exits(
        self,
        mock_setup_logger,
        mock_sync_vault,
        mock_scan_vault,
        mock_get_engine,
        mock_get_session_factory,
        monkeypatch,
    ):
        monkeypatch.setenv("VAULT_PATH", "/tmp/vault")
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")

        mock_session = MagicMock()
        mock_get_session_factory.return_value = MagicMock(return_value=mock_session)

        from src.main import run
        with pytest.raises(SystemExit):
            run()

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
