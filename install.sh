#!/bin/bash
#===============================================================================
# OpenClaw pg-memory v3.1.2 - Automated Installer
# Purpose: Durable memory persistence for OpenClaw
# Usage: ./install.sh [--separation-mode]
#===============================================================================
#
# SEPARATION NOTICE:
# This installer does NOT install token-management features.
# Token-guardian owns: bloat detection, archive rotation, danger-zone handling
# pg-memory owns: durable storage, retrieval, restoration from stored memory
#
# Use --separation-mode to ensure clean separation (default behavior)
#===============================================================================

set -e  # Exit on error

# Parse arguments
SEPARATION_MODE=true  # Default to separation mode
SKIP_LEGACY_CONTEXT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --legacy-context)
            SEPARATION_MODE=false
            SKIP_LEGACY_CONTEXT=false
            shift
            ;;
        --separation-mode)
            SEPARATION_MODE=true
            shift
            ;;
        --help)
            echo "Usage: ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --separation-mode      Clean separation from token-guardian (DEFAULT)"
            echo "  --legacy-context       Install legacy context management (NOT RECOMMENDED)"
            echo "  --help                 Show this help message"
            echo ""
            echo "NOTE: This installer does NOT include token-management features."
            echo "      Install openclaw-token-guardian separately for that functionality."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "🦞 OpenClaw pg-memory v3.1.2 Installer"
echo "=========================================="
echo ""

if [[ "$SEPARATION_MODE" == true ]]; then
    echo "✅ Separation mode enabled"
    echo "   Token-guardian owns: context management, bloat detection"
    echo "   pg-memory owns: durable storage, retrieval, restoration"
    echo ""
fi

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
log_step "Step 1/7: Checking prerequisites..."

if ! command -v brew &> /dev/null; then
    log_error "Homebrew not installed!"
    echo "   Install with: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
else
    log_info "Homebrew found: \$(brew --version | head -1)"
fi

if ! command -v node &> /dev/null; then
    log_info "Installing Node.js..."
    brew install node
else
    log_info "Node.js found: \$(node --version)"
fi

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found!"
    exit 1
else
    log_info "Python found: \$(python3 --version)"
fi

#-------------------------------------------------------------------------------
# Step 2: Install PostgreSQL
#-------------------------------------------------------------------------------
echo ""
log_step "Step 2/7: Installing PostgreSQL 18..."

if ! command -v psql &> /dev/null; then
    log_info "Installing PostgreSQL 18..."
    brew install postgresql@18
else
    log_info "PostgreSQL already installed: \$(psql --version)"
fi

log_info "Starting PostgreSQL service..."
brew services start postgresql@18
sleep 3

#-------------------------------------------------------------------------------
# Step 3: Create Database and User
#-------------------------------------------------------------------------------
echo ""
log_step "Step 3/7: Setting up database..."

DB_USER="openclaw"
DB_NAME="openclaw_memory"

# Create user if not exists
if psql -U postgres -c "\du" 2>/dev/null | grep -q $DB_USER; then
    log_info "User '\$DB_USER' already exists"
else
    log_info "Creating user '\$DB_USER'..."
    createuser -U postgres $DB_USER || true
fi

# Create database if not exists
if psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw $DB_NAME; then
    log_info "Database '\$DB_NAME' already exists"
else
    log_info "Creating database '\$DB_NAME'..."
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
log_step "Step 4/7: Setting up Ollama..."

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
log_step "Step 5/7: Installing Python dependencies..."

log_info "Installing psycopg2-binary..."
pip3 install --break-system-packages psycopg2-binary 2>/dev/null || pip3 install psycopg2-binary

log_info "Installing python-xid..."
pip3 install --break-system-packages git+https://github.com/pottertech/python_xid.git 2>/dev/null || {
    log_warn "python-xid installation failed, trying alternative..."
    pip3 install --break-system-packages xid 2>/dev/null || pip3 install xid || true
}

log_info "Installing numpy..."
pip3 install --break-system-packages numpy 2>/dev/null || pip3 install numpy

