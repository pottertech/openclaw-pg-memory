#!/usr/bin/env python3
"""
pg-memory Retention Manager v3.2.0
Safe retention, archive, consolidation, and purge controls for durable memory.

This module handles:
- Retention class management
- Archive operations (hot → cold → archived)
- Consolidation before purge
- Safe purge with protection checks
- Database size control
- Retention policy enforcement

IMPORTANT: This is DURABLE memory retention, not live token management.
Token management is owned by openclaw-token-guardian.
"""

import os
import sys
import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from pg_memory import PostgresMemory, get_config_directory


class RetentionClass(Enum):
    """Retention classes for memory records."""
    CANONICAL = "canonical"
    PINNED = "pinned"
    DECISION = "decision"
    PROCEDURE = "procedure"
    PREFERENCE = "preference"
    PROJECT_FACT = "project_fact"
    SUMMARY = "summary"
    TASK_HISTORY = "task_history"
    OBSERVATION = "observation"
    CHECKPOINT = "checkpoint"
    RAW_EXCHANGE = "raw_exchange"
    EPHEMERAL = "ephemeral"
    SUPERSEDED = "superseded"
    DUPLICATE = "duplicate"


class StorageTier(Enum):
    """Storage tiers for memory records."""
    HOT = "hot"
    COLD = "cold"
    ARCHIVED = "archived"


@dataclass
class RetentionPolicy:
    """User-configurable retention policy."""
    # Protection settings
    keep_pinned_forever: bool = True
    keep_canonical_forever: bool = True
    keep_decisions_forever: bool = True
    keep_procedures_forever: bool = True
    keep_preferences_forever: bool = True
    keep_project_facts_forever: bool = True
    
    # Retention periods (days)
    raw_exchanges_days: int = 60
    ephemeral_days: int = 21
    observation_days: int = 90
    task_history_days: int = 180
    superseded_grace_days: int = 120
    duplicate_grace_days: int = 30
    
    # Limits
    checkpoints_max_per_session: int = 5
    max_database_size_gb: int = 10
    target_database_size_gb: int = 8
    
    # Archive behavior
    archive_before_delete: bool = True
    archive_location: str = "database"  # 'database', 'file', 's3'
    enable_cold_storage: bool = True
    
    # Job settings
    purge_batch_size: int = 1000
    consolidate_before_purge: bool = True
    enable_nightly_retention_job: bool = True
    enable_dry_run: bool = True
    
    # Safety
    size_check_interval_hours: int = 24
    min_records_before_purge: int = 10000
    
    @classmethod
    def from_database(cls, mem: PostgresMemory) -> 'RetentionPolicy':
        """Load policy from database settings."""
        try:
            conn = mem._pool.getconn()
            cur = conn.cursor()
            
            cur.execute("SELECT * FROM retention_settings ORDER BY updated_at DESC LIMIT 1")
            row = cur.fetchone()
            
            cur.close()
            mem._pool.putconn(conn)
            
            if row:
                return cls(**{
                    k: v for k, v in row.items()
                    if k in cls.__dataclass_fields__
                })
        except Exception as e:
            print(f"Warning: Could not load retention settings: {e}")
        
        return cls()  # Return defaults
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }


