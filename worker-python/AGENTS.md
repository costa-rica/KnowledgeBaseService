# AGENTS.md — worker-python

## What this project is

A background worker for the Knowledge Base Service monorepo. It syncs an Obsidian vault from the cloud, scans for new or modified markdown files, generates semantic embeddings, and upserts them into PostgreSQL with pgvector.

This is one of three packages in the monorepo. It depends on `db-models` (sibling package) for all SQLAlchemy models and database setup.

## Key architecture decisions

- **Two-job pipeline:** Job 1 syncs the vault via `obsidianctl` CLI (one-way pull). Job 2 scans the vault and generates embeddings. Both run sequentially in a single invocation.
- **File diffing by mtime:** The scanner compares each file's filesystem `mtime` against `markdown_files.updated_at` in the database. Only new and modified files are processed.
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Lazy-loaded via `_get_model()` in `src/embedder.py`. First run will be slow while the model downloads.
- **No chunking (v1):** Each markdown file has one embedding for its full content. Snippets are the first 500 characters.
- **Single transaction:** The entire scan + embed pipeline runs in one database transaction. On any failure the transaction is rolled back.
- **Logging:** Loguru configured in `src/logger.py`, initialized before any work. Requires `NAME_APP`, `RUN_ENVIRONMENT`, and `PATH_TO_LOGS` (testing/production) env vars. Missing vars cause a fatal exit.
- **Scheduling:** Runs as a systemd oneshot service triggered by a daily timer. Not a long-running daemon.

## Project layout

```
worker-python/
├── main.py                     # top-level entrypoint (python main.py)
├── src/
│   ├── main.py                 # orchestrator: sync → scan → embed → commit
│   ├── logger.py               # Loguru setup per RUN_ENVIRONMENT
│   ├── sync.py                 # Job 1: obsidianctl vault pull
│   ├── scanner.py              # Job 2a: rglob + mtime diffing
│   └── embedder.py             # Job 2b: sentence-transformers + upsert
├── tests/
│   ├── unit/                   # all unit tests, mocked DB and model
│   └── integration/            # (placeholder for future integration tests)
├── systemd/
│   ├── knowledgebaseservice-worker-python.service
│   └── knowledgebaseservice-worker-python.timer
├── pyproject.toml
├── Makefile
└── .env.example
```

## How to run

```bash
# setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" -e ../db-models

# manual run
NAME_APP=KnowledgeBaseServiceWorkerPython RUN_ENVIRONMENT=development \
  VAULT_PATH=/path/to/vault DATABASE_URL=postgresql://... \
  python main.py

# tests
make test
```

## Testing approach

- All tests are in `tests/unit/` and use mocked database sessions, subprocess calls, and embedding models.
- Sync tests mock `subprocess.run` to avoid calling real `obsidianctl`.
- Scanner tests use `tmp_path` fixtures with real files but mocked SQLAlchemy sessions.
- Embedder tests mock `_get_model()` to avoid loading the real sentence-transformers model.
- Main tests mock all dependencies to test orchestration logic in isolation.
- Run with: `make test` (calls `python -m pytest --cov=src --cov-report=term-missing`).
- pytest markers configured: `unit`, `integration`, `contract`.

## Pipeline flow

```
main.py
  → setup_logger()
  → sync_vault()           # subprocess: obsidianctl sync --pull-only
  → scan_vault(session)    # returns {new, modified, unchanged, errors}
  → generate_embeddings()  # only for new + modified files
  → session.commit()
```

## Environment variables

| Variable          | Required    | Description                                      |
| ----------------- | ----------- | ------------------------------------------------ |
| `NAME_APP`        | Always      | App name for log files                           |
| `RUN_ENVIRONMENT` | Always      | `development`, `testing`, or `production`        |
| `PATH_TO_LOGS`    | test / prod | Directory for log output                         |
| `DATABASE_URL`    | Always      | PostgreSQL connection string                     |
| `VAULT_PATH`      | Always      | Absolute path to the Obsidian vault directory    |
| `LOG_MAX_SIZE_IN_MB` | No       | Log rotation size, default `3`                   |
| `LOG_MAX_FILES`   | No          | Log retention count, default `3`                 |

## Gotchas

- `db-models` must be installed as an editable dependency (`pip install -e ../db-models`) or imports will fail.
- `obsidianctl` must be on PATH for vault sync to work. If it's missing, the worker exits with a clear error.
- The embedding model is ~90 MB and downloads on first use. Ensure the production server has internet access for the initial run, or pre-cache the model.
- File paths in `markdown_files.file_path` are relative to the vault root, not absolute. The vault root is provided via `VAULT_PATH` at runtime.
- The scanner compares timezone-aware UTC datetimes. If existing `updated_at` values in the database are naive, they are treated as UTC.
