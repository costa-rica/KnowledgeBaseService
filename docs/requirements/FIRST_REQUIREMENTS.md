# Knowledge Base Service — Requirements Document

## Overview

**Project name:** knowledge-base-service  
**Type:** Python monorepo  
**Purpose:** A self-hosted knowledge retrieval system that syncs an Obsidian vault, generates semantic embeddings, and exposes a queryable API for use with Claude and other clients.  
**Primary server:** FSDC — avatar08 service server

---

## Monorepo structure

```
knowledge-base-service/
├── api/                  # FastAPI web service
│   ├── src/              # Application source code
│   └── tests/            # pytest test suite
├── worker-python/        # Systemd-managed sync and embedding worker
│   ├── src/              # Application source code
│   └── tests/            # pytest test suite
└── db-models/            # Shared SQLAlchemy package (local pip install)
    └── src/              # Package source code
```

All three are Python projects. Each project keeps its application code in a `src/` directory. `db-models` is installed as a local editable package into both `api` and `worker-python`.

---

## db-models

### Purpose

A shared Python package containing all SQLAlchemy ORM models and database migration configuration. Both `api` and `worker-python` import from this package.

### Installation

Referenced in dependent projects via:

```
pip install -e ../db-models
```

### Database

- **Engine:** PostgreSQL
- **Extension:** pgvector (for vector similarity search)
- **ORM:** SQLAlchemy

### Tables

#### `api_keys`

| Column     | Type       | Notes                  |
| ---------- | ---------- | ---------------------- |
| id         | UUID / int | Primary key            |
| key_hash   | VARCHAR    | Hashed API key         |
| name       | VARCHAR    | Human-readable label   |
| created_at | TIMESTAMP  | Auto-set on insert     |
| updated_at | TIMESTAMP  | Auto-updated on change |

#### `markdown_files`

| Column     | Type       | Notes                        |
| ---------- | ---------- | ---------------------------- |
| id         | UUID / int | Primary key                  |
| file_name  | VARCHAR    | Filename only (e.g. note.md) |
| file_path  | TEXT       | Full relative path in vault  |
| created_at | TIMESTAMP  | Auto-set on insert           |
| updated_at | TIMESTAMP  | Reflects file mtime on disk  |

#### `markdown_file_embeddings`

| Column           | Type       | Notes                              |
| ---------------- | ---------- | ---------------------------------- |
| id               | UUID / int | Primary key                        |
| markdown_file_id | FK         | References markdown_files.id       |
| embedding        | VECTOR     | pgvector column (e.g. 384 dims)    |
| snippet          | TEXT       | First N characters of file content |
| created_at       | TIMESTAMP  | Auto-set on insert                 |
| updated_at       | TIMESTAMP  | Auto-updated on change             |

---

## worker-python

### Purpose

A Python background worker that:

1. Triggers a one-way Obsidian headless sync (cloud → local, read-only replica)
2. Recursively scans the vault directory for new or modified markdown files
3. Generates and upserts embeddings for changed files into PostgreSQL

### Scheduling

- Runs via a **systemd .service** file on the avatar08 server
- Triggered on a schedule via a **systemd .timer** file (once daily)

### Job 1: Obsidian vault sync

- Run the Obsidian headless CLI (`obsidianctl` / `ob` commands) to pull the latest state from the Obsidian cloud account
- Sync is **one-way pull only** — the local vault never pushes changes back to the cloud
- The local vault is treated as a read-only replica

### Job 2: File diffing and embedding

After sync completes, the worker:

1. **Recursively walks** the vault root directory using `pathlib.Path.rglob("*.md")`
2. For each markdown file found:
   - Reads the file system `mtime` (modified timestamp)
   - Compares against the `updated_at` stored in `markdown_files` table
   - **New file:** inserts a row into `markdown_files`, generates embedding, inserts into `markdown_file_embeddings`
   - **Modified file:** updates `markdown_files.updated_at`, regenerates embedding, upserts into `markdown_file_embeddings`
   - **Unchanged file:** skipped entirely
3. Reads full file content for embedding generation (no chunking in v1)

### Embedding model

- **Library:** `sentence-transformers`
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- Embedding dimension: 384
- Stored in PostgreSQL via pgvector

### Key dependencies

```
sentence-transformers
sqlalchemy
psycopg2-binary  # or asyncpg
pgvector
loguru
pytest
pytest-cov
```

### Systemd service file (example)

```ini
[Unit]
Description=Knowledge Base Service Worker
After=network.target postgresql.service

[Service]
Type=oneshot
User=limited_user
WorkingDirectory=/home/limited_user/applications/knowledge-base-service/worker-python
ExecStart=/home/limited_user/environments/knowledge-base-service/bin/python main.py
EnvironmentFile=/home/limited_user/applications/knowledge-base-service/worker-python/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Systemd timer file (example)

```ini
[Unit]
Description=Daily trigger for Knowledge Base Service Worker

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

---

## api

### Purpose

A FastAPI service that exposes HTTP endpoints for querying the knowledge base. Authentication is enforced via Bearer token on all Obsidian endpoints.

### Authentication

- **Method:** `Authorization: Bearer ` header
- Token is validated by hashing and comparing against the `api_keys` table
- Token is generated via a one-time CLI script (not via API endpoint)

### Token generation script

A standalone Python script (`scripts/generate_token.py`) that:

1. Generates a secure random token
2. Hashes it
3. Inserts a row into `api_keys`
4. Prints the raw token to stdout for copying

