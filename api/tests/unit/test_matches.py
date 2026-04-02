import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.auth import hash_token


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("NAME_APP", "test-api")
    monkeypatch.setenv("RUN_ENVIRONMENT", "development")


TOKEN = "test-token-matches"
TOKEN_HASH = hash_token(TOKEN)


def _mock_api_key():
    key = MagicMock()
    key.id = uuid.uuid4()
    key.key_hash = TOKEN_HASH
    key.name = "test-key"
    return key


def _mock_match_row():
    row = MagicMock()
    row.id = uuid.uuid4()
    row.file_name = "deep-work.md"
    row.file_path = "productivity/deep-work.md"
    row.score = 0.94
    row.snippet = "First 500 characters..."
    return row


@pytest.fixture
def client():
    from src.app import app
    return TestClient(app)


def test_matches_returns_results(client):
    api_key = _mock_api_key()
    match_row = _mock_match_row()

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = api_key
    mock_session.execute.return_value.fetchall.return_value = [match_row]

    fake_embedding = [0.1] * 384

    with patch("src.auth._get_session_factory") as mock_factory, \
         patch("src.routes.obsidian._get_model") as mock_model:
        mock_factory.return_value.return_value = mock_session
        mock_model.return_value.encode.return_value = MagicMock(tolist=lambda: fake_embedding)

        response = client.post(
            "/obsidian/matches",
            json={"question": "What is deep work?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["matches"]) == 1
    assert data["matches"][0]["file_name"] == "deep-work.md"
    assert data["matches"][0]["score"] == 0.94


def test_matches_empty_results(client):
    api_key = _mock_api_key()

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = api_key
    mock_session.execute.return_value.fetchall.return_value = []

    fake_embedding = [0.1] * 384

    with patch("src.auth._get_session_factory") as mock_factory, \
         patch("src.routes.obsidian._get_model") as mock_model:
        mock_factory.return_value.return_value = mock_session
        mock_model.return_value.encode.return_value = MagicMock(tolist=lambda: fake_embedding)

        response = client.post(
            "/obsidian/matches",
            json={"question": "nonexistent topic"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )

    assert response.status_code == 200
    assert response.json()["matches"] == []


def test_matches_missing_auth(client):
    response = client.post("/obsidian/matches", json={"question": "test"})
    assert response.status_code in (401, 403)
