# pg-memory Commands Reference

**Complete list of slash commands for pg-memory v3.1.0**

---

## 🦞 pg-memory Commands

These commands are provided by the pg-memory integration.

### `/pg-search <query>`

Search pg-memory with semantic search.

**Syntax:**
```
/pg-search <query> [--max N] [--min-score N] [--days N] [--tags tag1,tag2]
```

**Examples:**
```
/pg-search what did I work on yesterday
/pg-search API decision --max 10
/pg-search bug fixes --days 7
/pg-search project alpha --tags project,critical
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--max N` | 5 | Maximum results to return |
| `--min-score N` | 0.3 | Minimum similarity score (0.0-1.0) |
| `--days N` | none | Limit to last N days |
| `--tags` | none | Filter by comma-separated tags |

**Output:**
- Ranked results with similarity scores
- Timestamps and tags
- Observation IDs for reference

---

### `/pg-get <observation-id>`

Get a specific observation by ID.

**Syntax:**
```
/pg-get <xid>
```

**Examples:**
```
/pg-get d6kngar24tejs7b24t50
/pg-get 824a19a8-9279-4ac5-9c46-2a333685bf90
```

**Output:**
- Full observation content
- Metadata (tags, importance, timestamp)
- Source information

---

### `/pg-recent`

Show recent observations from the last N days.

**Syntax:**
```
/pg-recent [--days N] [--limit N]
```

**Examples:**
```
/pg-recent
/pg-recent --days 7
/pg-recent --days 30 --limit 20
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--days N` | 1 | Number of days to look back |
| `--limit N` | 10 | Maximum results to return |

**Output:**
- Chronological list of recent observations
- Timestamps and preview snippets

---

### `/pg-stats`

Show pg-memory database statistics.

**Syntax:**
```
/pg-stats
```

**Examples:**
```
/pg-stats
```

**Output:**
- Total observations
- Session count
- Latest capture time
- Average importance score
- pgvector status
- Cache size

---

## 🔧 OpenClaw Commands (Related to pg-memory)

These are built-in OpenClaw commands that interact with pg-memory.

### `/new`

Start a new session.

**Syntax:**
```
/new
```

**pg-memory Integration:**
- Triggers `pg-memory-migration` hook
- Migrates any unmigrated markdown files to PostgreSQL
- Creates new session in database

