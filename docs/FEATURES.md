# pg-memory Features Reference

**Version:** 3.0.0  
**Last Updated:** 2026-03-04  
**Repository:** https://github.com/skipppotter/pg-memory

---

## Overview

pg-memory is a PostgreSQL-based structured memory system designed for OpenClaw agents. It provides persistent, searchable, and organized memory storage with advanced features for multi-agent deployments, semantic search, and session continuity.

---

## Core Features

### 1. Persistent Observation Storage

**Description:** Store structured observations (memories) with metadata including tags, importance scores, timestamps, and session context.

**Capabilities:**
- Unlimited observation storage (PostgreSQL-backed)
- Automatic timestamping (created_at, updated_at)
- Importance scoring (0.0–1.0) for prioritization
- Tag-based organization (multi-tag support)
- Session isolation (observations tied to specific sessions)
- JSON metadata field for custom data

**Example:**
```python
from pg_memory import capture

obs_id = capture(
    content="User prefers concise responses",
    tags=["preference", "communication"],
    importance=0.8,
    metadata={"context": "feedback_session"}
)
```

**CLI:**
```bash
pg-memory-cli capture "Important decision" --tags decision,project --importance 0.9
```

---

### 2. Semantic Search (Vector Similarity)

**Description:** Find observations by meaning, not just keywords, using AI-powered vector embeddings.

**Capabilities:**
- **Embedding Models:** BGE-M3 (1024-dim), nomic-embed-text (768-dim), OpenAI text-embedding-3-small (1536-dim)
- **Similarity Search:** Cosine similarity with configurable thresholds
- **Hybrid Search:** Combine semantic + tag filters
- **Performance:** 2-5x faster with IVFFLAT indexes (lists=10)
- **Configurable Limits:** Set max results and minimum similarity scores

**Example:**
```python
from pg_memory import search

results = search(
    query="What did the user say about email security?",
    limit=5,
    min_score=0.7,
    tags=["security"]  # Optional filter
)

for result in results:
    print(f"Score: {result['score']:.2f} - {result['content']}")
```

**CLI:**
```bash
pg-memory-cli search "email security preferences" --limit 5 --min-score 0.7
```

**Performance Stats (v3.0.0):**
- Index size: 1520 kB (50% reduction from v3.0.0)
- Search time: ~10-50ms for 1000+ observations
- Cache hit rate: Improved with time-sorted XID indexes

---

### 3. XID Session IDs (Time-Sorted Identifiers)

**Description:** Replace UUID with XID (20-character time-sorted IDs) for better performance and storage efficiency.

**Capabilities:**
- **25% Storage Reduction:** 12 bytes vs 16 bytes per ID
- **44% Shorter IDs:** 20 chars vs 36 chars (UUID)
- **Faster Writes:** Sequential IDs = less index fragmentation
- **Better Cache Utilization:** Time-sorted = better index locality
- **Faster Recent Queries:** Recent sessions clustered together
- **Automatic Migration:** `migrate_all_to_xid.py` handles 28 tables

**Example:**
```
UUID:  550e8400-e29b-41d4-a716-446655440000 (36 chars)
XID:   01ARZ3NDEKTSV4RRFFQ69G5FAV (20 chars)
```

**Benefits:**
```
Storage:        25% reduction (4 MB saved per million rows)
Index Cache:    10-20% better hit rate
Time Queries:   20-30% faster (recent data)
Write Speed:    20-30% faster INSERT/UPDATE
```

---

### 4. Multi-Agent Support

**Description:** Deploy multiple OpenClaw instances sharing one PostgreSQL database with automatic instance identification and agent labeling.

**Capabilities:**
- **Auto-Generated Instance IDs:** Unique XID per machine
- **Agent Labeling:** Human-readable names (e.g., "arty", "brodie", "maya")
- **Concurrent Access Safety:** UPSERT patterns prevent conflicts
- **Instance Statistics:** Query data by machine/agent
- **Session Isolation:** Each agent's sessions kept separate
- **Shared Knowledge Base:** All agents access same observation pool

**Configuration:**
```bash
export PG_MEMORY_INSTANCE_ID="auto"  # Auto-generate XID
export PG_MEMORY_AGENT_LABEL="arty"   # Human-readable name
```

**Query by Agent:**
```python
from pg_memory import search

# Find observations from specific agent
results = search("project update", agent="brodie")

# Find observations from specific instance
results = search("deployment", instance_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
```

**See:** `README-MULTI-INSTANCE.md` for full deployment guide.

