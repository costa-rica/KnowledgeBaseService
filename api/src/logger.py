import os
import sys

from loguru import logger

VALID_ENVIRONMENTS = {"development", "testing", "production"}

CONSOLE_FORMAT = (
    "<level>{time:HH:mm:ss.SSS}</level> | "
    "<level>{level: <8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{module}:{function}:{line} | "
    "{message}"
)


def _fatal(message: str) -> None:
    logger.critical(message)
    sys.exit(1)


def setup_logger() -> None:
    logger.remove()

    name_app = os.environ.get("NAME_APP", "").strip()
    run_environment = os.environ.get("RUN_ENVIRONMENT", "").strip()

    if not name_app:
        _fatal("Missing required environment variable: NAME_APP")

    if run_environment not in VALID_ENVIRONMENTS:
        _fatal(
            f"Invalid or missing RUN_ENVIRONMENT: '{run_environment}'. "
            f"Must be one of: {', '.join(sorted(VALID_ENVIRONMENTS))}"
        )

    path_to_logs = os.environ.get("PATH_TO_LOGS", "").strip()
    if run_environment in {"testing", "production"} and not path_to_logs:
        _fatal("Missing required environment variable: PATH_TO_LOGS")

    log_max_size = os.environ.get("LOG_MAX_SIZE_IN_MB", "3")
    log_max_files = int(os.environ.get("LOG_MAX_FILES", "3"))

    if run_environment == "development":
        logger.add(
            sys.stderr,
            format=CONSOLE_FORMAT,
            level="DEBUG",
            backtrace=True,
            diagnose=True,
        )

    elif run_environment == "testing":
        logger.add(
            sys.stderr,
            format=CONSOLE_FORMAT,
            level="INFO",
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )
        logger.add(
            os.path.join(path_to_logs, f"{name_app}.log"),
            format=FILE_FORMAT,
            level="INFO",
            rotation=f"{log_max_size} MB",
            retention=log_max_files,
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )

    elif run_environment == "production":
        logger.add(
            os.path.join(path_to_logs, f"{name_app}.log"),
            format=FILE_FORMAT,
            level="INFO",
            rotation=f"{log_max_size} MB",
            retention=log_max_files,
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )

    def _excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
            "Uncaught exception"
        )

    sys.excepthook = _excepthook

    logger.info(f"{name_app} logger initialized ({run_environment})")
