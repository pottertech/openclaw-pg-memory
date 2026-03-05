# pg-memory + OpenClaw Integration Guide v3.1.0

**Production-Ready Memory Integration**

---

## Quick Start (5 Minutes)

```bash
# 1. Clone pg-memory
cd ~/.openclaw/workspace/repos
git clone https://github.com/pottertech/openclaw-pg-memory.git
cd openclaw-pg-memory

# 2. Run installer
./install.sh

# 3. Restart OpenClaw
openclaw gateway restart
```

---

## What You Get

✅ **Persistent Memory** - All conversations saved to PostgreSQL  
✅ **Semantic Search** - Find memories by meaning, not keywords  
✅ **Context Restoration** - Auto-restore context after compaction  
✅ **Multi-Instance Safe** - Multiple agents share one database  
✅ **XID Performance** - 25% storage savings, time-sorted IDs  
✅ **Automated Backups** - Daily PostgreSQL dumps  

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Agent Session (Arty)                   │ │
│  │  ┌──────────────┐    ┌─────────────────────────┐   │ │
│  │  │ Conversation │───▶│  pg-memory Integration  │   │ │
│  │  │   Context    │    │  (memory_handler.py)    │   │ │
│  │  └──────────────┘    └───────────┬─────────────┘   │ │
│  └──────────────────────────────────┼─────────────────┘ │
└─────────────────────────────────────┼───────────────────┘
                                      │
                                      ▼
                          ┌───────────────────────┐
                          │   PostgreSQL 18       │
                          │   openclaw_memory     │
                          │                       │
                          │  - sessions           │
                          │  - observations       │
                          │  - raw_exchanges      │
                          │  - context_checkpoints│
                          │  - decision_log       │
                          │  - summaries          │
                          └───────────────────────┘
```

---

## How Memory Recall Works

### **Before Integration (File-Based)**

```
User: "What did I do yesterday?"
  ↓
OpenClaw: Reads memory/YYYY-MM-DD.md files
  ↓
Response: Text from markdown files
```

**Limitations:**
- ❌ No semantic search
- ❌ No vector embeddings
- ❌ Manual file management
- ❌ No multi-agent support

---

### **After Integration (pg-memory)**

```
User: "What did I do yesterday?"
  ↓
OpenClaw: Calls memory_search(query="yesterday activities")
  ↓
pg-memory: Queries PostgreSQL with vector similarity
  ↓
