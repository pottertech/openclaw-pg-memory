# Changelog

All notable changes to pg-memory will be documented in this file.

## v3.1.1 — Context Protection (2026-03-09)

### New: Automatic Context Overflow Prevention
**Problem:** Agents lose context during long sessions when context window exceeds 60% (danger zone).

**Solution:** Multi-layer protection system installed automatically with pg-memory.

### What's Added

| Component | Purpose | Auto-installs |
|-----------|---------|---------------|
| `context-guardian.sh` | Hourly bloat detection (MEMORY.md >800 lines, SESSION-STATE stale) | ✅ Yes |
| `compaction-cron.sh` | Weekly archive of old daily notes (>7 days) | ✅ Yes |
| `working-buffer.md` | Danger zone capture — survives context truncation | ✅ Yes |
| `memory/archive/` | Archived content storage | ✅ Yes |

### Protection Protocol

```
Session Start:
├── Load working-buffer.md (survives compaction)
├── Load SESSION-STATE.md (active task context)
├── Skip MEMORY.md unless needed (<50 lines or specifically required)
└── Load only today + yesterday daily notes

Danger Zone (>60% context):
├── STOP — don't respond
├── LOG exchange to working-buffer.md
└── THEN respond

After Compaction:
├── Read working-buffer.md FIRST
├── Extract to SESSION-STATE.md
└── Clear buffer
```

### For Existing Users
Run `./install.sh` again — Step 9 will auto-install context protection.

### For New Users
Installed automatically with pg-memory v3.1.1+.

---

## v3.1.0 — Observation Lifecycle (2026-03-05)

- Added `resolved_at` timestamp
- Added automatic cleanup of resolved observations (>180 days)
- Schema updates with status tracking

## v3.0.0 — Production Release (2026-02-28)

- Complete XID migration
- Tiered summary generation
- Automated backups
- OpenClaw integration
