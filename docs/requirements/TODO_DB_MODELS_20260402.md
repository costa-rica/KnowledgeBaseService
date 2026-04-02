# db-models — TODO

## Phase 1: Project scaffolding

- [x] Create `db-models/` directory with `src/` subdirectory
- [x] Create `pyproject.toml` (or `setup.py`) for editable install
- [x] Create `src/db_models/__init__.py`
- [x] Verify editable install works: `pip install -e .`

## Phase 2: SQLAlchemy base and database connection

- [x] Add `sqlalchemy` and `psycopg2-binary` to dependencies
- [x] Create `src/db_models/database.py` with engine and session configuration
- [x] Create `src/db_models/base.py` with SQLAlchemy declarative base
- [x] Add pgvector extension registration

## Phase 3: Models

- [x] Create `src/models/api_keys.py` — `api_keys` table
- [x] Create `src/models/markdown_files.py` — `markdown_files` table
- [x] Create `src/models/markdown_file_embeddings.py` — `markdown_file_embeddings` table with pgvector VECTOR column (384 dims)
- [x] Create `src/models/__init__.py` re-exporting all models
- [x] Verify all FK relationships and timestamp defaults

## Phase 4: Alembic migration setup

- [x] Add `alembic` to dependencies
- [x] Run `alembic init` and configure `alembic.ini` and `env.py`
- [x] Generate initial migration from models
- [ ] Verify migration applies cleanly against a local PostgreSQL + pgvector instance (deferred — no PostgreSQL on dev machine)

> **Checkpoint:** After each phase, verify the package imports correctly and the editable install still works. Commit referencing this file and the completed phase.
