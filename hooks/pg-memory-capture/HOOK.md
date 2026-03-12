---
name: pg-memory-capture
description: "Capture memory to PostgreSQL before compaction, restore from stored memory after"
homepage: https://github.com/pottertech/openclaw-pg-memory
metadata:
  {
    "openclaw":
      {
        "emoji": "🧠",
        "events": ["compaction:start", "compaction:end"],
        "requires": { 
          "bins": ["python3"],
          "config": ["workspace.dir"]
        },
        "install": [{ 
          "id": "pg-memory", 
          "kind": "git", 
          "url": "https://github.com/pottertech/openclaw-pg-memory",
          "path": "scripts/memory_handler.py"
        }],
      },
  }
---

# pg-memory Capture Hook

Captures durable memory before OpenClaw compaction, restores from stored memory after.

> **Separation Notice:** This hook ONLY handles memory persistence.
> Token management and context protection are owned by openclaw-token-guardian.
> This hook does NOT decide when compaction happens, monitor tokens, or prevent overflow.

## What It Does

### Pre-Compaction (capture to durable storage):
1. Captures exchanges, observations, tool calls
2. Persists to PostgreSQL (`raw_exchanges`, `observations`, etc.)
3. Creates memory checkpoint for later restoration
4. Backs up to markdown (optional)

**Does NOT:**
- Decide when compaction happens
- Monitor token counts
- Trigger compaction
- Prevent overflow

### Post-Compaction (restore from durable storage):
1. Loads context anchors (identity, preferences)
2. Retrieves persisted memory
3. Restores working context from stored memory

**Does NOT:**
- Decide when to restore
- Manage danger zones
- Trim or rewrite context
- Act as overflow controller

## Configuration

```yaml
# ~/.openclaw/workspace/config/memory.yaml
memory:
  primary_backend: "postgresql"
  markdown_backup: true
  retention_days: 7
  agent_id: "arty"

postgresql:
  host: "localhost"
  database: "openclaw_memory"
  user: "openclaw"
```

## Requirements

- PostgreSQL 18+ with pgvector
- Python 3.10+
- openclaw-pg-memory installed
- openclaw-token-guardian (for token management)

## Ownership

| Responsibility | Owner |
|----------------|-------|
| Memory capture to PostgreSQL | ✅ pg-memory |
| Memory restoration from PostgreSQL | ✅ pg-memory |
| Token threshold monitoring | 🔒 token-guardian |
| Compaction decision | 🔒 token-guardian |
| Context trimming | 🔒 token-guardian |
| Overflow prevention | 🔒 token-guardian |