---

### 5. Backup & Restore

**Description:** Full database backup and restore capabilities with compression and scheduling support.

**Capabilities:**
- **Compressed Backups:** gzip compression (default)
- **Uncompressed Option:** Plain SQL for manual editing
- **List Backups:** View available backups with timestamps
- **Restore Latest:** One-command restore from most recent
- **Restore Specific:** Restore from any backup file
- **Drop & Restore:** Optional drop existing data before restore
- **Python API:** Programmatic backup/restore

**CLI:**
```bash
# Create backup
pg-memory backup                          # → ~/.pg-memory/backups/
pg-memory backup --no-compress           # Uncompressed SQL

# List backups
pg-memory backup --list

# Restore
pg-memory restore --latest               # Most recent
pg-memory restore --file backup.sql.gz   # Specific file
pg-memory restore --latest --drop        # Drop first (WARNING: destroys data)
```

**Python API:**
```python
from pg_memory import backup, restore, list_backups

# Create backup
backup_path = backup(output_dir="./backups/", compress=True)

# List available backups
backups = list_backups()

# Restore
restore(backup_path, drop_existing=True)
```

**Storage:**
- Default location: `~/.pg-memory/backups/`
- Custom location: `--output-dir /path/to/backups`
- Compression ratio: ~60-70% size reduction

---

### 6. JSON Export/Import

**Description:** Machine-readable export format for migrations, backups, and data portability.

**Capabilities:**
- **Full Export:** All observations with metadata
- **Filtered Export:** By date range, tags, or importance
- **Duplicate Detection:** Skip or merge duplicates on import
- **Cross-Platform:** JSON works across different PostgreSQL versions
- **Python API:** Programmatic export/import

**CLI:**
```bash
# Export to JSON
pg-memory export --format json --output backup.json
pg-memory export --format json --since "2026-03-01" --tags project

# Import from JSON
pg-memory import --format json --file backup.json
pg-memory import --format json --file backup.json --skip-duplicates
```

**Python API:**
```python
from pg_memory import export_json, import_json

# Export
export_json("backup.json", since=datetime(2026, 3, 1), tags=["project"])

# Import with duplicate detection
import_json("backup.json", skip_duplicates=True)
```

---

### 7. Duplicate Detection

**Description:** Automatically detect similar observations before inserting to prevent memory bloat.

**Capabilities:**
- **Similarity Threshold:** Configurable (0.0–1.0, default 0.85)
- **Semantic Matching:** Uses vector embeddings, not exact text match
- **Auto-Skip:** Automatically skip duplicates
- **Manual Review:** Option to review before skipping
- **CLI & API:** Available in both interfaces

**Python API:**
```python
from pg_memory import capture

obs_id = capture(
    content="New observation",
    check_duplicates=True,        # Enable duplicate check
    duplicate_threshold=0.85      # 0.0-1.0 similarity threshold
)
```

**CLI:**
```bash
# Check for duplicates
pg-memory duplicate "Content to check" --threshold 0.85

# Capture with duplicate check
pg-memory-cli capture "New memory" --check-duplicates --threshold 0.9
```

---

### 8. Tag Autocomplete & Suggestions

**Description:** Intelligent tag suggestions based on content analysis and existing tag usage.

**Capabilities:**
- **Content-Based Suggestions:** Analyze observation content for relevant tags
- **Existing Tag Autocomplete:** Suggest from previously used tags
- **Partial Match:** Find tags by partial string
- **Limit Results:** Configurable number of suggestions
- **CLI & API:** Both interfaces supported

**Python API:**
```python
from pg_memory import suggest_tags, suggest_tags_from_existing

# Suggest tags based on content
tags = suggest_tags("Netflix streaming merger with competitor")
# Returns: ['streaming', 'merger', 'netflix', 'business']

# Autocomplete from existing tags
tags = suggest_tags_from_existing("pro")
# Returns: ['project', 'protocol', 'production']
```

**CLI:**
```bash
# Suggest from content
pg-memory tags --content "AI and streaming" --limit 5

# Autocomplete existing tags
pg-memory tags --partial "stre"              # Returns: streaming, structure, etc.
```

---

### 9. Related Observations

**Description:** Link observations to each other bidirectionally for building knowledge graphs and tracking related concepts.

**Capabilities:**
- **Bidirectional Links:** A→B automatically creates B→A
- **Link by Tags:** Auto-link observations with shared tags
- **Link by Content:** Semantic similarity-based linking
- **Manual Links:** Explicitly link specific observations
- **Query Relations:** Find all related observations

