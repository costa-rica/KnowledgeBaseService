import hashlib
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth import hash_token, verify_token


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("NAME_APP", "test-api")
    monkeypatch.setenv("RUN_ENVIRONMENT", "development")


def _make_app():
    app = FastAPI()

    @app.get("/protected", dependencies=[])
    def protected(api_key=__import__("fastapi").Depends(verify_token)):
        return {"name": api_key.name}

    return app


def _fake_api_key(token: str):
    key = MagicMock()
    key.id = uuid.uuid4()
    key.key_hash = hash_token(token)
    key.name = "test-key"
    return key


def test_hash_token_is_sha256():
    token = "my-secret-token"
    expected = hashlib.sha256(token.encode()).hexdigest()
    assert hash_token(token) == expected


def test_valid_token_returns_200():
    token = "valid-token"
    api_key = _fake_api_key(token)

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = api_key

    app = _make_app()

    with patch("src.auth._get_session_factory") as mock_factory:
        mock_factory.return_value.return_value = mock_session
        client = TestClient(app)
        response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["name"] == "test-key"


def test_invalid_token_returns_401():
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    app = _make_app()

    with patch("src.auth._get_session_factory") as mock_factory:
        mock_factory.return_value.return_value = mock_session
        client = TestClient(app)
        response = client.get("/protected", headers={"Authorization": "Bearer bad-token"})

    assert response.status_code == 401


def test_missing_auth_header_returns_unauthorized():
    app = _make_app()
    client = TestClient(app)
    response = client.get("/protected")
    assert response.status_code in (401, 403)
