"""Centralized Loguru configuration per LOGGING_PYTHON_V06.md."""

import os
import sys

from loguru import logger

VALID_ENVIRONMENTS = {"development", "testing", "production"}

# Format strings
_CONSOLE_FORMAT = (
    "<level>{time:HH:mm:ss.SSS}</level> | "
    "<level>{level: <8}</level> | "
    "{module}:{function}:{line} | "
    "{message}"
)
_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{module}:{function}:{line} | "
    "{message}"
)


def _fatal(message: str) -> None:
    """Write a fatal error to stderr and exit immediately."""
    logger.critical(message)
    sys.exit(1)


def _validate_env_vars() -> tuple[str, str, str | None]:
    """Validate and return required environment variables.

    Returns:
        Tuple of (name_app, run_environment, path_to_logs).
        path_to_logs may be None in development.
    """
    name_app = os.environ.get("NAME_APP", "").strip()
    if not name_app:
        _fatal("NAME_APP environment variable is missing or empty")

    run_environment = os.environ.get("RUN_ENVIRONMENT", "").strip()
    if run_environment not in VALID_ENVIRONMENTS:
        _fatal(
            f"RUN_ENVIRONMENT environment variable is missing or invalid: "
            f"'{run_environment}'. Must be one of: {VALID_ENVIRONMENTS}"
        )

    path_to_logs = os.environ.get("PATH_TO_LOGS", "").strip() or None
    if run_environment in ("testing", "production") and not path_to_logs:
        _fatal(
            "PATH_TO_LOGS environment variable is required "
            f"in {run_environment} environment"
        )

    return name_app, run_environment, path_to_logs


def _uncaught_exception_handler(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions at CRITICAL before the process dies."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
        "Uncaught exception"
    )


def setup_logger() -> None:
    """Configure Loguru sinks based on RUN_ENVIRONMENT.

    Must be called once at application startup before any logging.
    """
    name_app, run_environment, path_to_logs = _validate_env_vars()

    max_size = os.environ.get("LOG_MAX_SIZE_IN_MB", "3")
    max_files = int(os.environ.get("LOG_MAX_FILES", "3"))

    # Remove default stderr sink so we control all output.
    logger.remove()

    # Install uncaught exception handler.
    sys.excepthook = _uncaught_exception_handler

    if run_environment == "development":
        logger.add(
            sys.stderr,
            format=_CONSOLE_FORMAT,
            level="DEBUG",
            backtrace=True,
            diagnose=True,
        )

    elif run_environment == "testing":
        # Terminal sink.
        logger.add(
            sys.stderr,
            format=_CONSOLE_FORMAT,
            level="INFO",
            backtrace=True,
            diagnose=True,
        )
        # File sink.
        logger.add(
            os.path.join(path_to_logs, f"{name_app}.log"),
            format=_FILE_FORMAT,
            level="INFO",
            rotation=f"{max_size} MB",
            retention=max_files,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

    elif run_environment == "production":
        # File sink only — no terminal output.
        logger.add(
            os.path.join(path_to_logs, f"{name_app}.log"),
            format=_FILE_FORMAT,
            level="INFO",
            rotation=f"{max_size} MB",
            retention=max_files,
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

    logger.info(
        "Logger initialized: app={}, env={}", name_app, run_environment
    )
