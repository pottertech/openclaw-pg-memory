# Agent Configuration for pg-memory Users

## Context Protection (v3.1.1+)

⚠️ **Important:** If pg-memory was installed before 2026-03-09, re-run `./install.sh` to get context overflow protection.

Your workspace now includes automatic protection:

| File | Purpose | Check Frequency |
|------|---------|-----------------|
| `memory/context-guardian.sh` | Detect bloat before it causes issues | Hourly (cron) |
| `memory/compaction-cron.sh` | Archive old daily notes automatically | Weekly (cron) |
| `memory/working-buffer.md` | Survives context truncation | Every session |

### Session Start Protocol

```markdown
1. Check working-buffer.md — if >100 lines, extract to SESSION-STATE.md
2. Load SESSION-STATE.md (active task context)
3. Load SOUL.md + USER.md (identity)
4. SKIP MEMORY.md unless specifically needed
5. Load only today + yesterday daily notes
```

### Danger Zone (>60% context)

```markdown
STOP — Do not respond yet
LOG — Append to working-buffer.md:
  ## [timestamp] Human
  [message summary]
  
  ## [timestamp] Agent
  [response summary + key details]
THEN — Respond
```

### After Compaction

1. Read working-buffer.md FIRST
2. Extract important context to SESSION-STATE.md
3. Clear working-buffer.md
4. Continue session

---

*Auto-installed with pg-memory v3.1.1+*