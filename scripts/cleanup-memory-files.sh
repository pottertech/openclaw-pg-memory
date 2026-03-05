#!/bin/bash
# Memory Files Cleanup Script
# Keeps recent daily files, archives or deletes old ones
# 
# Usage:
#   ./cleanup-memory-files.sh [days_to_keep]
#
# Examples:
#   ./cleanup-memory-files.sh      # Keep last 7 days (default)
#   ./cleanup-memory-files.sh 14   # Keep last 14 days
#   ./cleanup-memory-files.sh 30   # Keep last 30 days

set -e

MEMORY_DIR="$HOME/.openclaw/workspace/memory"
ARCHIVE_DIR="$MEMORY_DIR/archive"
KEEP_DAYS=${1:-7}  # Default: keep 7 days

echo "🧹 Memory Files Cleanup"
echo "========================"
echo ""
echo "Configuration:"
echo "  Memory directory: $MEMORY_DIR"
echo "  Archive directory: $ARCHIVE_DIR"
echo "  Keep files from last: $KEEP_DAYS days"
echo ""

# Calculate cutoff date
CUTOFF_DATE=$(date -v -${KEEP_DAYS}d +%Y-%m-%d 2>/dev/null || date -d "${KEEP_DAYS} days ago" +%Y-%m-%d)
echo "  Cutoff date: $CUTOFF_DATE (files older will be archived)"
echo ""

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# Count files
TOTAL_FILES=$(ls -1 "$MEMORY_DIR"/*.md 2>/dev/null | wc -l)
echo "📊 Current state:"
echo "  Total files: $TOTAL_FILES"
echo ""

# Find old files (excluding working-buffer.md and index files)
echo "🔍 Scanning for files older than $CUTOFF_DATE..."
echo ""

ARCHIVED=0
DELETED=0

for file in "$MEMORY_DIR"/20*.md; do
    [ -f "$file" ] || continue
    
    filename=$(basename "$file")
    
    # Skip working-buffer and index files
    if [[ "$filename" == *"working-buffer"* ]] || [[ "$filename" == *"INDEX"* ]]; then
        echo "  ⏭️  Skipping: $filename (system file)"
        continue
    fi
    
    # Extract date from filename (YYYY-MM-DD.md or YYYY-MM-DD-HHMM.md)
    file_date=$(echo "$filename" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}')
    
    if [[ -z "$file_date" ]]; then
        echo "  ⏭️  Skipping: $filename (no date found)"
        continue
    fi
    
    # Compare dates
    if [[ "$file_date" < "$CUTOFF_DATE" ]]; then
        echo "  📦 Archiving: $filename (date: $file_date)"
        mv "$file" "$ARCHIVE_DIR/"
        ((ARCHIVED++))
    else
        echo "  ✅ Keeping: $filename (date: $file_date)"
    fi
done

echo ""
echo "📈 Results:"
echo "  Archived: $ARCHIVED files → $ARCHIVE_DIR/"
echo "  Deleted: $DELETED files"
echo ""

# Show remaining files
REMAINING=$(ls -1 "$MEMORY_DIR"/*.md 2>/dev/null | wc -l)
echo "📊 Final state:"
echo "  Remaining files: $REMAINING"
echo "  Archived files: $(ls -1 "$ARCHIVE_DIR"/*.md 2>/dev/null | wc -l)"
echo ""

# Show what's left
echo "📁 Remaining daily files:"
ls -lt "$MEMORY_DIR"/20*.md 2>/dev/null | head -10 | awk '{print "  " $9}'

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To restore archived files:"
echo "  mv $ARCHIVE_DIR/*.md $MEMORY_DIR/"
echo ""
echo "To delete archived files permanently:"
echo "  rm $ARCHIVE_DIR/*.md"
