import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.auth import hash_token


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("NAME_APP", "test-api")
    monkeypatch.setenv("RUN_ENVIRONMENT", "development")


TOKEN = "test-token-file"
TOKEN_HASH = hash_token(TOKEN)


def _mock_api_key():
    key = MagicMock()
    key.id = uuid.uuid4()
    key.key_hash = TOKEN_HASH
    key.name = "test-key"
    return key


@pytest.fixture
def client():
    from src.app import app
    return TestClient(app)


def test_get_file_returns_content(client, tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("# Hello World\nSome content here.")

    file_id = uuid.uuid4()
    api_key = _mock_api_key()

    mock_record = MagicMock()
    mock_record.id = file_id
    mock_record.file_name = "note.md"
    mock_record.file_path = str(md_file)

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        api_key,    # auth lookup
        mock_record,  # file lookup
    ]

    with patch("src.auth._get_session_factory") as mock_factory:
        mock_factory.return_value.return_value = mock_session
        response = client.get(
            f"/obsidian/file/{file_id}",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "note.md"
    assert "Hello World" in data["content"]


def test_get_file_not_found_in_db(client):
    file_id = uuid.uuid4()
    api_key = _mock_api_key()

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        api_key,  # auth lookup
        None,     # file lookup
    ]

    with patch("src.auth._get_session_factory") as mock_factory:
        mock_factory.return_value.return_value = mock_session
        response = client.get(
            f"/obsidian/file/{file_id}",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )

    assert response.status_code == 404


def test_get_file_missing_on_disk(client, tmp_path):
    file_id = uuid.uuid4()
    api_key = _mock_api_key()

    mock_record = MagicMock()
    mock_record.id = file_id
    mock_record.file_name = "gone.md"
    mock_record.file_path = str(tmp_path / "nonexistent.md")

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.side_effect = [
        api_key,
        mock_record,
    ]

    with patch("src.auth._get_session_factory") as mock_factory:
        mock_factory.return_value.return_value = mock_session
        response = client.get(
            f"/obsidian/file/{file_id}",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )

    assert response.status_code == 404


def test_get_file_missing_auth(client):
    file_id = uuid.uuid4()
    response = client.get(f"/obsidian/file/{file_id}")
    assert response.status_code in (401, 403)
