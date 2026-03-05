
# ============================================================================
# OBSERVATION RESOLUTION FUNCTIONS (v3.0.0)
# ============================================================================

def resolve_observation(obs_id: str, resolved_at: Optional[datetime] = None) -> bool:
    """Mark an observation as resolved with timestamp.
    
    Args:
        obs_id: Observation ID to resolve
        resolved_at: Timestamp (defaults to now)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if resolved_at is None:
        resolved_at = datetime.now()
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE observations 
            SET status = 'resolved', 
                resolved_at = %s,
                updated_at = NOW()
            WHERE id = %s AND status != 'resolved'
        """, (resolved_at, obs_id))
        
        rows_affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        if rows_affected > 0:
            print(f"✅ Observation {obs_id} marked as resolved")
            print(f"   Resolved at: {resolved_at.isoformat()}")
            return True
        else:
            print(f"⚠️  Observation {obs_id} not found or already resolved")
            return False
            
    except Exception as e:
        print(f"❌ Error resolving observation: {e}")
        return False

def cleanup_resolved_observations(days: int = 180, dry_run: bool = False) -> int:
    """Delete resolved observations older than specified days.
    
    Args:
        days: Days since resolution (default: 180 = 6 months)
        dry_run: If True, only show what would be deleted
    
    Returns:
        int: Number of observations deleted (or would be deleted in dry_run)
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Count first
        cur.execute("""
            SELECT COUNT(*) FROM observations 
            WHERE status = 'resolved' AND resolved_at < %s
        """, (cutoff_date,))
        count = cur.fetchone()[0]
        
        if count == 0:
            print(f"✅ No resolved observations older than {days} days")
            cur.close()
            conn.close()
            return 0
        
        print(f"📊 Found {count} resolved observations older than {days} days")
        print(f"   Cutoff date: {cutoff_date.isoformat()}")
        
        if dry_run:
            print(f"🔍 DRY RUN - would delete {count} observations")
            cur.close()
            conn.close()
            return count
        
        # Delete
        cur.execute("""
            DELETE FROM observations 
            WHERE status = 'resolved' AND resolved_at < %s
        """, (cutoff_date,))
        
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Deleted {deleted} resolved observations")
        return deleted
        
    except Exception as e:
        print(f"❌ Error cleaning up resolved observations: {e}")
        return 0

