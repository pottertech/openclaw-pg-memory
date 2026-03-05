---
name: pg-memory-migration
description: "Migrate markdown memory files to pg-memory when /new is run"
homepage: https://github.com/pottertech/openclaw-pg-memory
metadata:
  {
    "openclaw":
      {
        "emoji": "🦞",
        "events": ["command:new", "command:reset"],
        "requires": { "config": ["workspace.dir"] },
        "install": [{ "id": "local", "kind": "workspace", "label": "Workspace Hook" }],
      },
  }
---

# pg-memory Migration Hook

Automatically migrates markdown memory files to PostgreSQL when you run `/new` or `/reset`.

## What It Does

When you run `/new` or `/reset` to start a fresh session:

1. **Runs migration script** - Executes `migrate-markdown-to-pgmemory.py`
2. **Migrates any new files** - Finds markdown files not yet in PostgreSQL
3. **Logs output** - Writes results to `~/.openclaw/workspace/logs/pg-memory-migration.log`
4. **Silent operation** - Runs in background without interrupting your workflow

## Why This Matters

OpenClaw creates daily markdown files in `memory/YYYY-MM-DD.md` when you start new sessions. This hook ensures those files are automatically migrated to pg-memory (PostgreSQL) so you can:

- Search all memories with semantic search
- Access memories across multiple OpenClaw instances
- Keep markdown files as backup while PostgreSQL is primary

## Requirements

- **Config**: `workspace.dir` must be set
- **Python**: Python 3.10+ must be available
- **pg-memory**: Migration script must exist at `repos/openclaw-pg-memory/scripts/migrate-markdown-to-pgmemory.py`

## Output

Migration results are logged to:
```
~/.openclaw/workspace/logs/pg-memory-migration.log
```

## View Logs

```bash
# Check latest migration
tail -20 ~/.openclaw/workspace/logs/pg-memory-migration.log

# Watch in real-time
tail -f ~/.openclaw/workspace/logs/pg-memory-migration.log
```

## Configuration

No configuration required. The hook automatically:

- Finds the migration script in the pg-memory repo
- Runs with your current Python environment
- Logs to the standard workspace logs directory

## Disabling

To disable this hook:

```bash
openclaw hooks disable pg-memory-migration
```

Or remove it from your config:

```json
{
  "hooks": {
    "internal": {
      "entries": {
        "pg-memory-migration": { "enabled": false }
      }
    }
  }
}
```

## Relationship to Cron Job

This hook complements (doesn't replace) the daily cron job:

| Hook | Cron Job |
|------|----------|
| Runs on `/new` or `/reset` | Runs daily at 3 AM |
| Immediate migration | Backup/safety net |
| Only when you end session | Runs regardless of activity |

**Recommendation:** Keep both enabled for complete coverage.

## Troubleshooting

**Hook not running?**
```bash
# Check if hook is enabled
openclaw hooks list

# Check eligibility
openclaw hooks check

# View hook info
openclaw hooks info pg-memory-migration
```

**Migration failing?**
```bash
# Test migration script manually
cd ~/.openclaw/workspace/repos/openclaw-pg-memory/scripts
python3 migrate-markdown-to-pgmemory.py

# Check logs
cat ~/.openclaw/workspace/logs/pg-memory-migration.log
```

---

*Part of pg-memory v3.0.0 - Production Ready*
