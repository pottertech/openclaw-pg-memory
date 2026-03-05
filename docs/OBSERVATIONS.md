# Observations Reference Guide

**Complete list of tracked observation types and statuses in pg-memory v3.0.0**

---

## 📋 Observation Types (`obs_type`)

The `obs_type` field categorizes what kind of observation this is:

| Type | Description | Use Case |
|------|-------------|----------|
| **`note`** | General note or fact | Default type for most observations |
| **`decision`** | Important decision made | Track choices and rationale |
| **`task`** | Action item or todo | Things that need to be done |
| **`insight`** | Key realization or learning | Important discoveries |
| **`question`** | Unanswered question | Things to follow up on |
| **`fact`** | Verified information | Reference data |
| **`idea`** | Concept or suggestion | Brainstorming items |
| **`issue`** | Problem or bug | Things that need fixing |
| **`meeting`** | Meeting notes | Conversation summaries |
| **`project`** | Project information | Project-level context |

**Default:** `note`

---

## 🎯 Observation Statuses (`status`)

The `status` field tracks the lifecycle of an observation:

| Status | Description | When to Use |
|--------|-------------|-------------|
| **`active`** | Currently relevant and in use | Default for new observations |
| **`ongoing`** | In progress, not yet complete | Tasks, projects, multi-step items |
| **`resolved`** | Completed or no longer relevant | Finished tasks, answered questions |
| **`superseded`** | Replaced by newer observation | When content is updated/changed |

**Default:** `active`

### Status Flow

```
active → ongoing → resolved
   ↓
superseded (when replaced)
```

---

## 🔥 Priority Levels (`priority`)

For tasks and issues, track urgency:

| Priority | Description | Example |
|----------|-------------|---------|
| **`low`** | Can wait, not urgent | Nice-to-have improvements |
| **`medium`** | Normal priority | Standard tasks |
| **`high`** | Important, time-sensitive | Deadlines approaching |
| **`critical`** | Urgent, blocking | Production issues, emergencies |

**Default:** `medium`

---

## 📊 Source Tracking (`source`)

Where did this observation come from?

| Source | Description |
|--------|-------------|
| **`manual`** | Created by user directly |
| **`auto`** | Automatically generated |
| **`compaction`** | Created during session compaction |
| **`summary`** | Generated from summary process |
| **`extraction`** | Extracted from conversation |
| **`import`** | Imported from external source |

**Default:** `manual`

---

## 🏷️ Content Types (`content_type`)

What format is the content?

| Type | Description |
|------|-------------|
| **`observation`** | Standard observation (default) |
| **`summary`** | Generated summary |
| **`checkpoint`** | Session checkpoint |
| **`decision_record`** | Formal decision documentation |
| **`meeting_notes`** | Structured meeting notes |
| **`code`** | Code snippets |
| **`reference`** | Reference material |

**Default:** `observation`

---

## 📝 Complete Field Reference

### Core Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUID | ✅ | auto | Unique identifier |
| `session_id` | UUID | ✅ | - | Parent session |
| `obs_type` | VARCHAR(50) | ✅ | `note` | Type of observation |
| `title` | VARCHAR(255) | ❌ | NULL | Short title |
| `content` | TEXT | ✅ | - | Main content |
| `status` | VARCHAR(20) | ✅ | `active` | Current status |

### Metadata Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `importance_score` | DECIMAL | ✅ | `0.5` | 0.0-1.0 importance |
| `tags` | TEXT[] | ❌ | `{}` | Categorization tags |
| `priority` | VARCHAR(20) | ✅ | `medium` | Task priority |
| `metadata` | JSONB | ❌ | `{}` | Additional data |
| `embedding` | VECTOR(1024) | ❌ | NULL | Semantic search vector |

### Temporal Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `timestamp` | TIMESTAMP | ✅ | NOW() | Creation time |
| `started_at` | TIMESTAMP | ✅ | NOW() | When started |
| `resolved_at` | TIMESTAMP | ❌ | NULL | When resolved |
| `updated_at` | TIMESTAMP | ✅ | NOW() | Last update |
| `reminder_date` | TIMESTAMP | ❌ | NULL | Follow-up date |

