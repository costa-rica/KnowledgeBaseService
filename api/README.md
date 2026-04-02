# api

FastAPI service for the Knowledge Base Service. Exposes endpoints for querying semantic embeddings of an Obsidian vault.

## Setup

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" -e ../db-models
```

## Usage

```bash
# development
python main.py

# production (via systemd)
sudo cp systemd/knowledge-base-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now knowledge-base-api
```

## Project Structure

```
api/
├── main.py                  # uvicorn entrypoint
├── src/
│   ├── app.py               # FastAPI application
│   ├── auth.py              # Bearer token authentication
│   ├── logger.py            # Loguru configuration
│   └── routes/
│       └── obsidian.py      # /obsidian/matches and /obsidian/file endpoints
├── scripts/
│   └── generate_token.py    # CLI token generation
├── tests/
│   └── unit/
├── systemd/
│   └── knowledge-base-api.service
└── .env.example
```

## .env

| Variable          | Required | Description                                |
| ----------------- | -------- | ------------------------------------------ |
| `NAME_APP`        | Yes      | Application name for logging               |
| `RUN_ENVIRONMENT` | Yes      | `development`, `testing`, or `production`  |
| `PATH_TO_LOGS`    | Prod/Test| Directory for log files                    |
| `DATABASE_URL`    | Yes      | PostgreSQL connection string               |

## Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Token Generation

```bash
source .venv/bin/activate
DATABASE_URL=postgresql://... python -m scripts.generate_token --name "my-client"
```

The raw token is printed to stdout. Store it securely — it cannot be retrieved again.