**Python API:**
```python
from pg_memory import link_observations, get_related

# Link two observations
link_observations(obs_id_1, obs_id_2, relation_type="related_to")

# Get all related observations
related = get_related(obs_id, relation_type="related_to")
```

**CLI:**
```bash
# Link observations
pg-memory link <obs_id_1> <obs_id_2> --type related_to

# Find related
pg-memory related <obs_id> --type related_to
```

---

### 10. Observation Chains

**Description:** Track projects, workflows, or multi-step processes as linked sequences of observations.

**Capabilities:**
- **Create Chains:** Named chains for projects/workflows
- **Add Steps:** Link observations in sequence
- **Finish Chains:** Mark chains as complete
- **List Chains:** View all active/completed chains
- **Chain Metadata:** Track start/end times, status

**CLI:**
```bash
# List all chains
pg-memory chains

# Create new chain
pg-memory new-chain "Video Production Project"

# Add step to chain
pg-memory add-step <chain_id> -o <obs_id>

# Finish chain
pg-memory finish-chain <chain_id>
```

**Python API:**
```python
from pg_memory import create_chain, add_step, finish_chain

chain_id = create_chain("Video Project", chain_type="project")
add_step(chain_id, observation_id=obs_1_id)
add_step(chain_id, observation_id=obs_2_id)
finish_chain(chain_id)
```

---

### 11. Templates

**Description:** Pre-built structures for common observation types (bug reports, decisions, project kickoffs, etc.).

**Capabilities:**
- **Built-in Templates:** Bug Report, Decision Record, Project Kickoff, Milestone
- **Custom Templates:** Create your own template structures
- **Required Fields:** Enforce required fields per template
- **Validation:** Validate field types and formats
- **CLI & API:** Both interfaces supported

**Built-in Templates:**

**Bug Report:**
- brief_description (required)
- detailed_description
- steps_to_reproduce
- expected_behavior
- actual_behavior
- severity (low/medium/high/critical)

**Decision Record:**
- decision (required)
- context
- alternatives_considered
- consequences
- date (auto)

**Project Kickoff:**
- project_name (required)
- objectives
- stakeholders
- timeline
- success_criteria

**CLI:**
```bash
# Use template
pg-memory template "Bug Report" \
  --field brief_description="Audio sync issue" \
  --field severity="high"
```

**Python API:**
```python
from pg_memory import use_template

obs_id = use_template("Bug Report", {
    "brief_description": "Audio sync issue",
    "detailed_description": "Video and audio out of sync by 2 seconds",
    "severity": "high"
})
```

---

### 12. Summaries

**Description:** Auto-generate summary observations from recent observations (preserves originals).

**Capabilities:**
- **Time-Based Summaries:** Summarize last N days
- **Tag-Based Summaries:** Summarize observations with specific tags
- **Custom Prompts:** Provide custom summary instructions
- **Original Preservation:** Summaries are additional, originals kept
- **Search Summaries:** Search only summary observations

**Python API:**
```python
from pg_memory import summarize, search_summaries

# Generate summary
summary_id = summarize(
    tags=["project"],
    days=7,
    prompt="Summarize key project decisions"
)

# Search only summaries
results = search_summaries("video project")
```

**CLI:**
```bash
# Generate summary
pg-memory summarize --tags project --days 7

# Search summaries
pg-memory search-summaries "project status"
```

---

### 13. Conflict Detection

**Description:** Find potentially contradictory observations to identify inconsistencies or evolving decisions.

**Capabilities:**
- **Semantic Contradiction:** Detect opposing statements
- **Tag-Based Conflicts:** Find conflicts within specific topics
- **Confidence Scoring:** Rate conflict severity
- **Manual Review:** Review flagged conflicts before action

**Python API:**
```python
from pg_memory import detect_conflicts

conflicts = detect_conflicts(
    observation_id=obs_id,
    min_confidence=0.7
)

for conflict in conflicts:
    print(f"Conflict score: {conflict['score']:.2f}")
    print(f"  Original: {conflict['original']}")
    print(f"  Conflicting: {conflict['conflicting']}")
```

**CLI:**
```bash
pg-memory conflicts <obs_id> --min-confidence 0.7
```

---

### 14. Natural Language Queries (Optional)

**Description:** Ask questions in plain English — no SQL required! Powered by Ollama.

