# worker-python — TODO

> **Prerequisite:** `db-models` must be completed through at least Phase 3 before starting Phase 2 here.

## Phase 1: Project scaffolding

- [x] Create `worker-python/` directory with `src/` and `tests/` subdirectories
- [x] Create `pyproject.toml` with dependencies: `sentence-transformers`, `sqlalchemy`, `psycopg2-binary`, `pgvector`, `loguru`
- [x] Add dev dependencies: `pytest`, `pytest-cov` (via optional-dependencies)
- [x] Add `db-models` as editable dependency (`pip install -e ../db-models`)
- [x] Create `Makefile` with `test` target: `python -m pytest --cov=src --cov-report=term-missing`

> **Checkpoint:** Run `make test` (should pass with no tests collected). Commit referencing this file and Phase 1.

## Phase 2: Logging setup

- [x] Create `src/logger.py` — centralized Loguru configuration per `LOGGING_PYTHON_V06.md`
- [x] Validate required env vars at startup (`NAME_APP`, `RUN_ENVIRONMENT`, `PATH_TO_LOGS`)
- [x] Fatal exit with explicit error if required vars are missing
- [x] Configure sinks per `RUN_ENVIRONMENT` (development / testing / production)
- [x] Enable rotation, retention, and `enqueue=True` for testing and production
- [x] Install `sys.excepthook` for uncaught exception logging
- [x] Create `.env.example` with all required environment variables

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 2.

## Phase 3: Vault sync (Job 1)

- [x] Create `src/sync.py` — function to invoke Obsidian headless CLI for one-way pull
- [x] Read vault path from environment or config
- [x] Log sync start, completion, and any errors
- [x] Handle sync failure gracefully (log and exit with non-zero code)

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 3.

## Phase 4: File diffing (Job 2 — scan and compare)

- [x] Create `src/scanner.py` — recursively walk vault with `pathlib.Path.rglob("*.md")`
- [x] For each file, read filesystem `mtime`
- [x] Compare `mtime` against `markdown_files.updated_at` in the database
- [x] Classify each file as new, modified, or unchanged
- [x] Insert new files into `markdown_files`; update modified files; skip unchanged
- [x] Log counts: new, modified, unchanged, errors

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 4.

## Phase 5: Embedding generation (Job 2 — embed and upsert)

- [x] Create `src/embedder.py` — load `sentence-transformers/all-MiniLM-L6-v2` model
- [x] Generate embedding from full file content (no chunking in v1)
- [x] Extract snippet (first N characters) for storage
- [x] Insert into `markdown_file_embeddings` for new files
- [x] Upsert into `markdown_file_embeddings` for modified files
- [x] Log embedding generation counts and any failures

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 5.

## Phase 6: Main entrypoint and orchestration

- [x] Create `src/main.py` — orchestrates Job 1 (sync) then Job 2 (scan + embed)
- [x] Initialize logger before any work
- [x] Handle early exit logging (flush logs before exit)
- [x] Exit with non-zero code on any failure
- [x] Create top-level `main.py` that imports and runs `src/main.py`

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 6.

## Phase 7: Systemd service and timer files

- [x] Create `systemd/knowledge-base-worker.service` (reference file, not installed)
- [x] Create `systemd/knowledge-base-worker.timer` (reference file, not installed)
- [x] Verify paths match `limited_user` directory layout
- [x] Document install steps in inline comments

> **Checkpoint:** Commit referencing this file and Phase 7.
