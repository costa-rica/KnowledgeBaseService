# db-models — TODO

## Phase 1: Project scaffolding

- [ ] Create `db-models/` directory with `src/` subdirectory
- [ ] Create `pyproject.toml` (or `setup.py`) for editable install
- [ ] Create `src/__init__.py`
- [ ] Verify editable install works: `pip install -e .`

## Phase 2: SQLAlchemy base and database connection

- [ ] Add `sqlalchemy` and `psycopg2-binary` to dependencies
- [ ] Create `src/database.py` with engine and session configuration
- [ ] Create `src/base.py` with SQLAlchemy declarative base
- [ ] Add pgvector extension registration

## Phase 3: Models

- [ ] Create `src/models/api_keys.py` — `api_keys` table
- [ ] Create `src/models/markdown_files.py` — `markdown_files` table
- [ ] Create `src/models/markdown_file_embeddings.py` — `markdown_file_embeddings` table with pgvector VECTOR column (384 dims)
- [ ] Create `src/models/__init__.py` re-exporting all models
- [ ] Verify all FK relationships and timestamp defaults

## Phase 4: Alembic migration setup

- [ ] Add `alembic` to dependencies
- [ ] Run `alembic init` and configure `alembic.ini` and `env.py`
- [ ] Generate initial migration from models
- [ ] Verify migration applies cleanly against a local PostgreSQL + pgvector instance

> **Checkpoint:** After each phase, verify the package imports correctly and the editable install still works. Commit referencing this file and the completed phase.
