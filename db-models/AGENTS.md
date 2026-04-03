# AGENTS.md — db-models

## What this project is

Shared SQLAlchemy ORM package for the Knowledge Base Service monorepo. Both `api` and `worker-python` depend on this package for all database models, engine creation, and session management. It also owns the Alembic migration history.

This package has no runtime of its own — it is installed as an editable dependency into sibling projects via `pip install -e ../db-models`.

## Key architecture decisions

- **Single DeclarativeBase:** `base.py` defines one `Base` class. All models inherit from it. Alembic's `env.py` imports `Base.metadata` for autogenerate.
- **Engine and sessions:** `database.py` exposes `get_engine(database_url)` and `get_session_factory(engine)`. The `DATABASE_URL` env var is read once at module import time as a default. Callers can override by passing a URL explicitly.
- **pgvector:** The `get_engine` function registers a `connect` event listener stub for pgvector. The `CREATE EXTENSION vector` must already exist in the database (created by a superuser).
- **UUIDs as primary keys:** All three models use `uuid.uuid4` as the default primary key.
- **Cascade deletes:** `MarkdownFile.embeddings` has `cascade="all, delete-orphan"`, so deleting a file removes its embeddings.
- **Embedding dimensions:** 384 (matching `sentence-transformers/all-MiniLM-L6-v2`). The constant `EMBEDDING_DIMENSIONS` is defined in `models/markdown_file_embeddings.py`.
- **No test suite:** Model correctness is validated through integration tests in `api` and `worker-python`.

## Project layout

```
db-models/
├── alembic.ini                         # Alembic config (reads DATABASE_URL from env)
├── pyproject.toml
└── src/
    └── db_models/
        ├── __init__.py                 # Public exports: Base, get_engine, get_session_factory, all models
        ├── base.py                     # DeclarativeBase
        ├── database.py                 # Engine and session factory
        ├── models/
        │   ├── __init__.py             # Re-exports ApiKey, MarkdownFile, MarkdownFileEmbedding
        │   ├── api_keys.py             # ApiKey model
        │   ├── markdown_files.py       # MarkdownFile model (has embeddings relationship)
        │   └── markdown_file_embeddings.py  # MarkdownFileEmbedding model (Vector column)
        └── alembic/
            ├── env.py                  # Reads DATABASE_URL, imports all models for metadata
            └── versions/
                └── c45ad2d6dfd9_initial_tables.py  # Creates all 3 tables + pgvector extension
```

## Tables

| Table                        | Key columns                                      |
| ---------------------------- | ------------------------------------------------ |
| `api_keys`                   | `id` (UUID), `key_hash`, `name`                  |
| `markdown_files`             | `id` (UUID), `file_name`, `file_path` (unique)   |
| `markdown_file_embeddings`   | `id` (UUID), `markdown_file_id` (FK), `embedding` (Vector 384), `snippet` |

All tables include `created_at` and `updated_at` timestamp columns with server defaults.

## How consumers use this package

```python
from db_models import Base, get_engine, get_session_factory, ApiKey, MarkdownFile, MarkdownFileEmbedding

engine = get_engine()  # uses DATABASE_URL from env
SessionLocal = get_session_factory(engine)
session = SessionLocal()
```

## Running migrations

```bash
cd db-models
DATABASE_URL=postgresql://... alembic upgrade head
```

To generate a new migration after model changes:

```bash
DATABASE_URL=postgresql://... alembic revision --autogenerate -m "description"
```

## Gotchas

- `DATABASE_URL` is captured at import time as a module-level default. If you need to override it (e.g. in tests), pass the URL explicitly to `get_engine(database_url=...)`.
- Adding a new model requires importing it in `models/__init__.py` and re-exporting it in `db_models/__init__.py`, otherwise Alembic autogenerate won't detect it.
- The pgvector extension (`CREATE EXTENSION vector`) must be created by a database superuser before running migrations. The migration file includes this, but it will fail if the current user lacks superuser privileges.