**Capabilities:**
- **Plain English:** Ask questions naturally
- **SQL Generation:** AI converts to SQL queries
- **Multiple Models:** Support for Mistral, Qwen2.5-Coder, Gemma2
- **Optional Feature:** Core pg-memory works without Ollama

**Recommended Models:**

| Model | Size | Best For |
|-------|------|----------|
| `mistral:latest` | ~4GB | General NL to SQL |
| `qwen2.5-coder:latest` | ~8GB | Complex SQL generation |
| `gemma2:9b` | ~5GB | Fast queries |

**CLI:**
```bash
# Install models
ollama pull mistral
ollama pull qwen2.5-coder

# Ask questions
pg-memory query "show me high-importance projects from this week"
pg-memory query "find observations tagged with docker"
pg-memory ask "what was I working on yesterday"
```

**Python API:**
```python
from pg_memory import ask

result = ask("What are the critical observations from last week?")
print(result)
```

**Note:** Requires Ollama: `brew install ollama && ollama serve`

---

### 15. Status Management

**Description:** Track and update the status of observations (e.g., pending, in-progress, resolved, completed).

**Capabilities:**
- **Status Values:** pending, in-progress, resolved, completed, archived
- **Status History:** Track status changes over time
- **Notes:** Add notes to status updates
- **Filter by Status:** Query observations by status
- **Bulk Updates:** Update status for multiple observations

**Python API:**
```python
from pg_memory import update_status, complete_project

# Update status
update_status(obs_id, "resolved", notes="Video uploaded to YouTube")

# Complete project
complete_project("warner-bros", notes="All deliverables complete")
```

**CLI:**
```bash
pg-memory status <obs_id> resolved --notes "Fixed and deployed"
```

---

### 16. Follow-up Reminders

**Description:** Schedule follow-up reminders for observations that need future attention.

**Capabilities:**
- **Schedule Reminders:** Set future dates for follow-up
- **Reminder Queries:** Find observations due for follow-up
- **Overdue Tracking:** Identify overdue follow-ups
- **Completion Tracking:** Mark follow-ups as complete

**Python API:**
```python
from pg_memory import schedule_followup, get_due_followups

# Schedule follow-up
schedule_followup(obs_id, followup_date="2026-03-10", notes="Check progress")

# Get due follow-ups
due = get_due_followups(before=datetime.now())
```

**CLI:**
```bash
pg-memory followup <obs_id> --date 2026-03-10 --notes "Review progress"
pg-memory followups --due
```

---

### 17. Bulk Markdown Import

**Description:** Import existing markdown notes and documents into pg-memory.

**Capabilities:**
- **Recursive Import:** Import entire directory trees
- **Metadata Extraction:** Parse frontmatter for tags/importance
- **Batch Processing:** Import hundreds of files at once
- **Progress Tracking:** See import progress in real-time

**CLI:**
```bash
# Import directory recursively
pg-memory import ~/memory/ --recursive

# Import single file with metadata
pg-memory import ./note.md --importance 0.9 --tags imported,notes
```

**Python API:**
```python
from pg_memory import import_markdown

import_markdown(
    path="~/memory/",
    recursive=True,
    default_importance=0.7
)
```

---

### 18. Performance Optimizations

**Description:** Built-in performance features for speed and storage efficiency.

**Capabilities:**
- **IVFFLAT Indexes:** Optimized for vector similarity search (lists=10)
- **Connection Pooling:** Reuse database connections
- **Query Caching:** Cache frequent queries
- **Input Validation:** Prevent invalid data entry
- **Rate Limiting:** Protect against abuse
- **VACUUM Scripts:** Automated maintenance

**Performance Stats (v3.0.0):**
```
Storage:        50% reduction total (3056 kB → 1520 kB)
Write Speed:    20-30% faster INSERT/UPDATE
Search Speed:   2-5x faster semantic search
Index Cache:    10-20% better hit rate
```

**Maintenance Script:**
```bash
# Run optimization
psql pg_memory -f scripts/optimize_performance.sql

# This runs:
# - VACUUM ANALYZE on all tables
# - Reindex if needed
# - Update statistics
```

---

### 19. OpenClaw Integration

**Description:** Native integration with OpenClaw agent framework via skills and tools.

**Capabilities:**
- **memory_search Tool:** Semantic search from OpenClaw
- **memory_get Tool:** Safe snippet retrieval with citations
- **Automatic Loading:** Load memories before responses
- **Session Continuity:** Memories persist across restarts
- **Compaction Hooks:** Integrate with OpenClaw compaction

