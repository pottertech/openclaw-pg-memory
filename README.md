# 🧠 OpenClaw pg-memory v3.0.0

**Production-Ready Structured Memory for OpenClaw**

> **Version:** 3.0.0 (Production Release)  
> **Status:** ✅ Stable, Ready for Production  
> **License:** MIT  
> **Author:** Potter's Quill Media

---

## 🚀 Quick Start (5 Minutes)

Get pg-memory installed and integrated with OpenClaw in under 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/pottertech/openclaw-pg-memory.git
cd openclaw-pg-memory

# 2. Run the automated installer
./install.sh

# 3. Restart OpenClaw
openclaw gateway restart

# 4. Verify installation
python3 scripts/pg_memory.py --stats
```

That's it! Your OpenClaw instance now has persistent, structured memory with vector search, automatic backups, and intelligent context management.

### Automation Options

**Option 1: OpenClaw Hook (Recommended)**
```bash
# Migrates markdown files when you run /new or /reset
openclaw hooks install -l ./hooks/pg-memory-migration
openclaw hooks enable pg-memory-migration
```

**Option 2: Daily Cron Job**
```bash
# Migrates files daily at 3 AM
crontab -e
# Add: 0 3 * * * cd /path/to/scripts && python3 migrate-markdown-to-pgmemory.py
```

**Option 3: Both (Best Coverage)**
- Hook: Primary (runs on `/new`)
- Cron: Backup (daily at 3 AM)

See [`docs/CRON-EXAMPLES.md`](docs/CRON-EXAMPLES.md) for complete automation setup.

### OpenClaw Integration

Once installed, pg-memory automatically integrates with OpenClaw:

- **memory_search** → Semantic search PostgreSQL instead of markdown files
- **memory_get** → Retrieve observations by ID with full metadata
- **Auto-capture** → All conversations saved to PostgreSQL
- **Context restoration** → Auto-restore after compaction

**Citations change from:**
```
Source: MEMORY.md#42  # Before (markdown)
```

**To:**
```
Source: pg-memory:observations#d6k45fr24teg1v324t40  # After (PostgreSQL)
```

See [`docs/INTEGRATION-OPENCLAW.md`](docs/INTEGRATION-OPENCLAW.md) for complete integration guide.

---

## 📋 What You Get

### **Core Features**

- ✅ **Persistent Memory** - Never lose conversation context again
- ✅ **Vector Search** - Semantic search across all your conversations
- ✅ **Automatic Backups** - Daily backups at 3 AM with 7-day retention
- ✅ **Context Management** - Intelligent compaction with summary generation
- ✅ **Multi-Session Support** - Share memory across multiple OpenClaw instances
- ✅ **Web Dashboard** - Visual interface at http://localhost:8080
- ✅ **CLI Tools** - Command-line access to all memory functions

### **Technical Specifications**

| Component | Version | Purpose |
|-----------|---------|---------|
| **PostgreSQL** | 18+ | Database backend |
| **pgvector** | Latest | Vector embeddings |
| **Ollama** | Latest | Local AI (BGE-M3 embeddings) |
| **Python** | 3.10+ | Runtime |
| **XID** | Latest | Time-sorted compact IDs |

---

## 📦 Installation

### **Automated Install (Recommended)**

```bash
./install.sh
```

This script will:
1. Install PostgreSQL 18 with pgvector
2. Install Ollama and pull BGE-M3 model
3. Create database and user
4. Initialize schema with all tables
5. Configure environment variables
6. Set up automated backups
7. Install pg-memory skill into OpenClaw
8. Start the web dashboard

### **Manual Install**

If you prefer manual control, see [`docs/MANUAL-INSTALL.md`](docs/MANUAL-INSTALL.md)

---

## 🔧 Configuration

### **Environment Variables**

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export PG_MEMORY_DB=openclaw_memory
export PG_MEMORY_USER=openclaw
export PG_MEMORY_HOST=localhost
export PG_MEMORY_PORT=5432
export PG_MEMORY_DEBUG=0
export OPENCLAW_INSTANCE_ID=$(uuidgen)
```

### **OpenClaw Integration**

The installer automatically configures OpenClaw. To verify:

```bash
cat ~/.openclaw/openclaw.json | grep -A5 "pg-memory"
```

Should show:
```json
"pg-memory-compaction": {
  "enabled": true,
  "path": "./hooks/pg-memory-compaction/handler.js"
}
```

---

## 📖 Usage

### **Basic Commands**

```bash
# View memory statistics
python3 scripts/pg_memory.py --stats

# Search your memory
python3 scripts/pg_memory.py --search "what did we discuss about AI?"

# Create a backup
python3 scripts/pg_memory.py --backup

# View recent observations
python3 scripts/pg_memory.py --recent 10

# Natural language query
python3 scripts/pg_memory.py --query "What decisions did I make last week?"
```

### **Web Dashboard**

Access at: http://localhost:8080

Features:
- Real-time statistics
- Search interface
- Backup management
- Observation browser

### **OpenClaw Integration**

pg-memory automatically activates when you use OpenClaw:

- **Pre-compaction:** Saves conversation context before truncation
- **Post-compaction:** Restores relevant context after reset
- **Automatic:** No manual intervention required

---

## 🗂️ Project Structure

