---
name: pg-memory-compaction
description: "Save session to PostgreSQL before compaction, restore context after"
homepage: https://github.com/pottertech/pg-memory
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
          "url": "https://github.com/pottertech/pg-memory",
          "path": "scripts/memory_handler.py"
        }],
      },
  }
---

# pg-memory Compaction Hook

Integrates pg-memory v2.7.6+ with OpenClaw's compaction system.

## What It Does

### Pre-Compaction (before context reset):
1. Captures all exchanges, tool calls, observations
2. Saves to PostgreSQL `raw_exchanges`, `tool_executions`, `observations`
3. Creates intelligent context checkpoint
4. Backs up to markdown (optional)

### Post-Compaction (after context reset):
1. Loads context anchors (identity, preferences, critical config)
2. Retrieves working memory cache (priority-ordered)
3. Assembles full context within token budget
4. Logs context state for monitoring

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
  user: "skipppotter"

context:
  budget_tokens: 4000
  always_load:
    - agent_identity: true
    - user_preferences: true
```

## Requirements

- PostgreSQL 18+ with pgvector
- Python 3.10+
- pg-memory installed: `git clone https://github.com/pottertech/pg-memory`

