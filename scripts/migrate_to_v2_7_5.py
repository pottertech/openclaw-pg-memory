#!/usr/bin/env python3
"""
v3.0.0 Migration Script - Context Management Features

Applies schema changes and creates helper functions for:
- Context checkpoints
- Decision logging
- Working memory cache
- Context anchors
- Conversation segments
- Context state tracking

Usage:
    python3 scripts/migrate_to_v2_7_5.py
"""

import sys
import os
import psycopg2
from pathlib import Path

# Get database connection from environment or defaults
DB_HOST = os.getenv('PG_MEMORY_HOST', 'localhost')
DB_PORT = os.getenv('PG_MEMORY_PORT', '5432')
DB_NAME = os.getenv('PG_MEMORY_DB', 'openclaw_memory')
DB_USER = os.getenv('PG_MEMORY_USER', os.getenv('USER', 'postgres'))
DB_PASS = os.getenv('PG_MEMORY_PASSWORD', '')

def get_connection():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        print(f"✅ Connected to {DB_NAME}@{DB_HOST}")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

def apply_schema(conn, schema_file: str) -> bool:
    """Apply schema file to database."""
    schema_path = Path(__file__).parent / schema_file
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    print(f"\n📄 Applying {schema_file}...")
    
    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        
        conn.commit()
        print(f"✅ Schema applied successfully")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Schema application failed: {e}")
        return False

def verify_tables(conn) -> bool:
    """Verify all v3.0.0 tables exist."""
    expected_tables = [
        'context_checkpoints',
        'decision_log',
        'working_memory_cache',
        'context_anchors',
        'conversation_segments',
        'context_state_log',
        'memory_consolidation_log'
    ]
    
    print("\n🔍 Verifying tables...")
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
        """)
        existing = [row[0] for row in cur.fetchall()]
    
    all_present = True
    for table in expected_tables:
        if table in existing:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} - MISSING")
            all_present = False
    
    return all_present

def verify_functions(conn) -> bool:
    """Verify all v3.0.0 functions exist."""
    expected_functions = [
        'touch_working_memory',
        'prune_expired_working_memory',
        'calculate_temporal_importance',
        'get_session_anchors',
        'get_working_memory'
    ]
    
    print("\n🔍 Verifying functions...")
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'public' 
              AND routine_type = 'FUNCTION'
        """)
        existing = [row[0] for row in cur.fetchall()]
    
    all_present = True
    for func in expected_functions:
        if func in existing:
            print(f"  ✅ {func}()")
        else:
            print(f"  ❌ {func}() - MISSING")
            all_present = False
    
    return all_present

def main():
    """Run v3.0.0 migration."""
    print("=" * 70)
    print("pg-memory v3.0.0 Migration")
    print("=" * 70)
    print(f"\nTarget: {DB_NAME}@{DB_HOST}")
    print(f"User: {DB_USER}")
    
    # Connect
    conn = get_connection()
    
    # Apply schema
    success = apply_schema(conn, 'schema_v2_7_5_context_management.sql')
    
    if not success:
        print("\n❌ Migration failed!")
        sys.exit(1)
    
    # Verify
    tables_ok = verify_tables(conn)
    functions_ok = verify_functions(conn)
    
    print("\n" + "=" * 70)
    if tables_ok and functions_ok:
        print("✅ Migration COMPLETE! v3.0.0 is ready.")
        print("\nNew Features:")
        print("  • Context Checkpoints - Conversation summary points")
        print("  • Decision Log - Structured decision tracking")
        print("  • Working Memory Cache - Fast-access context")
        print("  • Context Anchors - Always-loaded critical info")
        print("  • Conversation Segments - Topic-based chunking")
        print("  • Context State Tracking - Real-time utilization metrics")
        print("\nNext Steps:")
        print("  1. Update your code to use new methods:")
        print("     - m.create_checkpoint()")
        print("     - m.log_decision()")
        print("     - m.add_to_working_memory()")
        print("     - m.add_context_anchor()")
        print("     - m.get_full_context()")
        print("  2. Review OPENCLAW_SETUP.md for integration examples")
        print("  3. Monitor with m.get_memory_stats()")
    else:
        print("⚠️  Migration completed with warnings")
        print("Some tables or functions may be missing.")
        print("Check the errors above.")
    print("=" * 70)
    
    conn.close()

if __name__ == '__main__':
    main()