class RetentionManager:
    """Manages retention, archive, consolidation, and safe purge."""
    
    def __init__(self, memory: PostgresMemory = None):
        """Initialize with PostgresMemory instance."""
        self.memory = memory or PostgresMemory()
        self.policy = RetentionPolicy.from_database(self.memory)
    
    # =========================================================================
    # RETENTION CLASSIFICATION
    # =========================================================================
    
    def classify_retention(self, content: str, tags: List[str], importance: float) -> str:
        """Classify a record into retention class.
        
        Args:
            content: The memory content
            tags: Associated tags
            importance: Importance score (0-1)
            
        Returns:
            Retention class name
        """
        # Check for durable classes
        if 'canonical' in tags:
            return RetentionClass.CANONICAL.value
        if 'decision' in tags:
            return RetentionClass.DECISION.value
        if 'procedure' in tags:
            return RetentionClass.PROCEDURE.value
        if 'preference' in tags:
            return RetentionClass.PREFERENCE.value
        if 'project_fact' in tags:
            return RetentionClass.PROJECT_FACT.value
        
        # High importance → summary
        if importance >= 0.9:
            return RetentionClass.SUMMARY.value
        
        # Ephemeral
        if any(t in tags for t in ['ephemeral', 'temp', 'draft']):
            return RetentionClass.EPHEMERAL.value
        
        # Default
        return RetentionClass.OBSERVATION.value
    
    # =========================================================================
    # ARCHIVE OPERATIONS
    # =========================================================================
    
    def archive_record(self, table: str, record_id: str, reason: str = 'age') -> bool:
        """Archive a single record to cold storage.
        
        Args:
            table: Source table name
            record_id: UUID of record to archive
            reason: Archive reason ('age', 'size', 'manual', 'consolidation')
            
        Returns:
            True if archived successfully
        """
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor()
            
            # Get the record
            cur.execute(f"""
                SELECT * FROM {table} WHERE id = %s
            """, (record_id,))
            
            record = cur.fetchone()
            if not record:
                print(f"Record {record_id} not found in {table}")
                return False
            
            # Insert into archive_storage
            cur.execute("""
                INSERT INTO archive_storage (
                    original_table, original_id, archived_data,
                    archive_type, archive_reason, original_retention_class,
                    original_created_at, original_importance_score,
                    archived_at, archived_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'system')
            """, (
                table,
                record_id,
                json.dumps(dict(record), default=str),
                'full',
                reason,
                record.get('retention_class', 'unknown'),
                record.get('created_at'),
                record.get('importance_score', 0.5)
            ))
            
            # Update source record
            cur.execute(f"""
                UPDATE {table}
                SET storage_tier = 'archived',
                    archived_at = NOW()
                WHERE id = %s
            """, (record_id,))
            
            conn.commit()
            cur.close()
            self.memory._pool.putconn(conn)
            
            print(f"✅ Archived {record_id} from {table}")
            return True
            
        except Exception as e:
            print(f"❌ Error archiving {record_id}: {e}")
            return False
    
    def archive_candidates(self, dry_run: bool = True, limit: int = 1000) -> Dict:
        """Archive records that are eligible for archiving.
        
        Args:
            dry_run: If True, only show what would be archived
            limit: Maximum records to archive
            
        Returns:
            Dict with results
        """
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get archive candidates from view
            cur.execute("""
                SELECT id, retention_class, age_days
                FROM archive_candidates
                LIMIT %s
            """, (limit,))
            
            candidates = cur.fetchall()
            cur.close()
            self.memory._pool.putconn(conn)
            
            if not candidates:
                return {'archived': 0, 'candidates': 0, 'dry_run': dry_run}
            
            archived = 0
            if not dry_run:
                for record in candidates:
                    if self.archive_record('observations', str(record['id'])):
                        archived += 1
            
            return {
                'archived': archived if not dry_run else 0,
                'candidates': len(candidates),
                'dry_run': dry_run,
                'sample': [dict(c) for c in candidates[:5]]
            }
            
        except Exception as e:
            print(f"❌ Error getting archive candidates: {e}")
            return {'archived': 0, 'candidates': 0, 'error': str(e)}
    
    # =========================================================================
    # SAFE PURGE
    # =========================================================================
    
    def can_purge(self, record_id: str, table: str = 'observations') -> Tuple[bool, str]:
        """Check if a record can be safely purged.
        
        Args:
            record_id: UUID to check
            table: Source table
            
        Returns:
            (can_purge, reason)
        """
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute(f"""
                SELECT 
                    o.*,
                    rc.durability,
                    rc.can_be_purged,
                    rc.class_name as rc_class
                FROM {table} o
                JOIN retention_classes rc ON rc.class_name = o.retention_class
                WHERE o.id = %s
            """, (record_id,))
            
            record = cur.fetchone()
            cur.close()
            self.memory._pool.putconn(conn)
            
            if not record:
                return False, "Record not found"
            
            # Protection checks
            if record.get('purge_protected'):
                return False, "Record is purge_protected"
            
            if record.get('pinned'):
                return False, "Record is pinned"
            
            if record.get('canonical'):
                return False, "Record is canonical"
            
            if record['retention_class'] in [
                'canonical', 'pinned', 'decision', 
                'procedure', 'preference', 'project_fact'
            ]:
                return False, f"Durable class: {record['retention_class']}"
            
            if not record['can_be_purged']:
                return False, f"Class cannot be purged: {record['retention_class']}"
            
            # Check if represented elsewhere
            if record.get('importance_score', 0) >= 0.7:
                if not (record.get('has_canonical_representation') or 
                        record.get('has_summary_representation')):
                    return False, "High importance with no representation"
            
            return True, "Safe to purge"
            
        except Exception as e:
            return False, f"Error checking: {e}"
    
    def purge_record(self, table: str, record_id: str, force: bool = False) -> bool:
        """Safely purge a single record.
        
        Args:
            table: Source table
            record_id: UUID to purge
            force: Skip safety checks (dangerous)
            
        Returns:
            True if purged
        """
        if not force:
            can_purge, reason = self.can_purge(record_id, table)
            if not can_purge:
                print(f"❌ Cannot purge {record_id}: {reason}")
                return False
        
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor()
            
            # Log the purge action
            cur.execute("""
                INSERT INTO retention_actions (
                    action_type, action_status, target_table, affected_ids,
                    records_purged, triggered_by, dry_run
                ) VALUES ('purge', 'completed', %s, ARRAY[%s], 1, 'system', FALSE)
            """, (table, record_id))
            
            # Delete the record
            cur.execute(f"DELETE FROM {table} WHERE id = %s", (record_id,))
            
            deleted = cur.rowcount
            conn.commit()
            cur.close()
            self.memory._pool.putconn(conn)
            
            if deleted > 0:
                print(f"✅ Purged {record_id} from {table}")
                return True
            else:
                print(f"⚠️  Record {record_id} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error purging {record_id}: {e}")
            return False
    
    def purge_candidates(self, dry_run: bool = True, limit: int = 1000) -> Dict:
        """Purge records that are eligible and safe to delete.
        
        Args:
            dry_run: If True, only show what would be purged
            limit: Maximum records to check
            
        Returns:
            Dict with results
        """
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT * FROM purge_candidates
                LIMIT %s
            """, (limit,))
            
            candidates = cur.fetchall()
            cur.close()
            self.memory._pool.putconn(conn)
            
            if not candidates:
                return {'purged': 0, 'candidates': 0, 'dry_run': dry_run}
            
            purged = 0
            protected = 0
            
            if not dry_run:
                for record in candidates:
                    if self.purge_record('observations', str(record['id'])):
                        purged += 1
            else:
                # In dry run, check which would actually be purged
                for record in candidates:
                    can_purge, reason = self.can_purge(str(record['id']))
                    if can_purge:
                        purged += 1
                    else:
                        protected += 1
            
            return {
                'purged': purged,
                'candidates': len(candidates),
                'protected': protected if dry_run else 0,
                'dry_run': dry_run,
                'sample': [dict(c) for c in candidates[:5]]
            }
            
        except Exception as e:
            print(f"❌ Error purging candidates: {e}")
            return {'purged': 0, 'candidates': 0, 'error': str(e)}
    
    # =========================================================================
    # CONSOLIDATION
    # =========================================================================
    
    def find_duplicates(self, days_back: int = 30, similarity_threshold: float = 0.8) -> List[Dict]:
        """Find potential duplicate observations.
        
        Args:
            days_back: Look back N days
            similarity_threshold: Minimum similarity (0-1)
            
        Returns:
            List of duplicate groups
        """
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            cur.execute("""
                SELECT 
                    o1.id as id1,
                    o2.id as id2,
                    o1.content as content1,
                    o2.content as content2,
                    similarity(o1.content, o2.content) as sim_score
                FROM observations o1
                JOIN observations o2 ON o1.id < o2.id
                WHERE o1.created_at > NOW() - INTERVAL '%s days'
                    AND o2.created_at > NOW() - INTERVAL '%s days'
                    AND o1.duplicate_of IS NULL
                    AND o2.duplicate_of IS NULL
                    AND similarity(o1.content, o2.content) > %s
                ORDER BY sim_score DESC
                LIMIT 100
            """, (days_back, days_back, similarity_threshold))
            
            duplicates = cur.fetchall()
            cur.close()
            self.memory._pool.putconn(conn)
            
            return [dict(d) for d in duplicates]
            
        except Exception as e:
            print(f"❌ Error finding duplicates: {e}")
            return []
    
    def consolidate_duplicates(self, duplicate_groups: List[Dict], dry_run: bool = True) -> Dict:
        """Consolidate duplicate observations.
        
        Args:
            duplicate_groups: From find_duplicates()
            dry_run: If True, only show what would be done
            
        Returns:
            Dict with results
        """
        consolidated = 0
        
        if dry_run:
            return {
                'consolidated': 0,
                'groups': len(duplicate_groups),
                'dry_run': True,
                'sample': duplicate_groups[:3] if duplicate_groups else []
            }
        
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor()
            
            for group in duplicate_groups:
                # Mark secondary as duplicate of primary
                cur.execute("""
                    UPDATE observations
                    SET duplicate_of = %s,
                        retention_class = 'duplicate',
                        updated_at = NOW()
                    WHERE id = %s
                """, (group['id1'], group['id2']))
                
                if cur.rowcount > 0:
                    consolidated += 1
            
            conn.commit()
            cur.close()
            self.memory._pool.putconn(conn)
            
            print(f"✅ Consolidated {consolidated} duplicates")
            
        except Exception as e:
            print(f"❌ Error consolidating: {e}")
        
        return {
            'consolidated': consolidated,
            'groups': len(duplicate_groups),
            'dry_run': dry_run
        }
    
    # =========================================================================
    # SIZE CONTROL
    # =========================================================================
    
    def get_database_size(self) -> Dict:
        """Get current database size information."""
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get total size
            cur.execute("""
                SELECT 
                    pg_database_size(current_database()) as total_bytes,
                    pg_size_pretty(pg_database_size(current_database())) as total_size
            """)
            
            size_info = cur.fetchone()
            
            # Get table sizes
            cur.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            tables = cur.fetchall()
            
            cur.close()
            self.memory._pool.putconn(conn)
            
            size_gb = size_info['total_bytes'] / (1024**3)
            
            return {
                'total_bytes': size_info['total_bytes'],
                'total_size': size_info['total_size'],
                'total_gb': round(size_gb, 2),
                'max_gb': self.policy.max_database_size_gb,
                'target_gb': self.policy.target_database_size_gb,
                'over_threshold': size_gb > self.policy.max_database_size_gb,
                'tables': [dict(t) for t in tables[:10]]
            }
            
        except Exception as e:
            print(f"❌ Error getting database size: {e}")
            return {}
    
    def check_size_pressure(self) -> Dict:
        """Check if database is under size pressure and recommend actions."""
        size_info = self.get_database_size()
        
        if not size_info:
            return {'error': 'Could not get size info'}
        
        current_gb = size_info['total_gb']
        max_gb = size_info['max_gb']
        target_gb = size_info['target_gb']
        
        if current_gb <= target_gb:
            return {
                'pressure': 'none',
                'current_gb': current_gb,
                'target_gb': target_gb,
                'recommended_action': 'none'
            }
        
        if current_gb <= max_gb:
            return {
                'pressure': 'warning',
                'current_gb': current_gb,
                'target_gb': target_gb,
                'max_gb': max_gb,
                'recommended_action': 'consolidate_and_archive',
                'message': f'Database at {current_gb:.1f}GB (target: {target_gb}GB)'
            }
        
        return {
            'pressure': 'critical',
            'current_gb': current_gb,
            'max_gb': max_gb,
            'recommended_action': 'purge_after_archive',
            'message': f'Database over max size: {current_gb:.1f}GB > {max_gb}GB'
        }
    
    # =========================================================================
    # RETENTION CYCLE
    # =========================================================================
    
    def run_retention_cycle(self, dry_run: bool = True) -> Dict:
        """Run a complete retention cycle.
        
        Escalation order:
        1. Consolidate duplicates
        2. Archive eligible records
        3. Purge archived low-value records
        
        Args:
            dry_run: If True, only show what would happen
            
        Returns:
            Dict with full results
        """
        print(f"\n🧹 Running retention cycle (dry_run={dry_run})\n")
        
        results = {
            'dry_run': dry_run,
            'started_at': datetime.now().isoformat(),
            'steps': {}
        }
        
        # Step 1: Consolidate duplicates
        print("Step 1: Consolidating duplicates...")
        duplicates = self.find_duplicates()
        if duplicates:
            results['steps']['consolidation'] = self.consolidate_duplicates(
                duplicates[:100],  # Limit to 100 groups
                dry_run=dry_run
            )
        else:
            results['steps']['consolidation'] = {'consolidated': 0, 'message': 'No duplicates found'}
        
        # Step 2: Update eligibility
        print("\nStep 2: Updating archive/delete eligibility...")
        try:
            conn = self.memory._pool.getconn()
            cur = conn.cursor()
            cur.execute("SELECT update_archive_eligibility()")
            cur.execute("SELECT update_delete_eligibility()")
            conn.commit()
            cur.close()
            self.memory._pool.putconn(conn)
            results['steps']['eligibility'] = {'status': 'updated'}
        except Exception as e:
            results['steps']['eligibility'] = {'status': 'error', 'error': str(e)}
        
        # Step 3: Archive
        print("\nStep 3: Archiving eligible records...")
        results['steps']['archive'] = self.archive_candidates(dry_run=dry_run)
        
        # Step 4: Check size pressure
        print("\nStep 4: Checking size pressure...")
        results['steps']['size_pressure'] = self.check_size_pressure()
        
        # Step 5: Purge (only if under pressure)
        if results['steps']['size_pressure'].get('pressure') in ['warning', 'critical']:
            print("\nStep 5: Purging safe candidates...")
            results['steps']['purge'] = self.purge_candidates(dry_run=dry_run)
        else:
            results['steps']['purge'] = {'purged': 0, 'message': 'No purge needed'}
        
        results['completed_at'] = datetime.now().isoformat()
        
        # Summary
        print("\n" + "="*50)
        print("RETENTION CYCLE COMPLETE")
        print("="*50)
        print(f"Dry run: {dry_run}")
        print(f"Consolidated: {results['steps']['consolidation'].get('consolidated', 0)}")
        print(f"Archived: {results['steps']['archive'].get('candidates', 0)} candidates")
        print(f"Purged: {results['steps']['purge'].get('candidates', 0)} candidates")
        print(f"Size: {results['steps']['size_pressure'].get('current_gb', 'N/A')} GB")
        
        return results


def main():
    """CLI for retention management."""
    import argparse
    
    parser = argparse.ArgumentParser(description='pg-memory Retention Manager')
    parser.add_argument('--stats', action='store_true', help='Show retention stats')
    parser.add_argument('--archive-candidates', action='store_true', help='Show archive candidates')
    parser.add_argument('--purge-candidates', action='store_true', help='Show purge candidates')
    parser.add_argument('--run-cycle', action='store_true', help='Run full retention cycle')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Dry run mode')
    parser.add_argument('--exec', action='store_true', help='Execute (not dry run)')
    
    args = parser.parse_args()
    
    dry_run = not args.exec
    
    manager = RetentionManager()
    
    if args.stats:
        size = manager.get_database_size()
        print(json.dumps(size, indent=2, default=str))
    
    elif args.archive_candidates:
        result = manager.archive_candidates(dry_run=True)
        print(json.dumps(result, indent=2, default=str))
    
    elif args.purge_candidates:
        result = manager.purge_candidates(dry_run=True)
        print(json.dumps(result, indent=2, default=str))
    
    elif args.run_cycle:
        result = manager.run_retention_cycle(dry_run=dry_run)
        print(json.dumps(result, indent=2, default=str))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
