---
origin: claude-opus-4-7
title: Obsidian Vault Sync Guide for AI Agents
added: 2026-04-26
---

# Obsidian Vault Sync Guide for AI Agents

Instructions for an AI coding agent that needs to sync the Obsidian vault on the **`fdc-avatar08`** server (FSDC network) using the `ob` (obsidian-headless) CLI. These instructions are specific to that machine — paths, users, and the systemd unit name will differ on other hosts.

The vault lives at `/home/limited_user/project_resources/PersonalWeb03/obsidian` and is owned by `limited_user`.

## Critical preconditions

Before running any sync command, verify these — getting them wrong will corrupt vault state or fail with `EPERM`:

1. **You must be running as `limited_user`.** The vault is owned by `limited_user`; `ob sync` calls `utimes()` and EPERMs if the caller is not the file owner. Use `sudo -u limited_user ...` or trigger the systemd unit.
2. **`ob login` must already be authenticated** for `limited_user` (or for whoever's `~/.config/obsidian-headless` the run sees). Check with `ob sync-list-remote`.
3. **No other sync is in progress.** Look for `.obsidian/.sync.lock` in the vault.
4. **Choose the sync mode deliberately.** The wrong mode will silently delete files. See the three modes below.

## The three sync modes

`ob sync-config --path <vault> --mode <mode>` writes the mode into the vault's local config; `ob sync --path <vault>` then runs whichever mode is configured. Always set the mode explicitly before running a sync — never assume the prior mode is what you want.

### 1. `bidirectional`

Two-way sync. Local changes are pushed to the remote; remote changes are pulled to local. Conflicts are resolved by the `--conflict-strategy` (default: `merge`).

```bash
ob sync-config --path /home/limited_user/project_resources/PersonalWeb03/obsidian --mode bidirectional
ob sync        --path /home/limited_user/project_resources/PersonalWeb03/obsidian
```

Use when: the local vault is a primary working copy and you want edits made on this server to flow back to other devices.

Risk: if the local copy was edited by the wrong user or contains stale state, those changes will be pushed to the remote. Inspect `git status` (if the vault is git-tracked) or compare against the remote before running.

### 2. `pull-only`

Download remote changes; do not push local changes. Local-only files are **kept**, not deleted. Local edits to files that also exist remotely are overwritten by the remote version.

```bash
ob sync-config --path /home/limited_user/project_resources/PersonalWeb03/obsidian --mode pull-only
ob sync        --path /home/limited_user/project_resources/PersonalWeb03/obsidian
```

Use when: the local vault is a read-only consumer (e.g. for indexing/embedding) and you want the latest remote content but also want to preserve local-only artifacts (caches, build outputs) inside the vault dir.

### 3. `mirror-remote`

Make the local vault an exact replica of the remote. Remote changes are downloaded; **local-only files are deleted**; local edits are reverted to remote state. Nothing is pushed.

```bash
ob sync-config --path /home/limited_user/project_resources/PersonalWeb03/obsidian --mode mirror-remote
ob sync        --path /home/limited_user/project_resources/PersonalWeb03/obsidian
```

Use when: the local vault is a strictly read-only mirror (e.g. for the `knowledgebaseservice-worker-python` worker). This is the mode the worker uses.

Risk: any file that exists locally but not remotely will be **deleted without confirmation**. Never run `mirror-remote` against a vault that has local-only work in it.

## Running the sync

### Preferred: via systemd

The repo ships a systemd unit that runs the sync (`mirror-remote` mode) as `limited_user`:

```bash
sudo systemctl start knowledgebaseservice-worker-python.service
sudo journalctl -u knowledgebaseservice-worker-python.service -n 100 --no-pager
```

The unit also runs daily at 23:00 via `knowledgebaseservice-worker-python.timer`.

### Manual: as `limited_user`

```bash
sudo -u limited_user ob sync --path /home/limited_user/project_resources/PersonalWeb03/obsidian
```

If `ob` is not on `limited_user`'s `PATH`, use the global install path: `/home/nick/.npm-global/bin/ob`.

### Continuous

`ob sync --path <vault> --continuous` keeps the process running and syncs on changes. Only useful for foreground/dev work; do not invoke from an automated agent run.

## Failure modes to watch for

- **`EPERM ... utime '...'`** — you (or some prior run) wrote files as the wrong user. The `ob` CLI calls `utimes()` to stamp file timestamps, and on Linux `utimes()` requires the caller to **own** the file (group-write is not enough). If files inside the vault were created by a user other than `limited_user`, those files trigger EPERM on the next sync, and the run aborts mid-stream. Fix:
  ```bash
  sudo chown -R limited_user:limited_user /home/limited_user/project_resources/PersonalWeb03/obsidian
  ```
  Then re-run as `limited_user`. **Lesson:** never invoke `ob sync` against this vault as anything other than `limited_user` — not even for a one-off manual run. Always go through `sudo -u limited_user` or the systemd unit.
- **`TimeoutNaNWarning: NaN is not a number`** — benign warning from the `ob` CLI; ignore.
- **`Sync error: ... .sync.lock`** — a previous sync is still running or crashed. Verify no `ob` process is alive (`pgrep -af 'ob sync'`), then delete the lock file as `limited_user`.
- **Sync deletes files you wanted to keep** — you ran `mirror-remote` against a vault with local-only files. Restore from a backup or push the files to the remote first using `bidirectional`.

## Verification after a sync

```bash
ls -la /home/limited_user/project_resources/PersonalWeb03/obsidian
find /home/limited_user/project_resources/PersonalWeb03/obsidian -not -user limited_user
test -f /home/limited_user/project_resources/PersonalWeb03/obsidian/LEFT-OFF.md && echo "vault looks healthy"
```

The `find` should return nothing — every file in the vault should be owned by `limited_user`.