**OpenClaw Usage:**
```python
# In OpenClaw agent (automatic via skill)

# Before answering
results = memory_search(query="user preferences", maxResults=5)

# Cite sources
for result in results:
    print(f"Source: {result['path']}#{result['line']}")
```

**See:** `INTEGRATION.md` or `INTEGRATION-GUIDE.md` for complete setup instructions.

---

### 20. Migration Tools

**Description:** Tools for migrating from other memory systems or upgrading pg-memory versions.

**Capabilities:**
- **UUID to XID Migration:** Automated schema migration (28 tables)
- **Embedding Regeneration:** Regenerate embeddings with new models
- **Markdown Import:** Import from markdown-only systems
- **JSON Import:** Import from JSON-based systems
- **Cross-Version Migration:** Upgrade between pg-memory versions

**Migration Scripts:**

**UUID to XID (v3.0.0+):**
```bash
python scripts/migrate_all_to_xid.py
```

**Embedding Regeneration (v3.0.0):**
```bash
python scripts/regenerate_embeddings.py --model bge-m3:latest
```

**Schema Migration:**
```bash
psql pg_memory -f scripts/schema_v2_7_1_embedding_fix.sql
```

---

## Feature Comparison Table

| Feature | CLI | Python API | OpenClaw Tool | Notes |
|---------|-----|------------|---------------|-------|
| Observation Storage | ✅ | ✅ | ✅ | Core feature |
| Semantic Search | ✅ | ✅ | ✅ | Vector similarity |
| XID Session IDs | ✅ | ✅ | ✅ | 25% storage savings |
| Multi-Agent Support | ✅ | ✅ | ✅ | Instance isolation |
| Backup & Restore | ✅ | ✅ | ❌ | Compression support |
| JSON Export/Import | ✅ | ✅ | ❌ | Migration support |
| Duplicate Detection | ✅ | ✅ | ❌ | Configurable threshold |
| Tag Autocomplete | ✅ | ✅ | ❌ | Content-based |
| Related Observations | ✅ | ✅ | ❌ | Bidirectional links |
| Observation Chains | ✅ | ✅ | ❌ | Project tracking |
| Templates | ✅ | ✅ | ❌ | Built-in + custom |
| Summaries | ✅ | ✅ | ❌ | Auto-generated |
| Conflict Detection | ✅ | ✅ | ❌ | Semantic analysis |
| Natural Language Queries | ✅ | ✅ | ❌ | Requires Ollama |
| Status Management | ✅ | ✅ | ❌ | Workflow tracking |
| Follow-up Reminders | ✅ | ✅ | ❌ | Schedule tracking |
| Bulk Markdown Import | ✅ | ✅ | ❌ | Recursive support |
| Performance Optimizations | ✅ | ✅ | ✅ | Automatic |
| Migration Tools | ✅ | ✅ | ❌ | Version upgrades |

---

## Requirements by Feature

| Feature | Required | Optional | Notes |
|---------|----------|----------|-------|
| Core Storage | PostgreSQL 16+, Python 3.10+ | — | Base requirement |
| Semantic Search | pgvector 0.8.1+, Ollama | — | BGE-M3 model |
| Natural Language Queries | Ollama | Mistral/Qwen2.5 model | Optional feature |
| Multi-Agent | PostgreSQL | — | Single database |
| Backup/Restore | pg_dump, gzip | — | Standard tools |

---

## Performance Benchmarks (v3.0.0)

**Test Environment:**
- PostgreSQL 16.12
- 1000 observations
- BGE-M3 embeddings (1024-dim)
- MacBook Pro M1

| Operation | Time | Notes |
|-----------|------|-------|
| INSERT observation | ~5ms | With embedding generation |
| Semantic search (top 5) | ~15ms | IVFFLAT lists=10 |
| Tag filter search | ~3ms | Indexed query |
| Backup (1000 obs) | ~500ms | Compressed |
| Restore (1000 obs) | ~800ms | From compressed backup |
| XID migration (28 tables) | ~2s | One-time operation |

---

## Support & Documentation

- **GitHub:** https://github.com/skipppotter/pg-memory
- **Integration Guide:** `docs/INTEGRATION.md`
- **Multi-Instance:** `README-MULTI-INSTANCE.md`
- **Migration:** `MIGRATION.md`
- **Skill Docs:** `SKILL.md`
- **Examples:** `examples/`

---

*Part of Proactive Agent v3.0 🦞*
