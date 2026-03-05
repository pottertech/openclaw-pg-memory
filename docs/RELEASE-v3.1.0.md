# pg-memory v3.1.0 — Release Notes

**Release Date:** 2026-03-05  
**Previous Version:** v3.0.0  
**Status:** ✅ Production Ready

---

## 🎯 What's New in v3.1.0

### Observation Resolution Lifecycle (NEW)

Complete lifecycle management for observations with automatic cleanup:

- **Resolve Command:** Mark observations as resolved with timestamp
- **Cleanup Command:** Auto-delete resolved observations after configurable period
- **Default Retention:** 180 days (6 months) for resolved observations
- **Unresolved Observations:** NEVER deleted (permanent until resolved)
- **Automated Cleanup:** Daily cron job at 3:00 AM

**Commands:**
```bash
# Mark observation as resolved
python3 scripts/pg_memory.py resolve <observation-id> [--date ISO_DATE]

# Cleanup old resolved observations
python3 scripts/pg_memory.py cleanup [--days 180] [--dry-run]
```

**Policy:**
| Status | Retention | Auto-Delete |
|--------|-----------|-------------|
| Unresolved | Forever | ❌ Never |
| Resolved | 180 days | ✅ After 6 months |
| Daily Markdown | 7 days | ✅ After migration |

---

## 📦 New Files

| File | Purpose |
|------|---------|
| `scripts/cleanup-resolved.py` | Standalone resolve/cleanup CLI |
| `scripts/cleanup-resolved-obs.sh` | Cron wrapper for daily cleanup |
| `docs/RELEASE-v3.1.0.md` | This release notes file |

---

## 🔄 Changes from v3.0.0

### Added
- ✅ `resolve_observation()` function - Mark observations as resolved
- ✅ `cleanup_resolved_observations()` function - Auto-delete old resolved
- ✅ CLI commands: `resolve` and `cleanup`
- ✅ Cron job for automated daily cleanup
- ✅ Documentation for lifecycle management
- ✅ Policy stored in MEMORY.md

### Changed
- ✅ Version bumped: 3.0.0 → 3.1.0
- ✅ All documentation updated to v3.1.0
- ✅ Test files updated to v3.1.0

### Fixed
- ✅ Connection pool access in resolve/cleanup functions (`mem._pool`)
- ✅ Standalone script for environments without full pg_memory.py

### Not Changed
- ✅ Core observation/capture functionality
- ✅ XID session IDs
- ✅ pgvector integration
- ✅ Multi-instance support

---

## 🚀 Upgrade from v3.0.0

### Database Schema
**No migration required!** The schema already has the required columns:
- `status` (default: 'active')
- `resolved_at` (timestamp, nullable)

### Steps
1. **Pull latest code:**
   ```bash
   cd ~/.openclaw/workspace/repos/openclaw-pg-memory
   git pull origin main
   ```

2. **Verify version:**
   ```bash
   python3 scripts/pg_memory.py --help
   # Should show v3.1.0
   ```

3. **Test cleanup (dry-run):**
   ```bash
   python3 scripts/pg_memory.py cleanup --dry-run
   ```

4. **Cron job auto-installs** (if not already present):
   ```bash
   crontab -l | grep cleanup
   # Should show daily 3 AM cleanup
   ```

---

## 📊 Version Comparison

| Feature | v3.0.0 | v3.1.0 |
|---------|--------|--------|
| Observation Capture | ✅ | ✅ |
| Semantic Search | ✅ | ✅ |
| XID Session IDs | ✅ | ✅ |
| Multi-Instance | ✅ | ✅ |
| **Resolve Observations** | ❌ | ✅ |
| **Auto Cleanup** | ❌ | ✅ |
| **Lifecycle Policy** | ❌ | ✅ |
| Cron Integration | ✅ | ✅ Enhanced |

---

## 🧪 Testing

```bash
# Test resolve command
python3 scripts/pg_memory.py resolve <test-obs-id>

# Test cleanup (dry-run)
python3 scripts/pg_memory.py cleanup --dry-run

# Test cleanup (actual)
python3 scripts/pg_memory.py cleanup --days 180
```

---

## 📝 Migration Notes

**From v3.0.0 to v3.1.0:**
- ✅ No database migration needed
- ✅ No config changes required
- ✅ Backward compatible with all v3.0.0 features
- ✅ New commands are optional (existing workflows unchanged)

---

## 🎯 Use Cases

### When to Resolve an Observation
- Task completed
- Issue fixed
- Decision implemented
- Action item closed
- Question answered

### Cleanup Benefits
- Database hygiene (remove old closed items)
- Performance (smaller active dataset)
- Compliance (auto-delete after retention period)
- Focus (keep unresolved items visible)

---

## 📖 Related Documentation

- [COMMANDS.md](COMMANDS.md#observation-resolution-lifecycle-v310) - Full command reference
- [FEATURES.md](FEATURES.md) - Complete feature list
- [CRON-EXAMPLES.md](CRON-EXAMPLES.md) - Cron job configurations
- [MEMORY.md](../../MEMORY.md#postgresql-observations--lifecycle-policy) - Lifecycle policy

---

## 👥 Credits

**Developed by:** Arty Craftson, Potter's Quill Media  
**Approved by:** Skip Potter  
**Date:** 2026-03-05

**GitHub:** https://github.com/pottertech/openclaw-pg-memory  
**Release:** v3.1.0

---

*pg-memory v3.1.0 - Observation Lifecycle Management*
