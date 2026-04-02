"""Unit tests for src/scanner.py."""

import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.scanner import scan_vault, _file_mtime_utc
from db_models.models.markdown_files import MarkdownFile


def _make_md_file(tmp_path: Path, name: str, content: str = "# Hello") -> Path:
    """Create a markdown file in the temp directory."""
    f = tmp_path / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content)
    return f


def _mock_session(existing_records=None):
    """Create a mock SQLAlchemy session."""
    session = MagicMock()
    query_mock = MagicMock()
    query_mock.all.return_value = existing_records or []
    session.query.return_value = query_mock
    return session


class TestFileMtimeUtc:
    """Tests for _file_mtime_utc."""

    def test_returns_aware_datetime(self, tmp_path):
        f = _make_md_file(tmp_path, "note.md")
        result = _file_mtime_utc(f)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None


class TestScanVault:
    """Tests for scan_vault."""

    def test_nonexistent_vault_exits(self):
        session = _mock_session()
        with pytest.raises(SystemExit):
            scan_vault(session, "/nonexistent/vault")

    def test_empty_vault_returns_empty(self, tmp_path):
        session = _mock_session()
        results = scan_vault(session, str(tmp_path))
        assert results["new"] == []
        assert results["modified"] == []
        assert results["unchanged"] == []
        assert results["errors"] == []

    def test_new_file_detected(self, tmp_path):
        _make_md_file(tmp_path, "note.md")
        session = _mock_session()
        results = scan_vault(session, str(tmp_path))
        assert len(results["new"]) == 1
        assert results["new"][0].file_name == "note.md"
        assert results["new"][0].file_path == "note.md"
        session.add.assert_called_once()
        session.flush.assert_called_once()

    def test_new_file_in_subdirectory(self, tmp_path):
        _make_md_file(tmp_path, "sub/deep/note.md")
        session = _mock_session()
        results = scan_vault(session, str(tmp_path))
        assert len(results["new"]) == 1
        assert results["new"][0].file_path == "sub/deep/note.md"

    def test_unchanged_file_skipped(self, tmp_path):
        f = _make_md_file(tmp_path, "note.md")
        mtime = _file_mtime_utc(f)

        existing = MarkdownFile(
            id=uuid.uuid4(),
            file_name="note.md",
            file_path="note.md",
            updated_at=mtime + timedelta(seconds=1),  # DB is newer
        )
        session = _mock_session(existing_records=[existing])
        results = scan_vault(session, str(tmp_path))
        assert len(results["unchanged"]) == 1
        assert results["new"] == []
        assert results["modified"] == []

    def test_modified_file_detected(self, tmp_path):
        f = _make_md_file(tmp_path, "note.md")

        old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        existing = MarkdownFile(
            id=uuid.uuid4(),
            file_name="note.md",
            file_path="note.md",
            updated_at=old_time,
        )
        session = _mock_session(existing_records=[existing])
        results = scan_vault(session, str(tmp_path))
        assert len(results["modified"]) == 1
        assert results["modified"][0].file_name == "note.md"

    def test_multiple_files_classified(self, tmp_path):
        _make_md_file(tmp_path, "new.md")
        _make_md_file(tmp_path, "existing.md")

        old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        existing = MarkdownFile(
            id=uuid.uuid4(),
            file_name="existing.md",
            file_path="existing.md",
            updated_at=old_time,
        )
        session = _mock_session(existing_records=[existing])
        results = scan_vault(session, str(tmp_path))
        assert len(results["new"]) == 1
        assert len(results["modified"]) == 1

    def test_non_md_files_ignored(self, tmp_path):
        (tmp_path / "readme.txt").write_text("not markdown")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        _make_md_file(tmp_path, "note.md")
        session = _mock_session()
        results = scan_vault(session, str(tmp_path))
        assert len(results["new"]) == 1
