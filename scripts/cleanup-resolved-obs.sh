#!/bin/bash
# pg-memory: Cleanup resolved observations older than 6 months
# Runs daily via cron at 3:00 AM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUP_PY="$SCRIPT_DIR/cleanup-resolved.py"

echo "🧠 pg-memory: Cleaning up resolved observations..."
echo "   Timestamp: $(date -Iseconds)"
echo "   Threshold: 180 days (6 months)"
echo ""

# Run cleanup
python3 "$CLEANUP_PY" cleanup --days 180

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Cleanup completed successfully"
else
    echo ""
    echo "❌ Cleanup failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