### Endpoints

#### `GET /`

- **Auth:** None required
- **Response:** HTML page displaying the app name "Knowledge Base Service"
- **Purpose:** Health check / index page

#### `POST /obsidian/matches`

- **Auth:** Bearer token required
- **Request body (JSON):**
  ```json
  { "question": "What did I write about focus and deep work?" }
  ```
- **Behaviour:**
  1. Validates Bearer token against `api_keys`
  2. Converts `question` to an embedding using the same model as the worker
  3. Runs a pgvector cosine similarity search against `markdown_file_embeddings`
  4. Returns top 5 matches
- **Response body (JSON):**
  ```json
  {
    "matches": [
      {
        "id": 1,
        "file_name": "deep-work.md",
        "file_path": "productivity/deep-work.md",
        "score": 0.94,
        "snippet": "First 500 characters of the file..."
      }
    ]
  }
  ```

#### `GET /obsidian/file/{file_id}`

- **Auth:** Bearer token required
- **Params:** `file_id` — integer or UUID matching `markdown_files.id`
- **Behaviour:**
  1. Validates Bearer token
  2. Looks up the file record in `markdown_files`
  3. Reads the markdown file from disk using `file_path`
  4. Returns full file content
- **Response body (JSON):**
  ```json
  {
    "id": 1,
    "file_name": "deep-work.md",
    "file_path": "productivity/deep-work.md",
    "content": "Full markdown content here..."
  }
  ```

### Key dependencies

```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pgvector
sentence-transformers
python-jose  # or passlib for token hashing
loguru
pytest
pytest-cov
httpx  # for FastAPI TestClient
```

---

## Testing

All projects use **pytest** as the test framework.

### Scope

- **`worker-python`** — pytest with `unit`, `integration`, and `contract` markers. Run via `make test` which executes `python -m pytest --cov=src --cov-report=term-missing`.
- **`api`** — pytest with FastAPI's `TestClient` (via `httpx`) for endpoint, auth, and workflow testing.
- **`db-models`** — no dedicated test suite in v1. Model correctness is validated through the integration tests in `api` and `worker-python`.

### Key dependencies

```
pytest
pytest-cov
httpx          # api only — for FastAPI TestClient
```

---

## Logging

All Python services use **Loguru** for logging, configured per `LOGGING_PYTHON_V06.md`.

### Environment variable: `RUN_ENVIRONMENT`

Controls logging mode. Valid values: `development`, `testing`, `production`.

### Required environment variables (fatal if missing)

| Variable          | Required In         | Fatal Behavior                    |
| ----------------- | ------------------- | --------------------------------- |
| `NAME_APP`        | All environments    | Fatal error if missing or empty   |
| `RUN_ENVIRONMENT` | All environments    | Fatal error if missing or invalid |
| `PATH_TO_LOGS`    | testing, production | Fatal error if missing            |

### Logging modes

| Feature                  | Development | Testing | Production |
| ------------------------ | ----------- | ------- | ---------- |
| Terminal Output          | Yes         | Yes     | No         |
| File Output              | No          | Yes     | Yes        |
| Log Level                | DEBUG       | INFO    | INFO       |
| Rotation                 | No          | Yes     | Yes        |
| Process Safe (`enqueue`) | No          | Yes     | Yes        |

### Key dependencies

```
loguru
```

---

## Infrastructure notes

### Target OS

- **OS:** Ubuntu 20.04 or 24.04 LTS Server
- **Python:** 3.12 or higher — 3.13 for local dev (Homebrew), 3.12+ on the server
- **Server:** FSDC avatar08

### User model

The server uses a two-user separation: **nick** (admin) configures the server and manages systemd service files; **limited_user** (no login shell, no sudo) runs all production applications. This limits the blast radius of any compromised application process.

- **nick** — clones repos, installs system packages, writes systemd units to `/etc/systemd/system/`, manages nginx and firewall
- **limited_user** — owns all runtime paths under `/home/limited_user/`:
  - `applications/` — cloned app repositories
  - `environments/` — Python virtual environments (one per app)
  - `logs/` — application log files (`PATH_TO_LOGS` points here)
  - `databases/` — file-based databases (if any)
  - `project_resources/` — shared data or assets
  - `_config_files/` — app-specific config and `.env` files

### Runtime paths for this project

| Path | Purpose |
| ---- | ------- |
| `/home/limited_user/applications/knowledge-base-service/` | Cloned monorepo |
| `/home/limited_user/environments/knowledge-base-service/` | Python venv |
| `/home/limited_user/logs/` | Log output directory |
| `/home/limited_user/project_resources/obsidian-vault/` | Obsidian vault (read-only replica) |

### Services

- **Process management:** systemd (worker) + systemd socket / reverse proxy (api)
- **Database:** PostgreSQL running locally or on the same VLAN
- **Reverse proxy:** nginx
- Environment variables are loaded from a `.env` file inside the application directory

---

## Out of scope (v1)

- Multi-user support (no users table)
- Chunked embeddings (whole-file only)
- Token management API endpoint (CLI script only)
- Support for non-markdown file types
- Push sync from server back to Obsidian cloud

---

## Open questions / future expansion

- Additional knowledge sources beyond Obsidian (the monorepo structure supports adding new worker modules)
- Chunking strategy for large files to improve retrieval precision
- Rate limiting on API endpoints
- Caching frequently queried embeddings
