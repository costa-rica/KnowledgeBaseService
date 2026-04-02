# worker-python — TODO

> **Prerequisite:** `db-models` must be completed through at least Phase 3 before starting Phase 2 here.

## Phase 1: Project scaffolding

- [ ] Create `worker-python/` directory with `src/` and `tests/` subdirectories
- [ ] Create `pyproject.toml` with dependencies: `sentence-transformers`, `sqlalchemy`, `psycopg2-binary`, `pgvector`, `loguru`
- [ ] Create `requirements.txt` or lock file
- [ ] Add dev dependencies: `pytest`, `pytest-cov`
- [ ] Add `db-models` as editable dependency (`pip install -e ../db-models`)
- [ ] Create `Makefile` with `test` target: `python -m pytest --cov=src --cov-report=term-missing`

> **Checkpoint:** Run `make test` (should pass with no tests collected). Commit referencing this file and Phase 1.

## Phase 2: Logging setup

- [ ] Create `src/logger.py` — centralized Loguru configuration per `LOGGING_PYTHON_V06.md`
- [ ] Validate required env vars at startup (`NAME_APP`, `RUN_ENVIRONMENT`, `PATH_TO_LOGS`)
- [ ] Fatal exit with explicit error if required vars are missing
- [ ] Configure sinks per `RUN_ENVIRONMENT` (development / testing / production)
- [ ] Enable rotation, retention, and `enqueue=True` for testing and production
- [ ] Install `sys.excepthook` for uncaught exception logging
- [ ] Create `.env.example` with all required environment variables

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 2.

## Phase 3: Vault sync (Job 1)

- [ ] Create `src/sync.py` — function to invoke Obsidian headless CLI for one-way pull
- [ ] Read vault path from environment or config
- [ ] Log sync start, completion, and any errors
- [ ] Handle sync failure gracefully (log and exit with non-zero code)

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 3.

## Phase 4: File diffing (Job 2 — scan and compare)

- [ ] Create `src/scanner.py` — recursively walk vault with `pathlib.Path.rglob("*.md")`
- [ ] For each file, read filesystem `mtime`
- [ ] Compare `mtime` against `markdown_files.updated_at` in the database
- [ ] Classify each file as new, modified, or unchanged
- [ ] Insert new files into `markdown_files`; update modified files; skip unchanged
- [ ] Log counts: new, modified, unchanged, errors

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 4.

## Phase 5: Embedding generation (Job 2 — embed and upsert)

- [ ] Create `src/embedder.py` — load `sentence-transformers/all-MiniLM-L6-v2` model
- [ ] Generate embedding from full file content (no chunking in v1)
- [ ] Extract snippet (first N characters) for storage
- [ ] Insert into `markdown_file_embeddings` for new files
- [ ] Upsert into `markdown_file_embeddings` for modified files
- [ ] Log embedding generation counts and any failures

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 5.

## Phase 6: Main entrypoint and orchestration

- [ ] Create `src/main.py` — orchestrates Job 1 (sync) then Job 2 (scan + embed)
- [ ] Initialize logger before any work
- [ ] Handle early exit logging (flush logs before exit)
- [ ] Exit with non-zero code on any failure
- [ ] Create top-level `main.py` that imports and runs `src/main.py`

> **Checkpoint:** Run tests. If tests pass, check off completed tasks and commit referencing this file and Phase 6.

## Phase 7: Systemd service and timer files

- [ ] Create `systemd/knowledge-base-worker.service` (reference file, not installed)
- [ ] Create `systemd/knowledge-base-worker.timer` (reference file, not installed)
- [ ] Verify paths match `limited_user` directory layout
- [ ] Document install steps in a README or inline comments

> **Checkpoint:** Commit referencing this file and Phase 7.
