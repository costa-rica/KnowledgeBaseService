import os
import sys
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("NAME_APP", "RUN_ENVIRONMENT", "PATH_TO_LOGS"):
        monkeypatch.delenv(var, raising=False)


def test_missing_name_app():
    with patch.dict(os.environ, {"RUN_ENVIRONMENT": "development"}):
        with pytest.raises(SystemExit):
            from importlib import reload
            import src.logger as mod
            reload(mod)
            mod.setup_logger()


def test_invalid_run_environment():
    with patch.dict(os.environ, {"NAME_APP": "test-app", "RUN_ENVIRONMENT": "invalid"}):
        with pytest.raises(SystemExit):
            from src.logger import setup_logger
            setup_logger()


def test_missing_path_to_logs_in_production():
    with patch.dict(os.environ, {"NAME_APP": "test-app", "RUN_ENVIRONMENT": "production"}):
        with pytest.raises(SystemExit):
            from src.logger import setup_logger
            setup_logger()


def test_missing_path_to_logs_in_testing():
    with patch.dict(os.environ, {"NAME_APP": "test-app", "RUN_ENVIRONMENT": "testing"}):
        with pytest.raises(SystemExit):
            from src.logger import setup_logger
            setup_logger()


def test_development_mode_succeeds(monkeypatch):
    monkeypatch.setenv("NAME_APP", "test-app")
    monkeypatch.setenv("RUN_ENVIRONMENT", "development")
    from src.logger import setup_logger
    setup_logger()


def test_testing_mode_succeeds(monkeypatch, tmp_path):
    monkeypatch.setenv("NAME_APP", "test-app")
    monkeypatch.setenv("RUN_ENVIRONMENT", "testing")
    monkeypatch.setenv("PATH_TO_LOGS", str(tmp_path))
    from src.logger import setup_logger
    setup_logger()


def test_production_mode_succeeds(monkeypatch, tmp_path):
    monkeypatch.setenv("NAME_APP", "test-app")
    monkeypatch.setenv("RUN_ENVIRONMENT", "production")
    monkeypatch.setenv("PATH_TO_LOGS", str(tmp_path))
    from src.logger import setup_logger
    setup_logger()


def test_excepthook_installed(monkeypatch):
    monkeypatch.setenv("NAME_APP", "test-app")
    monkeypatch.setenv("RUN_ENVIRONMENT", "development")
    from src.logger import setup_logger
    setup_logger()
    assert sys.excepthook is not sys.__excepthook__
