# AGENTS.md

## What this project is

A self-hosted knowledge retrieval system that syncs an Obsidian vault, generates semantic embeddings, and exposes a queryable API. Designed for use with Claude and other clients that need semantic search over personal notes.

## Monorepo structure

This is a Python monorepo with three packages:

| Package | Purpose | Has tests |
| ------- | ------- | --------- |
| `db-models` | Shared SQLAlchemy ORM models and Alembic migrations | No (v1) — validated via consumer tests |
| `worker-python` | Systemd-managed background worker: vault sync + embedding generation | Yes |
| `api` | FastAPI HTTP service: semantic search + file retrieval | Yes |

`db-models` is installed as an editable dependency into both `worker-python` and `api` via `pip install -e ../db-models`.

Each project has its own `AGENTS.md` with detailed architecture, layout, and gotchas. Read the relevant one before working in a package.

## Key technical decisions

- **Database:** PostgreSQL with pgvector for vector similarity search
- **ORM:** SQLAlchemy 2.0 with declarative mapped classes
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Logging:** Loguru, configured per `RUN_ENVIRONMENT` (see `docs/requirements/LOGGING_PYTHON_V06.md`)
- **Python:** 3.12 or higher
- **Testing:** pytest with coverage for `worker-python` and `api`

## Production environment

The production deployment target is an **Ubuntu 20.04 or 24.04 LTS** server (FSDC avatar08).

### User model

- **nick** — admin user. Configures the server, manages systemd units, installs packages, clones repos.
- **limited_user** — no login shell, no sudo. Runs all production applications via systemd. Owns all runtime paths under `/home/limited_user/`.

This separation limits the blast radius of any compromised application process.

### Runtime paths

| Path | Purpose |
| ---- | ------- |
| `/home/limited_user/applications/knowledge-base-service/` | Cloned monorepo |
| `/home/limited_user/environments/knowledge-base-service/` | Python venv |
| `/home/limited_user/logs/` | Log output directory |
| `/home/limited_user/project_resources/obsidian-vault/` | Obsidian vault (read-only replica) |

### Services

- `worker-python` runs as a systemd oneshot service triggered by a daily timer
- `api` runs as a systemd service behind an nginx reverse proxy
- Environment variables are loaded from `.env` files inside each project directory

## Requirements and TODOs

All requirements and task tracking live in `docs/requirements/`:

- `FIRST_REQUIREMENTS.md` — full project spec
- `LOGGING_PYTHON_V06.md` — logging standard
- `TODO_DB_MODELS_*.md`, `TODO_WORKER_PYTHON_*.md`, `TODO_API_*.md` — phased checklists

---

## Commit Message Guidance

### Guidelines

- Only generate the message for staged files/changes
- Title is lowercase, no period at the end.
- Title should be a clear summary, max 50 characters.
- Use the body to explain _why_ and the main areas changed, not just _what_.
- Bullet points should be concise and high-level.
- Try to use the ideal format. But if the commit is too broad or has too many different types, then use the borad format.
- When committing changes from TODO or task list that is already part of the repo and has phases, make refernce to the file and phase instead of writing a long commit message.
- Add a commit body whenever the staged change is not trivially small.
- A body is expected when the commit:
  - touches more than 3 files
  - touches more than one package or app
  - includes both implementation and tests
  - adds a new route, component, workflow, or integration point
- For broader commits, the title can stay concise, but the body should summarize the main change areas so a reader can understand scope without opening the diff.
- Do not use the body as a file inventory. Summarize the logical changes in 2-5 bullets.
- Never end a commit with `Co-Authored-By:` or `<noreply@anthropic.com>`.
  - it is ok to include a shorter message like "commit by Claude Sonnet 4.5"

### Format

#### Ideal Format

```
<type>:<space><message title>

<bullet points summarizing what was updated>
```

#### Broad Format

```
<message title>

<bullet points summarizing what was updated>
```

#### Types for Ideal Format

| Type     | Description                           |
| -------- | ------------------------------------- |
| feat     | New feature                           |
| fix      | Bug fix                               |
| chore    | Maintenance (e.g., tooling, deps)     |
| docs     | Documentation changes                 |
| refactor | Code restructure (no behavior change) |
| test     | Adding or refactoring tests           |
| style    | Code formatting (no logic change)     |
| perf     | Performance improvements              |
