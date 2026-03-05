# pg-memory v3.1.0 - Complete Documentation

**Production-Ready Structured Memory for OpenClaw**

---

## 📚 Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [API Reference](#api-reference)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance](#maintenance)

---

## Installation

### Quick Install (Recommended)

```bash
git clone https://github.com/pottertech/openclaw-pg-memory.git
cd openclaw-pg-memory
./install.sh
```

### Manual Installation

See [`MANUAL-INSTALL.md`](MANUAL-INSTALL.md) for step-by-step manual installation.

### Requirements

| Component | Version | Install |
|-----------|---------|---------|
| **macOS** | 12+ | Built-in |
| **Homebrew** | Latest | [brew.sh](https://brew.sh) |
| **PostgreSQL** | 18+ | `brew install postgresql@18` |
| **Python** | 3.10+ | Built-in |
| **Node.js** | 18+ | `brew install node` |
| **Ollama** | Latest | `brew install ollama` |

---

## Configuration

### Environment Variables

Add to `~/.zshrc`:

```bash
export PG_MEMORY_DB=openclaw_memory
export PG_MEMORY_USER=openclaw
export PG_MEMORY_HOST=localhost
export PG_MEMORY_PORT=5432
export PG_MEMORY_DEBUG=0
export OPENCLAW_INSTANCE_ID=$(uuidgen)
```

### memory.yaml Configuration

Location: `~/.openclaw/workspace/config/memory.yaml`

```yaml
memory:
  primary_backend: postgresql
  markdown_backup: true
  retention_days: 7
  agent_id: openclaw
  fallback_on_pgdb_down: true

postgresql:
  host: localhost
  port: 5432
  database: openclaw_memory
  user: openclaw
```

### OpenClaw Integration

Location: `~/.openclaw/openclaw.json`

```json
{
  "hooks": {
    "internal": {
      "entries": {
        "pg-memory-compaction": {
          "enabled": true,
          "path": "./hooks/pg-memory-compaction/handler.js"
        }
      }
    }
  }
}
```

---

## Usage

### Command-Line Interface

```bash
# View statistics
python3 scripts/pg_memory.py --stats

# Search memory
python3 scripts/pg_memory.py --search "your query"

# Natural language query
python3 scripts/pg_memory.py --query "What did we discuss about AI?"

# Create backup
python3 scripts/pg_memory.py --backup

# View recent observations
python3 scripts/pg_memory.py --recent 10

# Initialize database (first-time only)
python3 scripts/pg_memory.py --init
```

### Python API

```python
from pg_memory import PostgresMemory

# Initialize
mem = PostgresMemory()

# Start a session
session_id = mem.start_session(
    session_key="my-session",
    provider="discord"
)

# Capture an observation
mem.capture_observation(
    session_id=session_id,
    content="Important decision made",
    tags=["decision", "project"],
    importance_score=0.9
)

# Search
results = mem.search_observations(
    query="AI discussion",
    limit=10
)

# End session
mem.end_session(session_id)
mem.close()
```

### Web Dashboard

Start the dashboard:

```bash
cd pg-memory-webui
python3 app/main.py
```

Access at: http://localhost:8080

Features:
- Real-time statistics
- Search interface
- Backup management
- Observation browser

---

## API Reference

### PostgresMemory Class

#### `start_session(session_key, **kwargs)`
Start a new conversation session.

**Parameters:**
- `session_key` (str): Unique session identifier
- `provider` (str): Chat provider (discord, telegram, etc.)
- `channel_id` (str): Channel identifier
- `user_id` (str): User identifier

**Returns:** `str` - Session ID

---

#### `capture_observation(session_id, content, **kwargs)`
Save an observation to memory.

**Parameters:**
- `session_id` (str): Session identifier
- `content` (str): Observation content
- `tags` (List[str]): Tags for categorization
- `importance_score` (float): 0.0-1.0 importance
- `source` (str): Source type

**Returns:** `str` - Observation ID

---

#### `search_observations(query, **kwargs)`
Search observations with semantic search.

**Parameters:**
- `query` (str): Search query
- `limit` (int): Max results (default: 10)
- `session_id` (str): Filter by session
- `tags` (List[str]): Filter by tags
- `days` (int): Time range

**Returns:** `List[Dict]` - Matching observations

---

#### `generate_summary(**kwargs)`
Generate a summary of observations.

**Parameters:**
- `tags` (List[str]): Filter by tags
- `from_date` (datetime): Start date
- `to_date` (datetime): End date
- `min_importance` (float): Minimum importance

**Returns:** `int` - Summary ID

---

#### `get_stats()`
Get database statistics.

**Returns:** `Dict` - Statistics including:
- Total observations
- Session count
- Database size
- Cache hit rate

---

## Troubleshooting

### Database Connection Failed

**Error:** `Connection refused`

**Solution:**
```bash
# Check PostgreSQL status
brew services list | grep postgres

# Restart PostgreSQL
brew services restart postgresql@18
```

---

### Ollama Not Working

**Error:** `Ollama not found` or `Model not found`

**Solution:**
```bash
# Install Ollama
brew install ollama
brew services start ollama

# Pull model
ollama pull bge-m3:latest
```

---

### pg-memory Command Not Found

**Error:** `python3: can't open file 'pg_memory.py'`

**Solution:**
```bash
# Navigate to scripts directory
cd ~/.openclaw/workspace/skills/pg-memory/scripts

# Or add to PATH
export PATH="$HOME/.openclaw/workspace/skills/pg-memory/scripts:$PATH"
```

---

### Embedding Generation Failed

**Error:** `Failed to generate embedding`

**Solution:**
```bash
# Check Ollama is running
ollama list

# Verify model exists
ollama run bge-m3:latest "test"

# Restart Ollama
brew services restart ollama
```

---

### Hook Not Triggering

**Error:** Pre-compaction not saving

**Solution:**
1. Check hook is enabled in `openclaw.json`
2. Verify handler.js exists
3. Check OpenClaw logs: `tail -f ~/.openclaw/workspace/logs/openclaw.log`

---

## Maintenance

### Daily (Automated)

- ✅ Backups at 3:00 AM
- ✅ Old backup cleanup (>7 days)
- ✅ Log rotation

### Weekly (Manual)

```bash
# Check backups
ls -lh ~/.openclaw/workspace/backups/

# View logs
tail -f ~/.openclaw/workspace/logs/*.log

# Check disk space
df -h ~/.openclaw/workspace/
```

### Monthly (Manual)

```bash
# Update pg-memory
cd ~/openclaw-pg-memory
git pull origin main

# Update dependencies
pip3 install --upgrade psycopg2-binary
pip3 install --upgrade git+https://github.com/pottertech/python_xid.git

# Restart services
brew services restart postgresql@18
brew services restart ollama
openclaw gateway restart
```

---

## Support

- 📖 **Documentation:** This directory
- 🐛 **Issues:** https://github.com/pottertech/openclaw-pg-memory/issues
- 💬 **Discord:** https://discord.gg/clawd

---

*pg-memory v3.1.0 - Production Ready*
