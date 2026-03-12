# pg-memory vs token-guardian Separation Guide

## Overview

Starting with v3.1.2, `openclaw-pg-memory` and `openclaw-token-guardian` are cleanly separated to avoid overlapping responsibilities.

---

## Ownership Matrix

| Responsibility | pg-memory | token-guardian |
|----------------|:---------:|:--------------:|
| **Durable Storage** | ✅ | ❌ |
| **Semantic Embeddings** | ✅ | ❌ |
| **Vector Retrieval** | ✅ | ❌ |
| **Context Restoration** | ✅ | ❌ |
| **Long-term Summaries** | ✅ | ❌ |
| **Memory Capture** | ✅ | ❌ |
| **Token Threshold Monitoring** | ❌ | ✅ |
| **Live Context Reduction** | ❌ | ✅ |
| **Bloat Detection** | ❌ | ✅ |
| **Workspace Cleanup** | ❌ | ✅ |
| **Emergency Pruning** | ❌ | ✅ |
| **Active Session Management** | ❌ | ✅ |

---

## pg-memory Responsibilities

### What It Does

**1. Durable Storage**
- Saves conversations to PostgreSQL
- Maintains historical record
- Survives restarts and crashes

**2. Semantic Retrieval**
- BGE-M3 embeddings via Ollama
- Vector similarity search
- Natural language queries

**3. Context Restoration**
- Post-compaction memory reload
- Identity/preferences restoration
- Working memory reconstruction

**4. Long-term Summaries**
- Project summaries
- Decision records
- Checkpoint creation

**5. Backups & Maintenance**
- Daily PostgreSQL dumps
- Archive management
- Database health checks

### What It Does NOT Do

- ❌ Real-time token monitoring
- ❌ Active context trimming
- ❌ Live bloat detection
- ❌ Emergency workspace cleanup
- ❌ Session pruning

---

## token-guardian Responsibilities

### What It Does

**1. Token Management**
- Monitors context window usage
- Triggers compaction when needed
- Enforces token budgets

**2. Live Context Reduction**
- Active transcript trimming
- Priority-based pruning
- Emergency reduction protocols

**3. Bloat Detection**
- Hourly MEMORY.md checks
- Working buffer monitoring
- Size threshold alerts

**4. Workspace Cleanup**
- File rotation and archival
- Temporary file cleanup
- Log management

### What It Does NOT Do

- ❌ Long-term storage
- ❌ Semantic search
- ❌ PostgreSQL persistence
- ❌ Memory restoration

---

## Installation

### Recommended: Install Both

```bash
# 1. pg-memory (durable storage)
git clone https://github.com/pottertech/openclaw-pg-memory.git
cd openclaw-pg-memory
./install.sh --separation-mode

# 2. token-guardian (live context)
git clone https://github.com/pottertech/openclaw-token-guardian.git
cd ../openclaw-token-guardian
./install.sh
```

### pg-memory Only (Legacy Behavior)

```bash
# NOT RECOMMENDED - overlaps with token-guardian
./install.sh --legacy-context
```

---

## Configuration

### pg-memory Config (memory.yaml)

```yaml
memory:
  # Core features (always enabled)
  enable_persistent_storage: true
  enable_embeddings: true
  enable_semantic_retrieval: true
  enable_memory_capture: true
  enable_summaries: true
  enable_context_restoration: true
  
  # SEPARATION: These are owned by token-guardian
  # DO NOT enable unless token-guardian is NOT installed
  enable_context_guardian: false      # token-guardian
  enable_compaction_cron: false        # token-guardian
  enable_token_monitoring: false      # token-guardian
  enable_auto_pruning: false          # token-guardian
  enable_emergency_reduction: false   # token-guardian
```

### token-guardian Config

See [token-guardian documentation](https://github.com/pottertech/openclaw-token-guardian)

---

## Hook Integration

### pg-memory Hook

Only handles memory persistence:

```javascript
// hooks/pg-memory-compaction/handler.js
export async function handleCompactionStart(params) {
  // Save current session to PostgreSQL
  // Does NOT make compaction decisions
}

export async function handleCompactionEnd(params) {
  // Restore context from PostgreSQL
  // Does NOT trigger compaction
}
```

### token-guardian Hook

Handles compaction decisions:

```javascript
// hooks/token-guardian/handler.js
export async function checkTokenThreshold(session) {
  // Monitor tokens
  // Trigger compaction when needed
}
```

---

## Migration from v3.1.1

If upgrading from v3.1.1 (before separation):

```bash
# 1. Update pg-memory
cd openclaw-pg-memory
git pull
./install.sh --separation-mode

# 2. Install token-guardian (if not already)
git clone https://github.com/pottertech/openclaw-token-guardian.git
cd openclaw-token-guardian
./install.sh

# 3. Remove legacy cron jobs
crontab -e
# Remove: context-guardian.sh, compaction-cron.sh

# 4. Restart OpenClaw
openclaw gateway restart
```

---

## Troubleshooting

### "No bloat detection"

```
❌ pg-memory does NOT do bloat detection
✅ Install token-guardian for this feature
```

### "Context not being reduced"

```
❌ pg-memory does NOT manage live context
✅ token-guardian handles token thresholds
```

### "Missing memory after compaction"

```
✅ pg-memory restores context after compaction
⚠️  Check: Is the compaction hook enabled?
⚠️  Check: Is PostgreSQL running?
```

---

## FAQ

**Q: Do I need both pg-memory and token-guardian?**

A: **Recommended yes.** pg-memory for durable storage, token-guardian for live context management.

**Q: Can I use pg-memory without token-guardian?**

A: **Yes, but not recommended.** Use `--legacy-context` flag, but you'll have overlapping features.

**Q: What if I install token-guardian later?**

A: **Safe.** pg-memory will auto-detect and disable overlapping features.

**Q: Does this affect existing data?**

A: **No.** Your PostgreSQL data is preserved. Only installation behavior changes.

**Q: Which repo should I report issues to?**

| Issue | Repo |
|-------|------|
| Can't find old memories | pg-memory |
| Context not restoring | pg-memory |
| Token threshold alerts | token-guardian |
| Workspace cleanup | token-guardian |
| Compaction triggered too often | token-guardian |
| Search not working | pg-memory |

---

## Version History

| Version | Separation Status |
|---------|-------------------|
| v3.1.0 | ❌ Combined |
| v3.1.1 | ⚠️ Overlapping |
| v3.1.2 | ✅ Clean separation |

---

## Support

- **pg-memory issues:** https://github.com/pottertech/openclaw-pg-memory/issues
- **token-guardian issues:** https://github.com/pottertech/openclaw-token-guardian/issues
- **Discord:** #memory-systems channel