**Related:** [`/reset`](#reset)

---

### `/reset`

Reset current session (same as `/new`).

**Syntax:**
```
/reset
```

**pg-memory Integration:**
- Triggers `pg-memory-migration` hook
- Migrates any unmigrated markdown files to PostgreSQL
- Creates new session in database

**Related:** [`/new`](#new)

---

### `/memory`

View memory-related commands (if available in your OpenClaw version).

**Syntax:**
```
/memory
```

**Output:**
- List of memory-related commands
- Memory status

---

## 📊 CLI Commands (Terminal)

These commands are run in your terminal, not in OpenClaw chat.

### `python3 pg_memory.py --stats`

Show database statistics.

**Syntax:**
```bash
cd ~/.openclaw/workspace/repos/openclaw-pg-memory/scripts
python3 pg_memory.py --stats
```

**Output:** Same as `/pg-stats`

---

### `python3 pg_memory.py --search <query>`

Search observations from terminal.

**Syntax:**
```bash
python3 pg_memory.py --search "your query"
```

**Examples:**
```bash
python3 pg_memory.py --search "API decision"
python3 pg_memory.py --search "bug fix" --limit 10
```

---

### `python3 pg_memory.py --recent [days]`

Show recent observations.

**Syntax:**
```bash
python3 pg_memory.py --recent 7
```

**Examples:**
```bash
python3 pg_memory.py --recent      # Last 24 hours
python3 pg_memory.py --recent 7    # Last 7 days
python3 pg_memory.py --recent 30   # Last 30 days
```

---

### `python3 pg_memory.py --backup`

Create database backup.

**Syntax:**
```bash
python3 pg_memory.py --backup
```

**Output:**
- Backup file in `~/.openclaw/workspace/backups/`

---

### `python3 migrate-markdown-to-pgmemory.py`

Migrate markdown files to PostgreSQL.

**Syntax:**
```bash
cd ~/.openclaw/workspace/repos/openclaw-pg-memory/scripts
python3 migrate-markdown-to-pgmemory.py
```

**Output:**
- Migration report
- Number of files migrated
- Any errors encountered

---

### `./cleanup-memory-files.sh [days]`

Archive old markdown files.

**Syntax:**
```bash
./cleanup-memory-files.sh      # Keep last 7 days (default)
./cleanup-memory-files.sh 14   # Keep last 14 days
./cleanup-memory-files.sh 30   # Keep last 30 days
```

**Output:**
- List of archived files
- Remaining files count

---

## 🎯 Command Quick Reference

| Command | Type | Purpose |
|---------|------|---------|
| `/pg-search` | Chat | Semantic search |
| `/pg-get` | Chat | Get by ID |
| `/pg-recent` | Chat | Recent observations |
| `/pg-stats` | Chat | Database stats |
| `/new` | Chat | New session (+ migration) |
| `/reset` | Chat | Reset session (+ migration) |
| `pg_memory.py --stats` | CLI | Database stats |
| `pg_memory.py --search` | CLI | Search from terminal |
| `pg_memory.py --recent` | CLI | Recent from terminal |
| `pg_memory.py --backup` | CLI | Create backup |
| `migrate-markdown-to-pgmemory.py` | CLI | Manual migration |
| `cleanup-memory-files.sh` | CLI | Archive old files |

---

## 💡 Usage Examples

### Find Work from Yesterday
```
/pg-search what did I work on yesterday --days 2
```

### Get Specific Decision
```
/pg-search API architecture decision --tags decision
/pg-get d6kngar24tejs7b24t50
```

### Review This Week's Work
```
/pg-recent --days 7 --limit 20
```

### Check Database Health
```
/pg-stats
```

### Manual Migration (if needed)
```bash
cd ~/.openclaw/workspace/repos/openclaw-pg-memory/scripts
python3 migrate-markdown-to-pgmemory.py
```

### Clean Up Old Files
```bash
./cleanup-memory-files.sh 14
```

---

## 🔍 Troubleshooting

### Command Not Found
```
Error: Command /pg-search not found
```

**Solution:**
1. Verify pg-search skill is installed:
   ```bash
   ls -la ~/.openclaw/workspace/skills/pg-search/
   ```
2. Restart OpenClaw:
   ```bash
   openclaw gateway restart
   ```

### No Results Returned
```
🔍 No results found for: "query"
```

**Solutions:**
1. Try a broader query
2. Lower minimum score: `--min-score 0.2`
3. Check if data exists: `/pg-stats`
4. Run migration: `python3 migrate-markdown-to-pgmemory.py`

### Migration Fails
```
Error: Migration failed
```

**Solutions:**
1. Check Python dependencies:
   ```bash
   pip3 install psycopg2-binary
   ```
2. Verify database connection:
   ```bash
   psql -U openclaw -d openclaw_memory -c "SELECT 1"
   ```
3. Check logs:
   ```bash
   tail -20 ~/.openclaw/workspace/logs/pg-memory-migration.log
   ```

---

## 📚 Related Documentation

- [Features Overview](FEATURES.md) - What pg-memory can do
- [Integration Guide](INTEGRATION-OPENCLAW.md) - Setup instructions
- [Cron Examples](CRON-EXAMPLES.md) - Automation setup
- [Observations Reference](OBSERVATIONS.md) - Observation types and fields

---

*pg-memory v3.1.0 - Production Ready*

---

## Observation Resolution Lifecycle (v3.1.0)

### `resolve` — Mark Observation as Resolved

Mark an observation as resolved with a timestamp. Resolved observations are kept for 6 months before automatic cleanup.

**Usage:**
```bash
python3 scripts/pg_memory.py resolve <observation-id> [--date ISO_DATE]
```

**Examples:**
```bash
# Mark as resolved now
python3 scripts/pg_memory.py resolve 01jvtxk8h5m2n3p4q5r6s7t8

# Mark as resolved on specific date
python3 scripts/pg_memory.py resolve 01jvtxk8h5m2n3p4q5r6s7t8 --date 2026-03-05T10:30:00
```

**Output:**
```
✅ Observation 01jvtxk8h5m2n3p4q5r6s7t8 marked as resolved
   Resolved at: 2026-03-05T10:30:00
```

---

### `cleanup` — Delete Old Resolved Observations

Delete resolved observations older than specified days (default: 180 days = 6 months).

**Usage:**
```bash
python3 scripts/pg_memory.py cleanup [--days DAYS] [--dry-run]
```

**Options:**
- `--days N` — Delete observations resolved more than N days ago (default: 180)
- `--dry-run` — Show what would be deleted without actually deleting

**Examples:**
```bash
# Delete resolved observations older than 6 months
python3 scripts/pg_memory.py cleanup

# Preview what would be deleted
python3 scripts/pg_memory.py cleanup --dry-run

# Delete resolved observations older than 30 days
python3 scripts/pg_memory.py cleanup --days 30
```

**Output:**
```
📊 Found 42 resolved observations older than 180 days
   Cutoff date: 2025-09-07T03:00:00
✅ Deleted 42 resolved observations
```

---

### Automatic Cleanup

A cron job runs daily at 3:00 AM to clean up resolved observations older than 6 months:

```cron
0 3 * * * ~/.openclaw/workspace/repos/openclaw-pg-memory/scripts/cleanup-resolved-obs.sh
```

**Log file:** `~/.openclaw/workspace/logs/pg-memory-cleanup.log`

**Manual run:**
```bash
~/.openclaw/workspace/repos/openclaw-pg-memory/scripts/cleanup-resolved-obs.sh
```

---

### Lifecycle Policy

| Status | resolved_at | Deletion Policy |
|--------|-------------|-----------------|
| **UNRESOLVED** | NULL | ❌ NEVER DELETE |
| **RESOLVED** | < 180 days | ❌ KEEP |
| **RESOLVED** | > 180 days | ✅ DELETE |

**See also:** [Observation Lifecycle Policy](../MEMORY.md#postgresql-observations--lifecycle-policy)