```
openclaw-pg-memory/
├── install.sh                 # Automated installer
├── README.md                  # This file
├── docs/
│   ├── MANUAL-INSTALL.md      # Manual installation guide
│   ├── CONFIGURATION.md       # Advanced configuration
│   ├── USAGE.md               # Detailed usage guide
│   ├── TROUBLESHOOTING.md     # Common issues and fixes
│   └── API.md                 # Python API documentation
├── scripts/
│   ├── pg_memory.py           # Main Python library
│   ├── pg-memory-cli          # Command-line interface
│   ├── decode_xid.py          # XID decoder tool
│   ├── memory_handler.py      # OpenClaw integration
│   └── upgrade-schema.sql     # Schema migration (if needed)
├── hooks/
│   └── pg-memory-compaction/
│       └── handler.js         # OpenClaw compaction hook
├── sql/
│   ├── init_schema.sql        # Database schema
│   └── sample_queries.sql     # Example queries
└── tests/
    └── run_tests.py           # Test suite
```

---

## 🔍 Architecture

### **Database Schema**

pg-memory uses PostgreSQL with the following key tables:

- **sessions** - Conversation sessions
- **observations** - Structured memory entries
- **raw_exchanges** - Raw conversation data
- **summaries** - Auto-generated session summaries
- **context_checkpoints** - Compaction checkpoints
- **decision_log** - Tracked decisions
- **embedding_cache** - Cached vector embeddings

All tables use **XID** (time-sorted 20-character IDs) for optimal performance.

### **Data Flow**

```
OpenClaw Session
    ↓
pre-compaction hook
    ↓
memory_handler.py
    ↓
PostgreSQL (with pgvector)
    ↓
Automatic backup (daily)
```

---

## 🛠️ Maintenance

### **Daily (Automated)**

- ✅ Backups at 3 AM
- ✅ Old backup cleanup (>7 days)
- ✅ Log rotation

### **Weekly (Manual)**

```bash
# Check backup status
ls -lh ~/.openclaw/workspace/backups/

# View recent logs
tail -f ~/.openclaw/workspace/logs/*.log

# Check disk usage
df -h ~/.openclaw/workspace/
```

### **Monthly (Manual)**

```bash
# Update pg-memory
cd ~/openclaw-pg-memory
git pull origin main

# Update OpenClaw
npm update -g openclaw

# Restart services
openclaw gateway restart
```

---

## 🐛 Troubleshooting

### **Common Issues**

**Problem:** `Connection refused`
```bash
# Check if PostgreSQL is running
brew services list | grep postgres
brew services start postgresql@18
```

**Problem:** `Ollama not found`
```bash
# Install Ollama
brew install ollama
brew services start ollama
ollama pull bge-m3:latest
```

**Problem:** `pg-memory command not found`
```bash
# Reinstall skill
cd ~/openclaw-pg-memory
./install.sh
openclaw gateway restart
```

### **Get Help**

- 📖 **Documentation:** [`docs/`](docs/)
- 🐛 **Issues:** https://github.com/pottertech/openclaw-pg-memory/issues
- 💬 **Discord:** https://discord.gg/clawd

---

## 📊 Performance

### **Benchmarks**

| Operation | Time | Notes |
|-----------|------|-------|
| **Write Observation** | <10ms | With embedding |
| **Semantic Search** | <50ms | 1000+ observations |
| **Context Retrieval** | <100ms | Full session restore |
| **Backup (Daily)** | ~2s | Compressed |

### **Storage**

- **Per Observation:** ~2-3 KB (with embedding)
- **Per Session:** ~50-100 KB (average)
- **Daily Growth:** ~1-2 MB (typical usage)

---

## 🔒 Security

### **Best Practices**

- ✅ Database credentials stored in Keychain
- ✅ Local-only by default (no external access)
- ✅ Automated backups with encryption option
- ✅ Rate limiting on all operations
- ✅ Input validation and sanitization

### **Production Deployment**

For production use:

1. Enable SSL for PostgreSQL
2. Use strong database passwords
3. Restrict network access
4. Enable audit logging
5. Set up monitoring

See [`docs/PRODUCTION.md`](docs/PRODUCTION.md) for detailed guidance.

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python3 tests/run_tests.py`
5. Submit a pull request

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

## 🎯 What's New in v3.0.0

### **Major Features**

- ✅ **Complete XID Migration** - All tables use time-sorted IDs
- ✅ **Tiered Summary Generation** - Intelligent compaction summaries
- ✅ **Web Dashboard** - Visual interface for memory management
- ✅ **Automated Backups** - Daily backups with retention policy
- ✅ **Enhanced Context Management** - Better pre/post compaction handling

### **Improvements**

- 25% storage reduction with XID
- 2-5x faster semantic search
- Better error handling and recovery
- Improved multi-instance support
- Comprehensive test suite (7/7 passing)

### **Documentation**

- Complete installation guide
- Usage examples for all features
- Troubleshooting for common issues
- API documentation
- Production deployment guide

---

## 🎉 Ready to Get Started?

```bash
git clone https://github.com/pottertech/openclaw-pg-memory.git
cd openclaw-pg-memory
./install.sh
```

**Welcome to production-ready memory for OpenClaw!** 🦞

---

*Built with ❤️ by Potter's Quill Media*