### Relationship Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `related_observation_ids` | UUID[] | ❌ | `{}` | Linked observations |
| `supersedes_observation_id` | UUID | ❌ | NULL | Replaces this obs |
| `derived_from_exchange_ids` | UUID[] | ❌ | `{}` | Source messages |
| `related_files` | TEXT[] | ❌ | `{}` | File references |
| `related_urls` | TEXT[] | ❌ | `{}` | URL references |

### Project Tracking

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `project_name` | VARCHAR(255) | ❌ | NULL | Associated project |
| `assigned_by` | VARCHAR(100) | ❌ | NULL | Who assigned it |
| `next_steps` | TEXT | ❌ | NULL | What to do next |

---

## 💡 Usage Examples

### Create a Task Observation

```python
mem.capture_observation(
    session_id=session_id,
    content="Fix authentication bug in API",
    obs_type="task",
    title="Fix Auth Bug",
    tags=["bug", "api", "authentication"],
    importance_score=0.9,
    priority="critical",
    status="ongoing",
    project_name="API v2",
    next_steps="Check JWT validation logic"
)
```

### Create a Decision Record

```python
mem.capture_observation(
    session_id=session_id,
    content="Decided to use PostgreSQL for production database",
    obs_type="decision",
    title="Database Selection",
    tags=["architecture", "database", "decision"],
    importance_score=1.0,
    metadata={
        "alternatives": ["MySQL", "MongoDB"],
        "rationale": "Better JSON support and pgvector"
    }
)
```

### Create an Issue

```python
mem.capture_observation(
    session_id=session_id,
    content="Users reporting slow load times on dashboard",
    obs_type="issue",
    title="Dashboard Performance",
    tags=["performance", "bug", "dashboard"],
    priority="high",
    status="active",
    assigned_by="Support Team",
    reminder_date=datetime.now() + timedelta(days=2)
)
```

### Mark as Resolved

```python
mem.update_observation(
    obs_id=observation_id,
    status="resolved",
    resolved_at=datetime.now(),
    next_steps=None
)
```

---

## 🔍 Query Examples

### Get All Active Tasks

```sql
SELECT id, title, priority, status
FROM observations
WHERE obs_type = 'task'
  AND status IN ('active', 'ongoing')
ORDER BY 
  CASE priority
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
  END;
```

### Get Unresolved Issues

```sql
SELECT id, title, priority, created_at
FROM observations
WHERE obs_type = 'issue'
  AND status != 'resolved'
ORDER BY priority DESC, created_at ASC;
```

### Get Decisions by Project

```sql
SELECT id, title, content, timestamp
FROM observations
WHERE obs_type = 'decision'
  AND project_name = 'API v2'
ORDER BY timestamp DESC;
```

### Get Items Needing Follow-up

```sql
SELECT id, title, reminder_date, status
FROM observations
WHERE reminder_date IS NOT NULL
  AND reminder_date <= NOW()
  AND status != 'resolved';
```

---

## 📊 Status Statistics

Track observation lifecycle:

```sql
SELECT 
    obs_type,
    status,
    COUNT(*) as count,
    AVG(importance_score) as avg_importance
FROM observations
GROUP BY obs_type, status
ORDER BY obs_type, status;
```

---

## 🎯 Best Practices

### 1. Use Appropriate Types

- **Notes** for general information
- **Tasks** for action items
- **Decisions** for important choices
- **Issues** for problems

### 2. Set Meaningful Importance

- `0.0-0.3`: Low importance, reference only
- `0.4-0.6`: Medium importance, useful context
- `0.7-0.9`: High importance, critical info
- `1.0`: Maximum importance, must remember

### 3. Update Status Regularly

- Mark tasks as `ongoing` when started
- Mark as `resolved` when complete
- Use `superseded` when information changes

### 4. Tag Strategically

Use consistent tags for easy retrieval:
- Project names
- Topic areas
- Priority indicators
- Team members

### 5. Link Related Observations

Use `related_observation_ids` to connect:
- Tasks to their parent projects
- Issues to their resolutions
- Decisions to their rationale

---

**pg-memory v3.0.0 - Complete Observation Tracking**
