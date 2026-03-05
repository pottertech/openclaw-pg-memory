## [3.1.0] - 2026-03-05

### Added
- 🎯 Observation resolution lifecycle management
- ✅ `resolve_observation()` function - Mark observations as resolved with timestamp
- ✅ `cleanup_resolved_observations()` function - Auto-delete old resolved observations
- ✅ CLI command: `resolve` - Mark observation as resolved
- ✅ CLI command: `cleanup` - Delete resolved observations older than N days
- ✅ Standalone script: `scripts/cleanup-resolved.py`
- ✅ Cron wrapper: `scripts/cleanup-resolved-obs.sh`
- ✅ Automated daily cleanup at 3:00 AM via cron
- ✅ Documentation: `docs/RELEASE-v3.1.0.md`
- ✅ Policy: Unresolved=never delete, Resolved=180 days retention

### Changed
- 📦 Version bump: 3.0.0 → 3.1.0
- 📚 All documentation updated to v3.1.0
- 🧪 Test files updated to v3.1.0

### Fixed
- 🔧 Connection pool access in resolve/cleanup functions (`mem._pool`)
- 🔧 Standalone script for environments without full pg_memory.py dependencies

### Technical Details
- **Retention Policy:**
  - Unresolved observations: NEVER deleted (permanent)
  - Resolved observations: 180 days (6 months)
  - Daily markdown files: 7 days (after migration)
- **Database Schema:** No changes required (columns already exist)
- **Backward Compatibility:** 100% compatible with v3.0.0

### Files Added
- `scripts/cleanup-resolved.py` (standalone CLI)
- `scripts/cleanup-resolved-obs.sh` (cron wrapper)
- `docs/RELEASE-v3.1.0.md` (release notes)

### Migration
- No database migration needed
- No config changes required
- Pull and run: `git pull origin main`

---
