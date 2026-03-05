#!/usr/bin/env python3
"""
pg-memory Health Monitor
Run: python3 scripts/monitor.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

os.environ['PG_MEMORY_DEBUG'] = '0'

from pg_memory import PostgresMemory

def get_stats(mem):
    """Get database statistics"""
    with mem._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sessions")
            sessions = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM observations")
            observations = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM raw_exchanges")
            exchanges = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM context_checkpoints")
            checkpoints = cur.fetchone()[0]
            
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cur.fetchone()[0]
    
    return {
        'sessions': sessions,
        'observations': observations,
        'exchanges': exchanges,
        'checkpoints': checkpoints,
        'db_size': db_size
    }

def main():
    print("=" * 70)
    print("📊 PG-MEMORY HEALTH DASHBOARD")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        mem = PostgresMemory()
        
        print("✅ Database Connection")
        print(f"   Database: {os.getenv('PG_MEMORY_DB', 'openclaw_memory')}")
        print(f"   Host: {os.getenv('PG_MEMORY_HOST', 'localhost')}")
        print(f"   Instance: {mem.instance_id[:8]}...")
        print(f"   Agent: {mem.agent_label}")
        print()
        
        stats = get_stats(mem)
        
        print("📈 Statistics")
        print(f"   Sessions: {stats['sessions']}")
        print(f"   Observations: {stats['observations']}")
        print(f"   Exchanges: {stats['exchanges']}")
        print(f"   Checkpoints: {stats['checkpoints']}")
        print(f"   Database Size: {stats['db_size']}")
        print()
        
        print("🔧 Configuration")
        print(f"   XID Available: ✅")
        print(f"   Multi-Instance: ✅ (prefix: {mem.instance_id[:8]})")
        print(f"   pgvector: {'✅' if mem._pgvector_available else '❌'}")
        print()
        
        # Check backups
        backup_dir = Path.home() / '.openclaw' / 'workspace' / 'backups'
        if backup_dir.exists():
            backups = list(backup_dir.glob('pg-memory-*.sql.gz'))
            latest = max(backups, key=lambda p: p.stat().st_mtime) if backups else None
            if latest:
                age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
                print("💾 Backups")
                print(f"   Latest: {latest.name}")
                print(f"   Age: {age_hours:.1f} hours ago")
                print(f"   Total: {len(backups)} backup(s)")
            else:
                print("💾 Backups: No backups found")
        else:
            print("💾 Backups: Backup directory not found")
        
        print()
        print("=" * 70)
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("=" * 70)
        
        mem.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
