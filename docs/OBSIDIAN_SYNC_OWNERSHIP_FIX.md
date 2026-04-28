# Obsidian Sync Ownership Fix

How to recover from an `EPERM: operation not permitted, utime` error when running `ob sync` against the vault at `/home/limited_user/project_resources/PersonalWeb03/obsidian` on the avatar08 server.

## Symptom

```
Sync error: Error: EPERM: operation not permitted, utime '.../VAULT-MAP.md'
  errno: -1, code: 'EPERM', syscall: 'utime'
```

## Cause

The vault directory is owned by `limited_user`. The `ob sync` CLI calls `utimes()` to stamp file mtime/atime after writing each file. On Linux, `utimes()` requires the caller to **own** the file — group-write permission is not enough.

If `ob sync` is run as a non-owning user (e.g. `nick`), two things go wrong:

1. The sync fails with `EPERM` the first time it tries to stamp a file owned by `limited_user`.
2. Any new files the sync creates are owned by the running user (`nick`), poisoning future runs by `limited_user` (the systemd worker), which will then EPERM in the opposite direction.

The systemd unit `knowledgebaseservice-worker-python.service` correctly runs as `limited_user`. Manual runs by other users break this invariant.

## Fix

### 1. Re-own any vault files not owned by `limited_user`

Find them:

```bash
find /home/limited_user/project_resources/PersonalWeb03/obsidian -not -user limited_user
```

Re-own everything in the vault to `limited_user`:

```bash
sudo chown -R limited_user:limited_user /home/limited_user/project_resources/PersonalWeb03/obsidian
```

### 2. Run the sync as `limited_user`

Preferred: trigger the systemd unit (it runs as `limited_user` and uses the configured environment).

```bash
sudo systemctl start knowledgebaseservice-worker-python.service
sudo journalctl -u knowledgebaseservice-worker-python.service -n 50 --no-pager
```

Alternative: invoke `ob` directly as `limited_user`. If `ob` is not on `limited_user`'s `PATH`, point at the global install:

```bash
sudo -u limited_user /home/nick/.npm-global/bin/ob sync \
  --path /home/limited_user/project_resources/PersonalWeb03/obsidian
```

## Going forward

- Never run `ob sync` against this vault as a user other than `limited_user`.
- The timer `knowledgebaseservice-worker-python.timer` fires daily at 23:00; for ad-hoc syncs, use `systemctl start` on the service unit.
