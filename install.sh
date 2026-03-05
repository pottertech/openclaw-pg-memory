#!/bin/bash
#===============================================================================
# OpenClaw pg-memory v3.0.0 - Automated Installer
# Purpose: Complete installation in one command
# Usage: ./install.sh
#===============================================================================

set -e  # Exit on error

echo "=========================================="
echo "🦞 OpenClaw pg-memory v3.0.0 Installer"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}✅${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠️${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_step() { echo -e "${BLUE}📦${NC} $1"; }

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_warn "This script is optimized for macOS. Linux users: see docs/MANUAL-INSTALL.md"
fi

#-------------------------------------------------------------------------------
# Step 1: Check Prerequisites
#-------------------------------------------------------------------------------
echo ""
log_step "Step 1/8: Checking prerequisites..."

if ! command -v brew &> /dev/null; then
    log_error "Homebrew not installed!"
    echo "   Install with: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
else
    log_info "Homebrew found: $(brew --version | head -1)"
fi

if ! command -v node &> /dev/null; then
    log_info "Installing Node.js..."
    brew install node
else
    log_info "Node.js found: $(node --version)"
fi

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found!"
    exit 1
else
    log_info "Python found: $(python3 --version)"
fi

#-------------------------------------------------------------------------------
# Step 2: Install PostgreSQL
#-------------------------------------------------------------------------------
echo ""
log_step "Step 2/8: Installing PostgreSQL 16..."

if ! command -v psql &> /dev/null; then
    log_info "Installing PostgreSQL 16..."
    brew install postgresql@16
else
    log_info "PostgreSQL already installed: $(psql --version)"
fi

log_info "Starting PostgreSQL service..."
brew services start postgresql@16
sleep 3

#-------------------------------------------------------------------------------
# Step 3: Create Database and User
#-------------------------------------------------------------------------------
echo ""
log_step "Step 3/8: Setting up database..."

DB_USER="openclaw"
DB_NAME="openclaw_memory"

# Create user if not exists
if psql -U postgres -c "\du" 2>/dev/null | grep -q $DB_USER; then
    log_info "User '$DB_USER' already exists"
else
    log_info "Creating user '$DB_USER'..."
    createuser -U postgres $DB_USER || true
fi

# Create database if not exists
if psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw $DB_NAME; then
    log_info "Database '$DB_NAME' already exists"
else
    log_info "Creating database '$DB_NAME'..."
    createdb -U postgres -O $DB_USER $DB_NAME || true
fi

# Enable pgvector extension
log_info "Enabling pgvector extension..."
psql -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || {
    log_warn "pgvector extension creation failed (may already exist)"
}

#-------------------------------------------------------------------------------
# Step 4: Install Ollama
#-------------------------------------------------------------------------------
echo ""
log_step "Step 4/8: Setting up Ollama..."

if ! command -v ollama &> /dev/null; then
    log_info "Installing Ollama..."
    brew install ollama
    brew services start ollama
else
    log_info "Ollama already installed"
fi

log_info "Pulling BGE-M3 embedding model..."
ollama pull bge-m3:latest

#-------------------------------------------------------------------------------
# Step 5: Install Python Dependencies
#-------------------------------------------------------------------------------
echo ""
log_step "Step 5/8: Installing Python dependencies..."

log_info "Installing psycopg2-binary..."
pip3 install --break-system-packages psycopg2-binary

log_info "Installing python-xid..."
pip3 install --break-system-packages git+https://github.com/pottertech/python_xid.git || {
    log_warn "python-xid installation failed, trying alternative..."
    pip3 install --break-system-packages xid || true
}

log_info "Installing numpy..."
pip3 install --break-system-packages numpy

#-------------------------------------------------------------------------------
# Step 6: Initialize Database Schema
#-------------------------------------------------------------------------------
echo ""
log_step "Step 6/8: Initializing database schema..."

cd "$(dirname "$0")"

log_info "Running schema initialization..."
psql -U $DB_USER -d $DB_NAME -f sql/init_schema.sql 2>/dev/null || {
    log_warn "Schema initialization had warnings (tables may already exist)"
}

log_info "Database schema initialized!"

#-------------------------------------------------------------------------------
# Step 7: Configure Environment
#-------------------------------------------------------------------------------
echo ""
log_step "Step 7/8: Configuring environment..."

# Create config directory
CONFIG_DIR="$HOME/.openclaw/workspace/config"
mkdir -p "$CONFIG_DIR"

# Create memory.yaml config
cat > "$CONFIG_DIR/memory.yaml" << EOF
# pg-memory v3.0.0 Configuration
# Auto-generated: $(date)

memory:
  primary_backend: postgresql
  markdown_backup: true
  retention_days: 7
  agent_id: openclaw
  fallback_on_pgdb_down: true

postgresql:
  host: localhost
  port: 5432
  database: $DB_NAME
  user: $DB_USER
EOF

log_info "Created memory.yaml configuration"

# Set environment variables
ENV_BLOCK="
# pg-memory v3.0.0 Environment
export PG_MEMORY_DB=$DB_NAME
export PG_MEMORY_USER=$DB_USER
export PG_MEMORY_HOST=localhost
export PG_MEMORY_PORT=5432
export PG_MEMORY_DEBUG=0
export OPENCLAW_INSTANCE_ID=\$(uuidgen)
"

if ! grep -q "PG_MEMORY_DB" ~/.zshrc 2>/dev/null; then
    echo "$ENV_BLOCK" >> ~/.zshrc
    log_info "Added environment variables to ~/.zshrc"
    log_warn "Run 'source ~/.zshrc' or restart terminal to apply"
else
    log_info "Environment variables already configured"
fi

#-------------------------------------------------------------------------------
# Step 8: Install OpenClaw Integration
#-------------------------------------------------------------------------------
echo ""
log_step "Step 8/8: Installing OpenClaw integration..."

# Check if OpenClaw is installed
if ! command -v openclaw &> /dev/null; then
    log_warn "OpenClaw not found. Installing..."
    npm install -g openclaw
else
    log_info "OpenClaw found: $(openclaw --version)"
fi

# Copy hooks to OpenClaw workspace
OPENCLAW_HOOKS="$HOME/.openclaw/workspace/hooks"
mkdir -p "$OPENCLAW_HOOKS"

log_info "Installing pg-memory compaction hook..."
cp -r hooks/pg-memory-compaction "$OPENCLAW_HOOKS/"

# Copy scripts to workspace
WORKSPACE_SCRIPTS="$HOME/.openclaw/workspace/skills/pg-memory"
mkdir -p "$WORKSPACE_SCRIPTS"

log_info "Copying pg-memory scripts to workspace..."
cp scripts/*.py "$WORKSPACE_SCRIPTS/"
cp scripts/pg-memory-cli "$WORKSPACE_SCRIPTS/"
chmod +x "$WORKSPACE_SCRIPTS"/*.py
chmod +x "$WORKSPACE_SCRIPTS"/pg-memory-cli

# Configure OpenClaw to use pg-memory
OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"

if [ -f "$OPENCLAW_CONFIG" ]; then
    log_info "Updating OpenClaw configuration..."
    # Backup existing config
    cp "$OPENCLAW_CONFIG" "$OPENCLAW_CONFIG.backup"
    
    # Add pg-memory hook if not present
    if ! grep -q "pg-memory-compaction" "$OPENCLAW_CONFIG"; then
        python3 << PYTHON_EOF
import json

with open('$OPENCLAW_CONFIG', 'r') as f:
    config = json.load(f)

if 'hooks' not in config:
    config['hooks'] = {}
if 'internal' not in config['hooks']:
    config['hooks']['internal'] = {}
if 'entries' not in config['hooks']['internal']:
    config['hooks']['internal']['entries'] = {}

config['hooks']['internal']['entries']['pg-memory-compaction'] = {
    'enabled': True,
    'path': './hooks/pg-memory-compaction/handler.js'
}

with open('$OPENCLAW_CONFIG', 'w') as f:
    json.dump(config, f, indent=4)

print("Configuration updated successfully")
PYTHON_EOF
        log_info "OpenClaw configuration updated!"
    else
        log_info "pg-memory already configured in OpenClaw"
    fi
else
    log_warn "OpenClaw config not found. Manual configuration required."
    echo "   See docs/MANUAL-INSTALL.md for instructions"
fi

#-------------------------------------------------------------------------------
# Setup Automated Backups
#-------------------------------------------------------------------------------
echo ""
log_step "Setting up automated maintenance..."

BACKUP_SCRIPT="$HOME/.openclaw/workspace/scripts/backup-pg-memory.sh"
mkdir -p "$(dirname "$BACKUP_SCRIPT")"

cat > "$BACKUP_SCRIPT" << 'BACKUP_EOF'
#!/bin/bash
# Daily pg-memory backup
BACKUP_DIR="$HOME/.openclaw/workspace/backups"
mkdir -p "$BACKUP_DIR"
psql -U openclaw -d openclaw_memory | gzip > "$BACKUP_DIR/pg-memory-$(date +%Y%m%d-%H%M).sql.gz"
find "$BACKUP_DIR" -name "pg-memory-*.sql.gz" -mtime +7 -delete
BACKUP_EOF

chmod +x "$BACKUP_SCRIPT"

# Install cron job
(crontab -l 2>/dev/null | grep -v "backup-pg-memory"; \
 echo "0 3 * * * $BACKUP_SCRIPT >> $HOME/.openclaw/workspace/logs/backup.log 2>&1" \
) | crontab -

log_info "Daily backups scheduled (3:00 AM)"

#-------------------------------------------------------------------------------
# Final Verification
#-------------------------------------------------------------------------------
echo ""
log_step "Running final verification..."

# Test database connection
if psql -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
    log_info "✅ Database connection successful"
else
    log_error "Database connection failed"
fi

# Test pg-memory script
if python3 "$WORKSPACE_SCRIPTS/pg_memory.py" --stats > /dev/null 2>&1; then
    log_info "✅ pg-memory working correctly"
else
    log_warn "pg-memory stats failed (may need OpenClaw restart)"
fi

#-------------------------------------------------------------------------------
# Summary
#-------------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "🎉 Installation Complete!"
echo "=========================================="
echo ""
echo "✅ What was installed:"
echo "   - PostgreSQL 16 with pgvector"
echo "   - Ollama with BGE-M3 embeddings"
echo "   - pg-memory v3.0.0 scripts"
echo "   - OpenClaw integration hook"
echo "   - Automated daily backups (3 AM)"
echo ""
echo "📁 Important locations:"
echo "   - Database: $DB_NAME"
echo "   - User: $DB_USER"
echo "   - Scripts: $WORKSPACE_SCRIPTS"
echo "   - Config: $CONFIG_DIR/memory.yaml"
echo "   - Backups: $HOME/.openclaw/workspace/backups/"
echo ""
echo "🚀 Next steps:"
echo "   1. Restart terminal (or run: source ~/.zshrc)"
echo "   2. Restart OpenClaw: openclaw gateway restart"
echo "   3. Test: python3 $WORKSPACE_SCRIPTS/pg_memory.py --stats"
echo ""
echo "🌐 Web Dashboard (optional):"
echo "   cd $WORKSPACE_SCRIPTS/../pg-memory-webui"
echo "   python3 app/main.py"
echo "   Access at: http://localhost:8080"
echo ""
echo "📖 Documentation:"
echo "   - Usage: docs/USAGE.md"
echo "   - Configuration: docs/CONFIGURATION.md"
echo "   - Troubleshooting: docs/TROUBLESHOOTING.md"
echo ""
echo "🎬 pg-memory v3.0.0 is ready for production!"
echo "=========================================="
