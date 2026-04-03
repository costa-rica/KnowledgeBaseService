# AGENTS.md — api

## What this project is

FastAPI service for the Knowledge Base Service monorepo. It exposes HTTP endpoints for querying semantic embeddings of an Obsidian vault stored in PostgreSQL with pgvector.

This is one of three packages in the monorepo. It depends on `db-models` (sibling package) for all SQLAlchemy models and database setup.

## Key architecture decisions

- **Authentication:** Bearer token hashed with SHA-256 and compared against the `api_keys` table. The `verify_token` dependency in `src/auth.py` is injected into all protected routes.
- **Database sessions:** Lazy-initialized session factory in `src/auth.py` (`_get_session_factory`). The `get_db` generator yields a session per request and closes it in the `finally` block.
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions). Lazy-loaded via `_get_model()` in `src/routes/obsidian.py`. First request will be slow while the model downloads/loads.
- **Similarity search:** Raw SQL with pgvector's `<=>` cosine distance operator, not the ORM. Returns top 5 results.
- **Logging:** Loguru configured in `src/logger.py`, initialized during the FastAPI lifespan event. Requires `NAME_APP`, `RUN_ENVIRONMENT`, and `PATH_TO_LOGS` (testing/production) env vars. Missing vars cause a fatal exit.
- **No chunking (v1):** Each markdown file has one embedding for its full content.

## Project layout

```
api/
├── main.py                     # uvicorn entrypoint (python main.py)
├── src/
│   ├── app.py                  # FastAPI app instance, lifespan, router registration
│   ├── auth.py                 # Bearer token auth, get_db dependency
│   ├── logger.py               # Loguru setup per RUN_ENVIRONMENT
│   └── routes/
│       └── obsidian.py         # POST /obsidian/matches, GET /obsidian/file/{file_id}
├── scripts/
│   └── generate_token.py       # CLI: generate and insert a new API key
├── tests/
│   └── unit/                   # All unit tests, mocked DB and model
├── systemd/
│   └── knowledge-base-api.service
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

# dev server
NAME_APP=knowledge-base-api RUN_ENVIRONMENT=development DATABASE_URL=postgresql://... python main.py

# tests
make test
```

## Testing approach

- All tests are in `tests/unit/` and use mocked database sessions and embedding models.
- Auth tests patch `_get_session_factory` to return a mock session.
- Route tests patch both the session factory and `_get_model` to avoid real DB and model loading.
- Run with: `make test` (calls `python -m pytest --cov=src --cov-report=term-missing`).

## Routes

| Method | Path                        | Auth     | Description                           |
| ------ | --------------------------- | -------- | ------------------------------------- |
| GET    | `/`                         | None     | HTML health check page                |
| POST   | `/obsidian/matches`         | Bearer   | Semantic similarity search            |
| GET    | `/obsidian/file/{file_id}`  | Bearer   | Retrieve full markdown file content   |

## Environment variables

| Variable          | Required    | Description                               |
| ----------------- | ----------- | ----------------------------------------- |
| `NAME_APP`        | Always      | App name for log files                    |
| `RUN_ENVIRONMENT` | Always      | `development`, `testing`, or `production` |
| `PATH_TO_LOGS`    | test / prod | Directory for log output                  |
| `DATABASE_URL`    | Always      | PostgreSQL connection string              |

## Gotchas

- `db-models` must be installed as an editable dependency (`pip install -e ../db-models`) or imports will fail.
- The session factory is a module-level singleton. Tests must patch `src.auth._get_session_factory`, not the db_models imports directly.
- `DATABASE_URL` is read by `db_models.database` from `os.environ` at import time. It must be set before the app starts.
