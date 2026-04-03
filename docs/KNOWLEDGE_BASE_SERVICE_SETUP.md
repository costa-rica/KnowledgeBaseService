# Knowledge Base Service Setup

Setup guide for deploying the Knowledge Base Service monorepo on avatar08 (Ubuntu 24.04 LTS, FSDC network). Covers PostgreSQL, db-models, worker-python, and api.

## PostgreSQL + pgvector

### 1. Install PostgreSQL and pgvector

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib postgresql-16-pgvector
```

### 2. Verify it's running

```bash
sudo systemctl status postgresql
```

### 3. Create a PostgreSQL role for limited_user

```bash
sudo -u postgres psql -c "CREATE USER limited_user;"
sudo -u postgres psql -c "CREATE DATABASE knowledge_base OWNER limited_user;"
sudo -u postgres psql -d knowledge_base -c "CREATE EXTENSION vector;"
```

This uses peer authentication — the OS user `limited_user` maps to the PostgreSQL role `limited_user` with no password needed.

### 4. Verify the connection

```bash
sudo -u limited_user psql -d knowledge_base -c "SELECT 1;"
```

### 5. Resulting DATABASE_URL

Use this in `.env` files for worker-python and api:

```
DATABASE_URL=postgresql:///knowledge_base
```

The triple-slash (`///`) means connect via local Unix socket with peer auth. No host, port, or password needed.

## db-models

### 1. Create the Python venv

```bash
sudo -u limited_user python3.12 -m venv /home/limited_user/environments/knowledge-base-service
```

### 2. Install db-models into the venv

```bash
sudo -u limited_user /home/limited_user/environments/knowledge-base-service/bin/pip install -e /home/limited_user/applications/KnowledgeBaseService/db-models
```

### 3. Run the Alembic migration

```bash
sudo -u limited_user DATABASE_URL=postgresql:///knowledge_base /home/limited_user/environments/knowledge-base-service/bin/alembic -c /home/limited_user/applications/KnowledgeBaseService/db-models/alembic.ini upgrade head
```

### 4. Verify tables were created

```bash
sudo -u limited_user psql -d knowledge_base -c "\dt"
```

Expected tables: `api_keys`, `markdown_files`, `markdown_file_embeddings`, and `alembic_version`.

## worker-python

### 1. Install worker-python into the venv

```bash
sudo -u limited_user /home/limited_user/environments/knowledge-base-service/bin/pip install -e /home/limited_user/applications/KnowledgeBaseService/worker-python
```

### 2. Ensure obsidian-headless is installed

The worker calls `ob sync` to pull the vault. Verify it's available:

```bash
ob --version
```

If not installed:

```bash
npm install -g obsidian-headless
```

Ensure mirror-remote mode is configured for the vault (one-time setup):

```bash
ob sync-config --path /home/limited_user/project_resources/PersonalWeb03/obsidian --mode mirror-remote
```

### 3. Create the .env file

```bash
nano /home/limited_user/applications/KnowledgeBaseService/worker-python/.env
```

Contents:

```
NAME_APP=KnowledgeBaseServiceWorkerPython
RUN_ENVIRONMENT=production
PATH_TO_LOGS=/home/limited_user/logs
DATABASE_URL=postgresql:///knowledge_base
VAULT_PATH=/home/limited_user/project_resources/PersonalWeb03/obsidian
```

### 4. Test a manual run

```bash
sudo -u limited_user /home/limited_user/environments/knowledge-base-service/bin/python /home/limited_user/applications/KnowledgeBaseService/worker-python/main.py
```

### 5. Install the systemd service and timer

```bash
sudo cp /home/limited_user/applications/KnowledgeBaseService/worker-python/systemd/knowledgebaseservice-worker-python.service /etc/systemd/system/
sudo cp /home/limited_user/applications/KnowledgeBaseService/worker-python/systemd/knowledgebaseservice-worker-python.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now knowledgebaseservice-worker-python.timer
```

### 6. Verify the timer is scheduled

```bash
systemctl list-timers | grep knowledgebaseservice
```

## api

### 1. Install api into the venv

```bash
sudo -u limited_user /home/limited_user/environments/knowledge-base-service/bin/pip install -e /home/limited_user/applications/KnowledgeBaseService/api
```

### 2. Create the .env file

```bash
nano /home/limited_user/applications/KnowledgeBaseService/api/.env
```

Contents:

```
NAME_APP=KnowledgeBaseServiceAPI
RUN_ENVIRONMENT=production
PATH_TO_LOGS=/home/limited_user/logs
DATABASE_URL=postgresql:///knowledge_base
```

### 3. Install the systemd service

```bash
sudo cp /home/limited_user/applications/KnowledgeBaseService/api/systemd/knowledgebaseservice-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable knowledgebaseservice-api
sudo systemctl start knowledgebaseservice-api
```

### 4. Verify it's running

```bash
sudo systemctl status knowledgebaseservice-api
curl http://127.0.0.1:8007/
```

The api runs on port 8007 behind localhost only. Configure nginx to reverse proxy to this port for external access.