#-------------------------------------------------------------------------------
# Step 6: Initialize Database Schema
#-------------------------------------------------------------------------------
echo ""
log_step "Step 6/7: Initializing database schema..."

cd "\$(dirname "\$0")"

log_info "Running schema initialization..."
psql -U $DB_USER -d $DB_NAME -f sql/init_schema.sql 2>/dev/null || {
    log_warn "Schema initialization had warnings (tables may already exist)"
}

log_info "Database schema initialized!"

#-------------------------------------------------------------------------------
# Step 7: Configure Environment
#-------------------------------------------------------------------------------
echo ""
log_step "Step 7/7: Configuring environment..."

# Create config directory
CONFIG_DIR="\$HOME/.openclaw/workspace/config"
mkdir -p "\$CONFIG_DIR"

# Create memory.yaml config
if [[ "$SEPARATION_MODE" == true ]]; then
    cat > "\$CONFIG_DIR/memory.yaml" << EOF
# pg-memory v3.1.2 Configuration
# Separation Mode: Clean separation from token-guardian
# Auto-generated: \$(date)
#
# OWNERSHIP:
#   token-guardian owns: token thresholds, bloat detection, live context management
#   pg-memory owns: durable storage, retrieval, restoration from stored memory
#
# For token management, install: openclaw-token-guardian

memory:
  # Core features (pg-memory)
  primary_backend: postgresql
  markdown_backup: true
  retention_days: 7
  agent_id: openclaw
  fallback_on_pgdb_down: true
  
  # SEPARATION: These are OWNED BY token-guardian, not pg-memory
  # Do NOT enable these unless token-guardian is NOT installed
  enable_context_guardian: false      # token-guardian owns this
  enable_compaction_cron: false       # token-guardian owns this
  enable_token_monitoring: false      # token-guardian owns this
  enable_auto_pruning: false          # token-guardian owns this
  enable_emergency_reduction: false   # token-guardian owns this
  
  # pg-memory features (always enabled)
  enable_persistent_storage: true     # Durable PostgreSQL storage
  enable_embeddings: true             # BGE-M3 semantic embeddings
  enable_semantic_retrieval: true     # Vector search
  enable_memory_capture: true          # Save conversations
  enable_summaries: true              # Long-term summaries
  enable_context_restoration: true    # Post-compaction restore

postgresql:
  host: localhost
  port: 5432
  database: $DB_NAME
  user: $DB_USER
EOF
else
    cat > "\$CONFIG_DIR/memory.yaml" << EOF
# pg-memory v3.1.2 Configuration (LEGACY MODE)
# WARNING: Overlaps with token-guardian. Use --separation-mode instead.
# Auto-generated: \$(date)

memory:
  primary_backend: postgresql
  markdown_backup: true
  retention_days: 7
  agent_id: openclaw
  fallback_on_pgdb_down: true
  
  # LEGACY: All features enabled (overlaps with token-guardian)
  enable_context_guardian: true
  enable_compaction_cron: true
  enable_token_monitoring: true
  enable_auto_pruning: true
  enable_emergency_reduction: true
  enable_persistent_storage: true
  enable_embeddings: true
  enable_semantic_retrieval: true
  enable_memory_capture: true
  enable_summaries: true
  enable_context_restoration: true

postgresql:
  host: localhost
  port: 5432
  database: $DB_NAME
  user: $DB_USER
EOF
fi

log_info "Created memory.yaml configuration"

# Set environment variables
ENV_BLOCK="
# pg-memory v3.1.2 Environment
export PG_MEMORY_DB=$DB_NAME
export PG_MEMORY_USER=$DB_USER
export PG_MEMORY_HOST=localhost
export PG_MEMORY_PORT=5432
export PG_MEMORY_DEBUG=0
export OPENCLAW_INSTANCE_ID=\$(uuidgen)
"

if ! grep -q "PG_MEMORY_DB" ~/.zshrc 2>/dev/null; then
    echo "\$ENV_BLOCK" >> ~/.zshrc
    log_info "Added environment variables to ~/.zshrc"
    log_warn "Run 'source ~/.zshrc' or restart terminal to apply"
