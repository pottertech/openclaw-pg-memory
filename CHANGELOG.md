# Changelog

All notable changes to pg-memory will be documented in this file.

## v3.1.2 — Clean Separation from token-guardian (2026-03-12)

### BREAKING CHANGE: Removed Context Protection

**Problem:** v3.1.1 introduced Context Protection features that overlapped with token-guardian.

**Solution:** Complete separation of responsibilities.

### What Changed

| Feature | v3.1.1 | v3.1.2 |
|---------|--------|--------|
| Context Guardian | ✅ Auto-installed | ❌ Removed |
| Compaction Cron | ✅ Auto-installed | ❌ Removed |
| Working Buffer | ✅ Auto-created | ❌ Removed |
| Bloat Detection | ✅ Hourly checks | ❌ Removed |
| Token Monitoring | ✅ Enabled | ❌ Disabled |
| Durable Storage | ✅ | ✅ |
| Semantic Retrieval | ✅ | ✅ |
| Context Restoration | ✅ | ✅ |

### New: Clean Separation

**pg-memory owns:**
- Durable storage (PostgreSQL)
- Semantic embeddings (BGE-M3)
- Vector retrieval
- Context restoration post-compaction
- Long-term summaries
- Backups

**token-guardian owns:**
- Token threshold monitoring
- Live context reduction
- Bloat detection
- Workspace cleanup
- Emergency pruning

### Migration from v3.1.1

```bash
# 1. Update pg-memory
git pull
./install.sh --separation-mode

# 2. Install token-guardian
git clone https://github.com/pottertech/openclaw-token-guardian.git
cd openclaw-token-guardian && ./install.sh

# 3. Remove legacy cron jobs
crontab -e
# Delete: context-guardian, compaction-cron

# 4. Restart
openclaw gateway restart
```

### Documentation
- Added `docs/SEPARATION.md` with complete ownership guide
- Updated README with ownership matrix
- Added migration guide

---

## v3.1.1 — DEPRECATED: Context Protection (2026-03-09)

> ⚠️ **DEPRECATED:** These features moved to token-guardian in v3.1.2

### Deprecated Features (now in token-guardian)

- `context-guardian.sh` → token-guardian
- `compaction-cron.sh` → token-guardian
- `working-buffer.md` → token-guardian
- Bloat detection → token-guardian
- Live context management → token-guardian

---
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
