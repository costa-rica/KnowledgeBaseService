"""Unit tests for src/embedder.py."""

import uuid
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path

import numpy as np
import pytest

from src.embedder import (
    generate_embeddings,
    _read_file_content,
    SNIPPET_LENGTH,
)
from db_models.models.markdown_files import MarkdownFile
from db_models.models.markdown_file_embeddings import (
    MarkdownFileEmbedding,
    EMBEDDING_DIMENSIONS,
)


def _make_record(file_name: str, file_path: str) -> MarkdownFile:
    """Create a MarkdownFile record for testing."""
    return MarkdownFile(
        id=uuid.uuid4(),
        file_name=file_name,
        file_path=file_path,
    )


def _mock_session():
    """Create a mock SQLAlchemy session with query support."""
    session = MagicMock()
    return session


def _fake_vector():
    """Return a fake embedding vector of the right shape."""
    return np.zeros(EMBEDDING_DIMENSIONS, dtype=np.float32)


class TestReadFileContent:
    """Tests for _read_file_content."""

    def test_reads_existing_file(self, tmp_path):
        f = tmp_path / "note.md"
        f.write_text("hello world", encoding="utf-8")
        result = _read_file_content(str(tmp_path), "note.md")
        assert result == "hello world"

    def test_returns_none_for_missing_file(self, tmp_path):
        result = _read_file_content(str(tmp_path), "missing.md")
        assert result is None

    def test_reads_file_in_subdirectory(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        f = sub / "note.md"
        f.write_text("nested", encoding="utf-8")
        result = _read_file_content(str(tmp_path), "sub/note.md")
        assert result == "nested"


class TestGenerateEmbeddings:
    """Tests for generate_embeddings."""

    @patch("src.embedder._get_model")
    def test_new_file_creates_embedding(self, mock_get_model, tmp_path):
        model = MagicMock()
        model.encode.return_value = _fake_vector()
        mock_get_model.return_value = model

        f = tmp_path / "note.md"
        f.write_text("test content")

        record = _make_record("note.md", "note.md")
        session = _mock_session()

        counts = generate_embeddings(session, str(tmp_path), [record], [])
        assert counts["embedded"] == 1
        assert counts["errors"] == 0
        session.add.assert_called_once()
        session.flush.assert_called_once()

    @patch("src.embedder._get_model")
    def test_modified_file_updates_existing_embedding(self, mock_get_model, tmp_path):
        model = MagicMock()
        model.encode.return_value = _fake_vector()
        mock_get_model.return_value = model

        f = tmp_path / "note.md"
        f.write_text("updated content")

        record = _make_record("note.md", "note.md")

        existing_embedding = MagicMock(spec=MarkdownFileEmbedding)
        session = _mock_session()
        query_chain = session.query.return_value.filter_by.return_value
        query_chain.first.return_value = existing_embedding

        counts = generate_embeddings(session, str(tmp_path), [], [record])
        assert counts["embedded"] == 1
        assert counts["errors"] == 0

    @patch("src.embedder._get_model")
    def test_modified_file_missing_embedding_creates_new(self, mock_get_model, tmp_path):
        model = MagicMock()
        model.encode.return_value = _fake_vector()
        mock_get_model.return_value = model

        f = tmp_path / "note.md"
        f.write_text("content")

        record = _make_record("note.md", "note.md")

        session = _mock_session()
        query_chain = session.query.return_value.filter_by.return_value
        query_chain.first.return_value = None  # No existing embedding

        counts = generate_embeddings(session, str(tmp_path), [], [record])
        assert counts["embedded"] == 1
        session.add.assert_called_once()

    @patch("src.embedder._get_model")
    def test_unreadable_file_counted_as_error(self, mock_get_model, tmp_path):
        model = MagicMock()
        mock_get_model.return_value = model

        record = _make_record("missing.md", "missing.md")
        session = _mock_session()

        counts = generate_embeddings(session, str(tmp_path), [record], [])
        assert counts["embedded"] == 0
        assert counts["errors"] == 1
        model.encode.assert_not_called()

    @patch("src.embedder._get_model")
    def test_snippet_truncated(self, mock_get_model, tmp_path):
        model = MagicMock()
        model.encode.return_value = _fake_vector()
        mock_get_model.return_value = model

        long_content = "x" * (SNIPPET_LENGTH + 100)
        f = tmp_path / "long.md"
        f.write_text(long_content)

        record = _make_record("long.md", "long.md")
        session = _mock_session()

        generate_embeddings(session, str(tmp_path), [record], [])
        # Verify the added embedding has a truncated snippet.
        added = session.add.call_args[0][0]
        assert len(added.snippet) == SNIPPET_LENGTH

    @patch("src.embedder._get_model")
    def test_multiple_files_processed(self, mock_get_model, tmp_path):
        model = MagicMock()
        model.encode.return_value = _fake_vector()
        mock_get_model.return_value = model

        for name in ["a.md", "b.md", "c.md"]:
            (tmp_path / name).write_text(f"content of {name}")

        records = [_make_record(n, n) for n in ["a.md", "b.md", "c.md"]]
        session = _mock_session()

        counts = generate_embeddings(session, str(tmp_path), records, [])
        assert counts["embedded"] == 3
        assert counts["errors"] == 0
