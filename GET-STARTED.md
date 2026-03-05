# Get Started with pg-memory v3.0.0

**Your Complete Setup Guide**

---

## 🚀 Option 1: Automated Install (Recommended)

Perfect for beginners. One command does everything:

```bash
git clone https://github.com/pottertech/openclaw-pg-memory.git
cd openclaw-pg-memory
./install.sh
```

**Time:** 5-10 minutes  
**Interaction:** None (fully automated)  
**Result:** Complete installation with OpenClaw integration

---

## 🛠️ Option 2: Manual Install

For advanced users who want full control.

See [`docs/MANUAL-INSTALL.md`](docs/MANUAL-INSTALL.md)

---

## ✅ Verify Installation

After installation, verify everything works:

```bash
# 1. Test database connection
psql -U openclaw -d openclaw_memory -c "SELECT 1"

# Expected: Shows "1"

# 2. Test pg-memory
python3 scripts/pg_memory.py --stats

# Expected: Shows database statistics

# 3. Test OpenClaw integration
openclaw status

# Expected: Shows gateway running
```

---

## 🎯 Next Steps

### **1. Configure Your Environment**

Add to `~/.zshrc`:

```bash
export PG_MEMORY_DB=openclaw_memory
export PG_MEMORY_USER=openclaw
export PG_MEMORY_HOST=localhost
export PG_MEMORY_DEBUG=0
```

Then reload:
```bash
source ~/.zshrc
```

### **2. Start Using Memory**

pg-memory automatically activates when you use OpenClaw. No additional configuration needed!

### **3. Explore the Web Dashboard** (Optional)

```bash
cd pg-memory-webui
python3 app/main.py
```

Access at: http://localhost:8080

---

## 📖 Learn More

- **[Usage Guide](docs/USAGE.md)** - How to use pg-memory
- **[API Reference](docs/API.md)** - Python API documentation
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues
- **[Configuration](docs/CONFIGURATION.md)** - Advanced settings

---

## 🆘 Need Help?

- Check [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
- Open an issue on GitHub
- Join our Discord: https://discord.gg/clawd

---

**Welcome to pg-memory v3.0.0!** 🦞
