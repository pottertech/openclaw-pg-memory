# Automated Cron Jobs for pg-memory

**Optional automation scripts for pg-memory maintenance**

---

## 🕐 Recommended Cron Jobs

### 1. Daily Markdown Migration (Recommended)

Migrates markdown memory files to PostgreSQL every day.

**Add to crontab:**
```bash
crontab -e
```

**Add this line:**
```bash
0 3 * * * cd /path/to/openclaw-pg-memory/scripts && python3 migrate-markdown-to-pgmemory.py >> ~/.openclaw/workspace/logs/pg-memory-migration.log 2>&1
```

**Schedule:** Daily at 3:00 AM  
**Purpose:** Ensures all markdown files are migrated to PostgreSQL  
**Logs:** `~/.openclaw/workspace/logs/pg-memory-migration.log`

---

### 2. Weekly File Cleanup (Optional)

Archives old markdown files to reduce clutter.

**Add to crontab:**
```bash
0 4 * * 0 cd /path/to/openclaw-pg-memory/scripts && ./cleanup-memory-files.sh 7 >> ~/.openclaw/workspace/logs/memory-cleanup.log 2>&1
```

**Schedule:** Every Sunday at 4:00 AM  
**Purpose:** Keep only last 7 days of markdown files (archives older ones)  
**Logs:** `~/.openclaw/workspace/logs/memory-cleanup.log`

**Customize retention:**
```bash
# Keep 14 days instead
0 4 * * 0 ... ./cleanup-memory-files.sh 14

# Keep 30 days
0 4 * * 0 ... ./cleanup-memory-files.sh 30
```

---

### 3. Database Backup (Recommended)

Daily PostgreSQL backup.

**Add to crontab:**
```bash
0 2 * * * pg_dump -U openclaw openclaw_memory > ~/.openclaw/workspace/backups/pg-memory-$(date +\%Y-\%m-\%d).sql
```

**Schedule:** Daily at 2:00 AM (before migration)  
**Purpose:** Daily backup of PostgreSQL database  
**Retention:** Manually clean old backups (recommend 30 days)

**With cleanup:**
```bash
0 2 * * * pg_dump -U openclaw openclaw_memory > ~/.openclaw/workspace/backups/pg-memory-$(date +\%Y-\%m-\%d).sql && find ~/.openclaw/workspace/backups -name "pg-memory-*.sql" -mtime +30 -delete
```

---

## 📋 Complete Cron Setup

**All three jobs together:**
```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily backup at 2 AM
0 2 * * * pg_dump -U openclaw openclaw_memory > ~/.openclaw/workspace/backups/pg-memory-$(date +\%Y-\%m-\%d).sql && find ~/.openclaw/workspace/backups -name "pg-memory-*.sql" -mtime +30 -delete

# Daily migration at 3 AM
0 3 * * * cd /path/to/openclaw-pg-memory/scripts && python3 migrate-markdown-to-pgmemory.py >> ~/.openclaw/workspace/logs/pg-memory-migration.log 2>&1

# Weekly cleanup on Sunday at 4 AM
0 4 * * 0 cd /path/to/openclaw-pg-memory/scripts && ./cleanup-memory-files.sh 7 >> ~/.openclaw/workspace/logs/memory-cleanup.log 2>&1
```

**Result:**
- 2:00 AM - Database backup
- 3:00 AM - Markdown → PostgreSQL migration
- 4:00 AM (Sun) - Archive old markdown files

---

## 🔍 Monitoring

**View logs:**
```bash
# Migration logs
tail -20 ~/.openclaw/workspace/logs/pg-memory-migration.log

# Cleanup logs
tail -20 ~/.openclaw/workspace/logs/memory-cleanup.log

# Watch in real-time
tail -f ~/.openclaw/workspace/logs/pg-memory-migration.log
```

**Check crontab:**
```bash
crontab -l
```

**Test scripts manually:**
```bash
# Test migration
cd /path/to/openclaw-pg-memory/scripts
python3 migrate-markdown-to-pgmemory.py

# Test cleanup
./cleanup-memory-files.sh 7
```

---

## ⚠️ Important Notes

**1. Update Paths:**
Replace `/path/to/openclaw-pg-memory/` with your actual path:
```bash
# Usually:
~/.openclaw/workspace/repos/openclaw-pg-memory/
```

**2. Make Scripts Executable:**
```bash
chmod +x cleanup-memory-files.sh
chmod +x migrate-markdown-to-pgmemory.py
```

**3. Timezone:**
Cron uses system timezone. Verify yours:
```bash
date
```

**4. Logs Directory:**
Create logs directory if it doesn't exist:
```bash
mkdir -p ~/.openclaw/workspace/logs
```

---

## 🎯 Alternative: OpenClaw Hook

Instead of cron job #2 (migration), you can use the **pg-memory-migration hook**:

**What it does:**
- Runs when you execute `/new` or `/reset`
- Migrates markdown files immediately when session ends
- More responsive than waiting for daily cron

**Setup:**
```bash
cd ~/.openclaw/workspace
openclaw hooks install -l ./hooks/pg-memory-migration
openclaw hooks enable pg-memory-migration
openclaw gateway restart
```

**Recommendation:** Use **both** hook + cron:
- **Hook:** Primary (runs on `/new`)
- **Cron:** Backup (daily at 3 AM, catches anything missed)

---

## 📊 Example Schedule

| Time | Job | Frequency |
|------|-----|-----------|
| 2:00 AM | Database backup | Daily |
| 3:00 AM | Markdown migration | Daily |
| 4:00 AM | File cleanup | Weekly (Sunday) |

**Total runtime:** ~5-10 minutes per day  
**Impact:** Fully automated memory management

---

*pg-memory v3.1.0 - Production Ready*
