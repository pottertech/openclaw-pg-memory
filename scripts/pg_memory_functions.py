# ============================================================================
# OBSERVATION RESOLUTION FUNCTIONS (v3.0.0)
# ============================================================================

def resolve_observation(obs_id: str, resolved_at=None) -> bool:
    """Mark an observation as resolved with timestamp."""
    from datetime import datetime
    if resolved_at is None:
        resolved_at = datetime.now()
    
    try:
        config = MemoryConfig()
        mem = PostgresMemory(config)
        conn = mem.pool.getconn()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE observations 
            SET status = 'resolved', resolved_at = %s, updated_at = NOW()
            WHERE id = %s AND status != 'resolved'
        """, (resolved_at, obs_id))
        
        rows = cur.rowcount
        conn.commit()
        cur.close()
        mem.pool.putconn(conn)
        
        if rows > 0:
            print(f"✅ Observation {obs_id} marked as resolved")
            return True
        else:
            print(f"⚠️  Observation {obs_id} not found or already resolved")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def cleanup_resolved_observations(days=180, dry_run=False):
    """Delete resolved observations older than specified days."""
    from datetime import timedelta
    try:
        config = MemoryConfig()
        mem = PostgresMemory(config)
        conn = mem.pool.getconn()
        cur = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        cur.execute("SELECT COUNT(*) FROM observations WHERE status = 'resolved' AND resolved_at < %s", (cutoff,))
        count = cur.fetchone()[0]
        
        if count == 0:
            print(f"✅ No resolved observations older than {days} days")
            return 0
        
        print(f"📊 Found {count} resolved observations older than {days} days")
        
        if dry_run:
            print(f"🔍 DRY RUN - would delete {count} observations")
            return count
        
        cur.execute("DELETE FROM observations WHERE status = 'resolved' AND resolved_at < %s", (cutoff,))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        mem.pool.putconn(conn)
        
        print(f"✅ Deleted {deleted} resolved observations")
        return deleted
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0
