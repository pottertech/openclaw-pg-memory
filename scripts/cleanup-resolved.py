#!/usr/bin/env python3
"""
pg-memory: Cleanup resolved observations older than specified days
Usage: python3 cleanup-resolved.py [--days 180] [--dry-run]
"""
import os
import sys
import argparse
from datetime import datetime, timedelta
import psycopg2

# Database config
DB_HOST = os.getenv("PG_MEMORY_HOST", "localhost")
DB_PORT = os.getenv("PG_MEMORY_PORT", "5432")
DB_NAME = os.getenv("PG_MEMORY_DB", "openclaw_memory")
DB_USER = os.getenv("PG_MEMORY_USER", os.getenv("USER", "skipppotter"))

def cleanup_resolved(days=180, dry_run=False):
    """Delete resolved observations older than specified days."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER
        )
        cur = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        # Count
        cur.execute(
            "SELECT COUNT(*) FROM observations WHERE status = 'resolved' AND resolved_at < %s",
            (cutoff,)
        )
        count = cur.fetchone()[0]
        
        if count == 0:
            print(f"✅ No resolved observations older than {days} days")
            return 0
        
        print(f"📊 Found {count} resolved observations older than {days} days")
        print(f"   Cutoff: {cutoff.isoformat()}")
        
        if dry_run:
            print(f"🔍 DRY RUN - would delete {count} observations")
            return count
        
        # Delete
        cur.execute(
            "DELETE FROM observations WHERE status = 'resolved' AND resolved_at < %s",
            (cutoff,)
        )
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Deleted {deleted} resolved observations")
        return deleted
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def resolve_obs(obs_id, date_str=None):
    """Mark observation as resolved."""
    from datetime import datetime
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER
        )
        cur = conn.cursor()
        
        resolved_at = datetime.fromisoformat(date_str) if date_str else datetime.now()
        
        cur.execute("""
            UPDATE observations 
            SET status = 'resolved', resolved_at = %s, updated_at = NOW()
            WHERE id = %s AND status != 'resolved'
        """, (resolved_at, obs_id))
        
        rows = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        if rows > 0:
            print(f"✅ Observation {obs_id} marked as resolved")
            return True
        else:
            print(f"⚠️  Observation {obs_id} not found or already resolved")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="pg-memory: Resolve/Cleanup observations")
    subparsers = parser.add_subparsers(dest="command")
    
    # Cleanup
    cleanup_p = subparsers.add_parser("cleanup", help="Delete old resolved observations")
    cleanup_p.add_argument("--days", type=int, default=180, help="Days threshold")
    cleanup_p.add_argument("--dry-run", action="store_true", help="Preview only")
    
    # Resolve
    resolve_p = subparsers.add_parser("resolve", help="Mark observation as resolved")
    resolve_p.add_argument("obs_id", help="Observation ID")
    resolve_p.add_argument("--date", help="Resolved date (ISO format)")
    
    args = parser.parse_args()
    
    if args.command == "cleanup":
        sys.exit(0 if cleanup_resolved(args.days, args.dry_run) >= 0 else 1)
    elif args.command == "resolve":
        sys.exit(0 if resolve_obs(args.obs_id, args.date) else 1)
    else:
        parser.print_help()
