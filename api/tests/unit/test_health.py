import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("NAME_APP", "test-api")
    monkeypatch.setenv("RUN_ENVIRONMENT", "development")


@pytest.fixture
def client():
    from src.app import app
    return TestClient(app)


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_returns_html(client):
    response = client.get("/")
    assert "text/html" in response.headers["content-type"]


def test_index_contains_app_name(client):
    response = client.get("/")
    assert "Knowledge Base Service" in response.text