else
    log_info "Environment variables already configured"
fi

# Copy scripts to workspace
WORKSPACE_SCRIPTS="\$HOME/.openclaw/workspace/skills/pg-memory"
mkdir -p "\$WORKSPACE_SCRIPTS"

log_info "Copying pg-memory scripts to workspace..."
cp scripts/*.py "\$WORKSPACE_SCRIPTS/"
cp scripts/pg-memory-cli "\$WORKSPACE_SCRIPTS/"
chmod +x "\$WORKSPACE_SCRIPTS"/*.py
chmod +x "\$WORKSPACE_SCRIPTS"/pg-memory-cli

# Install compaction hook ONLY (for memory persistence, not token management)
OPENCLAW_HOOKS="\$HOME/.openclaw/workspace/hooks"
mkdir -p "\$OPENCLAW_HOOKS"

log_info "Installing pg-memory compaction hook..."
cp -r hooks/pg-memory-compaction "\$OPENCLAW_HOOKS/"

# Configure OpenClaw
OPENCLAW_CONFIG="\$HOME/.openclaw/openclaw.json"

if [ -f "\$OPENCLAW_CONFIG" ]; then
    log_info "Updating OpenClaw configuration..."
    cp "\$OPENCLAW_CONFIG" "\$OPENCLAW_CONFIG.backup"
    
    if ! grep -q "pg-memory-compaction" "\$OPENCLAW_CONFIG"; then
        python3 << PYTHON_EOF
import json

with open('\$OPENCLAW_CONFIG', 'r') as f:
    config = json.load(f)

if 'hooks' not in config:
    config['hooks'] = {}
if 'internal' not in config['hooks']:
    config['hooks']['internal'] = {}
if 'entries' not in config['hooks']['internal']:
    config['hooks']['internal']['entries'] = {}

# NOTE: This hook ONLY handles memory persistence
# Token management is handled by openclaw-token-guardian
config['hooks']['internal']['entries']['pg-memory-compaction'] = {
    'enabled': True,
    'path': './hooks/pg-memory-compaction/handler.js',
    'note': 'Memory persistence only - token management by token-guardian'
}

with open('\$OPENCLAW_CONFIG', 'w') as f:
    json.dump(config, f, indent=4)

print("Configuration updated")
PYTHON_EOF
        log_info "OpenClaw configuration updated!"
    else
        log_info "pg-memory already configured"
    fi
else
    log_warn "OpenClaw config not found. See docs/INTEGRATION.md"
fi

#-------------------------------------------------------------------------------
# Summary
#-------------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "🎉 Installation Complete!"
echo "=========================================="
echo ""
echo "✅ Installed:"
echo "   - PostgreSQL 18 with pgvector"
echo "   - Ollama with BGE-M3 embeddings"
echo "   - pg-memory v3.1.2 scripts"
echo "   - Memory persistence hook"
echo ""
if [[ "$SEPARATION_MODE" == true ]]; then
    echo "🔒 Separation mode: ENABLED"
    echo "   pg-memory owns: durable storage, retrieval, restoration"
    echo ""
    echo "⚠️  For token management, install openclaw-token-guardian:"
    echo "   git clone https://github.com/pottertech/openclaw-token-guardian"
else
    echo "⚠️  Legacy mode: Context management features enabled"
    echo "   WARNING: May overlap with token-guardian"
fi
echo ""
echo "📁 Locations:"
echo "   - Database: $DB_NAME"
echo "   - User: $DB_USER"
echo "   - Scripts: \$WORKSPACE_SCRIPTS"
echo "   - Config: \$CONFIG_DIR/memory.yaml"
echo ""
echo "🚀 Next steps:"
echo "   1. source ~/.zshrc"
echo "   2. openclaw gateway restart"
echo "   3. python3 \$WORKSPACE_SCRIPTS/pg_memory.py --stats"
echo ""
echo "📖 See docs/SEPARATION.md for ownership details"
echo "=========================================="