Response: Ranked observations with scores + citations
```

**Benefits:**
- ✅ Semantic search (find by meaning)
- ✅ Vector embeddings (BGE-M3, 1024-dim)
- ✅ Automatic persistence
- ✅ Multi-agent safe
- ✅ Time-sorted XID indexes

---

## Step-by-Step Integration

### Step 1: Install pg-memory

```bash
cd ~/.openclaw/workspace/repos
git clone https://github.com/pottertech/openclaw-pg-memory.git
cd openclaw-pg-memory
./install.sh
```

**What the installer does:**
1. ✅ Installs PostgreSQL 18 + pgvector
2. ✅ Installs Ollama + BGE-M3 model
3. ✅ Creates database `openclaw_memory`
4. ✅ Initializes schema with XID support
5. ✅ Installs Python dependencies
6. ✅ Configures environment variables

---

### Step 2: Configure OpenClaw

Edit `~/.openclaw/openclaw.json`:

```json
{
  "env": {
    "OPENCLAW_NAME": "arty",
    "OPENCLAW_INSTANCE_ID": "auto",
    "PG_MEMORY_DB": "openclaw_memory",
    "PG_MEMORY_USER": "openclaw",
    "PG_MEMORY_HOST": "localhost",
    "PG_MEMORY_DEBUG": "1"
  },
  "hooks": {
    "internal": {
      "enabled": true,
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

**Generate unique instance ID:**
```bash
uuidgen
# Use output as OPENCLAW_INSTANCE_ID (or use "auto" for auto-generation)
```

---

### Step 3: Enable Memory Recall Tools

OpenClaw's built-in `memory_search` and `memory_get` tools need to be configured to use pg-memory instead of markdown files.

**Create `~/.openclaw/workspace/config/memory.yaml`:**

```yaml
memory:
  primary_backend: "postgresql"  # Use pg-memory instead of markdown
  markdown_backup: true          # Also write to markdown as backup
  retention_days: 30
  agent_id: "arty"
  fallback_on_pgdb_down: true    # Use markdown if DB is down

postgresql:
  host: "localhost"
  port: 5432
  database: "openclaw_memory"
  user: "openclaw"

context:
  budget_tokens: 4000
  always_load:
    - agent_identity: true
    - user_preferences: true
    - critical_config: true
  priority_order:
    - "critical"
    - "high"
    - "medium"
    - "low"

compaction:
  pre_compaction_enabled: true
  post_compaction_enabled: true
  hook_script: "~/.openclaw/workspace/skills/pg-memory/scripts/memory_handler.py"
```

---

### Step 4: Update memory_search Tool

The `memory_search` tool needs to query pg-memory instead of markdown files.

**Create `~/.openclaw/workspace/skills/pg-memory/scripts/openclaw_integration.py`:**

```python
#!/usr/bin/env python3
"""
pg-memory Integration for OpenClaw Tools

Replaces markdown-based memory_search with PostgreSQL-backed semantic search.
"""

from pg_memory import PostgresMemory
from datetime import datetime, timedelta
import json

def memory_search(query: str, maxResults: int = 5, minScore: float = 0.5):
    """
    Search pg-memory observations with semantic search.
    
    This replaces the default markdown-based memory_search.
    
    Args:
        query: Search query (semantic, not keyword)
        maxResults: Maximum results to return
        minScore: Minimum similarity score (0.0-1.0)
    
    Returns:
        List of observations with scores and citations
    """
    mem = PostgresMemory()
    
    try:
        # Search observations
        results = mem.search_observations(
            query=query,
            limit=maxResults,
            min_score=minScore
        )
        
        # Format for OpenClaw
        formatted = []
        for obs in results:
            formatted.append({
                'id': obs['id'],
                'content': obs['content'],
                'score': obs['score'],
                'timestamp': obs['timestamp'],
                'tags': obs.get('tags', []),
                'path': f"pg-memory:observations#{obs['id']}",  # Citation format
                'lines': 1  # Single observation
            })
        
        return formatted
    
    finally:
        mem.close()


def memory_get(path: str, from_line: int = None, lines: int = None):
    """
    Get specific observation from pg-memory.
    
    Args:
        path: Observation path (pg-memory:observations#<id>)
        from_line: Ignored (single observation)
        lines: Ignored (single observation)
    
    Returns:
        Observation content
    """
    if not path.startswith('pg-memory:'):
        return None
    
    # Extract observation ID
    obs_id = path.split('#')[-1] if '#' in path else None
    
    if not obs_id:
        return None
    
    mem = PostgresMemory()
    
    try:
        # Get observation by ID
        obs = mem.get_observation(obs_id)
        
        if obs:
            return {
                'content': obs['content'],
                'metadata': obs,
                'path': path
            }
        return None
    
    finally:
        mem.close()


def capture_observation(content: str, tags: list = None, importance: float = 0.5):
    """
    Capture an observation to pg-memory.
    
    Args:
        content: Observation content
        tags: List of tags
        importance: Importance score (0.0-1.0)
    
    Returns:
        Observation ID
    """
    mem = PostgresMemory()
    
    try:
        # Get current session
        session_id = mem.get_or_create_session(
            session_key='current',
            provider='openclaw'
        )
        
        # Capture observation
        obs_id = mem.capture_observation(
            session_id=session_id,
            content=content,
            tags=tags or [],
            importance_score=importance
        )
        
        return obs_id
    
    finally:
        mem.close()


# Test function
if __name__ == '__main__':
    print("Testing pg-memory integration...")
    
    # Test search
    results = memory_search("pg-memory installation", maxResults=3)
    print(f"Found {len(results)} observations")
    
    for obs in results:
        print(f"  Score: {obs['score']:.2f} - {obs['content'][:50]}...")
        print(f"  Citation: {obs['path']}")
```

---

### Step 5: Hook Into OpenClaw's Tool System

OpenClaw needs to use pg-memory instead of markdown for memory operations.

**Option A: Override Default Tools (Recommended)**

Create `~/.openclaw/workspace/config/tools.json`:

```json
{
  "overrides": {
    "memory_search": {
      "script": "~/.openclaw/workspace/skills/pg-memory/scripts/openclaw_integration.py",
      "function": "memory_search"
    },
    "memory_get": {
      "script": "~/.openclaw/workspace/skills/pg-memory/scripts/openclaw_integration.py",
      "function": "memory_get"
    }
  }
}
```

**Option B: Modify OpenClaw's Tool Registry**

Edit `~/.openclaw/openclaw.json`:

```json
{
  "tools": {
    "custom": {
      "memory_search": {
        "path": "./skills/pg-memory/scripts/openclaw_integration.py",
        "handler": "memory_search"
      },
      "memory_get": {
        "path": "./skills/pg-memory/scripts/openclaw_integration.py",
        "handler": "memory_get"
      }
    }
  }
}
```

---

### Step 6: Restart OpenClaw

```bash
openclaw gateway restart
```

Wait 10 seconds for full restart.

---

### Step 7: Verify Integration

**Test 1: Check pg-memory is working**

```bash
cd ~/.openclaw/workspace/repos/openclaw-pg-memory/scripts
python3 << 'EOF'
from pg_memory import PostgresMemory

mem = PostgresMemory()
print(f"✅ Database: {mem.db_name}")
print(f"✅ Instance: {mem.instance_id[:8]}...")
print(f"✅ Agent: {mem.agent_label}")

# Create test observation
session_id = mem.start_session('integration-test', provider='discord')
obs_id = mem.capture_observation(
    session_id=session_id,
    content="Integration test observation",
    tags=['test', 'integration'],
    importance_score=0.9
)
print(f"✅ Created observation: {obs_id}")

# Search for it
results = mem.search_observations("integration test", limit=5)
print(f"✅ Search found: {len(results)} results")

mem.close()
print("✅ pg-memory working!")
EOF
```

**Test 2: Test memory_search**

In OpenClaw chat, ask:
```
What is pg-memory?
```

Expected response should cite pg-memory observations, not markdown files.

**Test 3: Check citations**

Look for citations in format:
```
Source: pg-memory:observations#d6k45fr24teg1v324t40
```

Instead of:
```
Source: MEMORY.md#42
```

---

## How It Works in Practice

### **Example: User Asks About Past Work**

**User:** "What did I work on yesterday?"

**Before (markdown):**
```python
# OpenClaw reads memory/2026-03-03.md
# Returns text from file
```

**After (pg-memory):**
```python
# OpenClaw calls memory_search(query="work yesterday")
# pg-memory queries PostgreSQL:

SELECT content, score, timestamp, tags
FROM observations
WHERE embedding <=> query_embedding('work yesterday')
  AND timestamp >= NOW() - INTERVAL '2 days'
ORDER BY score DESC
LIMIT 5;

# Returns ranked observations with scores
```

**Response:**
```
Yesterday you worked on:

1. **pg-memory v2.7.3 Release** (Score: 0.92)
   - Performance optimizations
   - Dropped 7 unused indexes
   - 50% storage reduction
   Source: pg-memory:observations#d6k87bb24tekhfr24tg0

2. **Embedding Fix** (Score: 0.88)
   - Fixed dimension: 1536 → 1024
   - Regenerated 76 observations
   Source: pg-memory:observations#d6k87cd24temlcj24teg

3. **Tool Outage** (Score: 0.75)
   - 4+ hour tool failure
   - Gateway restart required
   Source: pg-memory:observations#d6k87sr24temm2b24tf0
```

---

## Migration from Markdown

If you have existing markdown memories, migrate them to pg-memory:

```bash
cd ~/.openclaw/workspace/repos/openclaw-pg-memory/scripts

# Import all markdown memories
python3 << 'EOF'
from pg_memory import PostgresMemory
from pathlib import Path
import re

mem = PostgresMemory()
session_id = mem.start_session('markdown-migration', provider='migration')

# Find all memory files
memory_dir = Path.home() / '.openclaw' / 'workspace' / 'memory'
for md_file in memory_dir.glob('*.md'):
    print(f"Importing {md_file.name}...")
    
    content = md_file.read_text()
    
    # Capture as observation
    mem.capture_observation(
        session_id=session_id,
        content=content,
        tags=['imported', 'markdown', md_file.stem],
        importance_score=0.7,
        metadata={
            'source_file': str(md_file),
            'import_date': str(datetime.now())
        }
    )

mem.close()
print("✅ Migration complete!")
EOF
```

---

## Troubleshooting

### "memory_search still uses markdown"

**Cause:** Tool override not configured

**Fix:**
1. Verify `~/.openclaw/workspace/config/tools.json` exists
2. Check OpenClaw logs: `openclaw logs | grep memory_search`
3. Restart OpenClaw: `openclaw gateway restart`

### "Database connection failed"

**Cause:** PostgreSQL not running

**Fix:**
```bash
brew services list | grep postgresql
brew services start postgresql@18
```

### "No observations found"

**Cause:** No data in pg-memory yet

**Fix:**
1. Use OpenClaw for a while (observations auto-captured)
2. Or manually capture test observation:
   ```bash
   python3 scripts/pg_memory.py --capture "Test observation" --tags test
   ```

### "Citations show markdown instead of pg-memory"

**Cause:** memory_get not overridden

**Fix:** Update both `memory_search` AND `memory_get` in tools.json

---

## Advanced Usage

### Query by Date Range

```python
from pg_memory import PostgresMemory
from datetime import datetime, timedelta

mem = PostgresMemory()

# Get last 24 hours
results = mem.search_observations(
    query="work completed",
    days=1,  # Last 24 hours
    limit=10
)

mem.close()
```

### Query by Tags

```python
results = mem.search_observations(
    query="project update",
    tags=['project', 'critical'],
    limit=5
)
```

### Get Observation by ID

```python
obs = mem.get_observation('d6k45fr24teg1v324t40')
print(obs['content'])
print(obs['tags'])
print(obs['timestamp'])
```

### Generate Summary

```python
summary_id = mem.generate_summary(
    tags=['project'],
    days=7,
    prompt="Summarize key project decisions"
)
```

---

## Performance Tips

### 1. Index Optimization

```sql
-- Optimize for semantic search
psql -d openclaw_memory -c "
  CREATE INDEX IF NOT EXISTS idx_observations_embedding 
  ON observations 
  USING ivfflat (embedding vector_cosine_ops) 
  WITH (lists = 10);
"
```

### 2. Regular Maintenance

```bash
# Weekly VACUUM
psql -d openclaw_memory -c "VACUUM ANALYZE observations;"

# Monthly reindex
psql -d openclaw_memory -c "REINDEX INDEX idx_observations_embedding;"
```

### 3. Connection Pooling

Add to `~/.config/pg-memory/config.env`:
```bash
PG_MEMORY_POOL_SIZE=10
PG_MEMORY_MAX_OVERFLOW=20
```

---

## Support

- **GitHub:** https://github.com/pottertech/openclaw-pg-memory
- **Issues:** https://github.com/pottertech/openclaw-pg-memory/issues
- **Discord:** https://discord.gg/clawd

---

*pg-memory v3.1.0 - Production Ready*
