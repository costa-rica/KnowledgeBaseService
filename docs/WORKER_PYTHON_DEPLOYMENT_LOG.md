# worker-python Deployment Log — avatar08

Completed 2026-04-03. Documents the steps taken to get worker-python running on avatar08 (Ubuntu 24.04 LTS, FSDC network).

## 1. Install worker-python into the venv

```bash
sudo -u limited_user /home/limited_user/environments/knowledge-base-service/bin/pip install -e /home/limited_user/applications/KnowledgeBaseService/worker-python
```

## 2. Create the .env file

Created `/home/limited_user/applications/KnowledgeBaseService/worker-python/.env`:

```
NAME_APP=KnowledgeBaseServiceWorkerPython
RUN_ENVIRONMENT=production
PATH_TO_LOGS=/home/limited_user/logs
DATABASE_URL=postgresql:///knowledge_base
VAULT_PATH=/home/limited_user/project_resources/PersonalWeb03/obsidian
```

## 3. Install obsidian-headless globally

The `ob` CLI was originally installed under nick's npm prefix (`/home/nick/.npm-global/`), but `limited_user` cannot traverse `/home/nick/` (750 permissions). Reinstalled globally:

```bash
sudo npm install -g obsidian-headless
sudo ln -s /usr/lib/node_modules/obsidian-headless/cli.js /usr/local/bin/ob
sudo chmod +x /usr/lib/node_modules/obsidian-headless/cli.js
```

Verified with:

```bash
sudo -u limited_user /usr/local/bin/ob --version
```

## 4. Log in and configure ob sync as limited_user

The `ob` sync config is per-user, so `limited_user` needed its own login and sync setup:

```bash
sudo -u limited_user ob login
sudo -u limited_user ob sync-setup --vault "Nick Vault" --path /home/limited_user/project_resources/PersonalWeb03/obsidian
sudo -u limited_user ob sync-config --path /home/limited_user/project_resources/PersonalWeb03/obsidian --mode mirror-remote
```

Mirror-remote mode means the local vault is a read-only replica — any local changes are reverted to match the remote.

## 5. Fix vault directory ownership

The vault files were owned by `nick`, causing `EPERM: operation not permitted` when `ob` tried to set file timestamps during sync:

```bash
sudo chown -R limited_user:limited_user /home/limited_user/project_resources/PersonalWeb03/obsidian
```

## 6. Systemd service file

The installed service file at `/etc/systemd/system/knowledgebaseservice-worker-python.service` needed:

- `ExecStart` pointing to `main.py` (not `src/main.py`) — the top-level `main.py` is the entrypoint
- `PATH` environment including `/usr/local/bin` so the `ob` binary is found:

```
Environment="PATH=/home/limited_user/environments/knowledge-base-service/bin:/usr/local/bin:/usr/bin:/bin"
```

## 7. Successful run

After all fixes, the worker completed successfully:

```
Logger initialized: app=KnowledgeBaseServiceWorkerPython, env=production
Worker started
Starting vault sync: /home/limited_user/project_resources/PersonalWeb03/obsidian
Vault sync completed successfully
Found 69 markdown files in vault
Scan complete: 69 new, 0 modified, 0 unchanged, 0 errors
Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
Embedding generation complete: 69 embedded, 0 errors
Database transaction committed successfully
Worker finished successfully
```

## Issues encountered (summary)

| Issue | Cause | Fix |
| ----- | ----- | --- |
| `No module named 'src'` | Service ran `src/main.py` instead of `main.py` | Changed ExecStart to `python main.py` |
| `ob command not found` | `ob` not on limited_user's PATH | Symlinked to `/usr/local/bin/ob` |
| `Permission denied: 'ob'` | Symlink pointed into `/home/nick/` (750) | Installed obsidian-headless globally under `/usr/lib/node_modules/` |
| `No sync configuration found` | ob sync config is per-user | Ran `ob login` and `ob sync-setup` as limited_user |
| `EPERM: utime` | Vault files owned by nick | `chown -R limited_user:limited_user` on vault dir |
