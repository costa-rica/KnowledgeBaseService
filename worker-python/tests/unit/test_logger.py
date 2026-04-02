"""Unit tests for src/logger.py."""

import os
import pytest
from unittest.mock import patch

from src.logger import _validate_env_vars, setup_logger, VALID_ENVIRONMENTS


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure logger env vars are cleared before each test."""
    for var in ("NAME_APP", "RUN_ENVIRONMENT", "PATH_TO_LOGS",
                "LOG_MAX_SIZE_IN_MB", "LOG_MAX_FILES"):
        monkeypatch.delenv(var, raising=False)


class TestValidateEnvVars:
    """Tests for _validate_env_vars."""

    def test_missing_name_app_exits(self, monkeypatch):
        monkeypatch.setenv("RUN_ENVIRONMENT", "development")
        with pytest.raises(SystemExit):
            _validate_env_vars()

    def test_empty_name_app_exits(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "  ")
        monkeypatch.setenv("RUN_ENVIRONMENT", "development")
        with pytest.raises(SystemExit):
            _validate_env_vars()

    def test_missing_run_environment_exits(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "test-app")
        with pytest.raises(SystemExit):
            _validate_env_vars()

    def test_invalid_run_environment_exits(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "staging")
        with pytest.raises(SystemExit):
            _validate_env_vars()

    def test_development_does_not_require_path_to_logs(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "development")
        name, env, path = _validate_env_vars()
        assert name == "test-app"
        assert env == "development"
        assert path is None

    def test_testing_requires_path_to_logs(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "testing")
        with pytest.raises(SystemExit):
            _validate_env_vars()

    def test_production_requires_path_to_logs(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "production")
        with pytest.raises(SystemExit):
            _validate_env_vars()

    def test_testing_with_path_to_logs_succeeds(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "testing")
        monkeypatch.setenv("PATH_TO_LOGS", "/tmp/logs")
        name, env, path = _validate_env_vars()
        assert name == "test-app"
        assert env == "testing"
        assert path == "/tmp/logs"

    def test_production_with_path_to_logs_succeeds(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "production")
        monkeypatch.setenv("PATH_TO_LOGS", "/tmp/logs")
        name, env, path = _validate_env_vars()
        assert name == "test-app"
        assert env == "production"
        assert path == "/tmp/logs"


class TestSetupLogger:
    """Tests for setup_logger."""

    def test_development_setup_succeeds(self, monkeypatch):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "development")
        setup_logger()

    def test_testing_setup_succeeds(self, monkeypatch, tmp_path):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "testing")
        monkeypatch.setenv("PATH_TO_LOGS", str(tmp_path))
        setup_logger()
        assert (tmp_path / "test-app.log").exists()

    def test_production_setup_succeeds(self, monkeypatch, tmp_path):
        monkeypatch.setenv("NAME_APP", "test-app")
        monkeypatch.setenv("RUN_ENVIRONMENT", "production")
        monkeypatch.setenv("PATH_TO_LOGS", str(tmp_path))
        setup_logger()
        assert (tmp_path / "test-app.log").exists()
