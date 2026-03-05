#!/usr/bin/env python3
"""
Final XID Migration - Handle Views
Migrates remaining base tables with view dependencies
"""

import psycopg2
import os

db_name = os.getenv('PG_MEMORY_DB', 'openclaw_memory')
db_user = os.getenv('PG_MEMORY_DB_USER', os.getenv('USER', 'openclaw'))

conn = psycopg2.connect(
    host='localhost',
    database=db_name,
    user=db_user
)
conn.autocommit = True

print("=" * 80)
print("FINAL XID MIGRATION - HANDLING VIEW DEPENDENCIES")
print("=" * 80)

# Views to drop and recreate
VIEWS_TO_DROP = [
    'decision_followup_queue',
    'instance_stats',
    'observations_search',
    'memory_stats',
    'performance_stats',
]

# Get view definitions
view_definitions = {}

with conn.cursor() as cur:
    print("\n1. Saving view definitions...")
    for view in VIEWS_TO_DROP:
        cur.execute("""
            SELECT definition 
            FROM pg_views 
            WHERE schemaname = 'public' 
            AND viewname = %s
        """, (view,))
        row = cur.fetchone()
        if row:
            view_definitions[view] = row[0]
            print(f"   ✅ {view} definition saved")
        else:
            print(f"   ⚠️  {view} not found in pg_views")
    
    print("\n2. Dropping views...")
    for view in VIEWS_TO_DROP:
        try:
            cur.execute(f"DROP VIEW IF EXISTS {view} CASCADE")
            print(f"   ✅ {view} dropped")
        except Exception as e:
            print(f"   ⚠️  {view}: {str(e)[:50]}")
    
    print("\n3. Migrating base tables...")
    
    # Migrate decision_log
    print(f"\n   MIGRATING: decision_log")
    try:
        cur.execute("""
            ALTER TABLE decision_log 
            ALTER COLUMN id TYPE TEXT,
            ALTER COLUMN session_id TYPE TEXT
        """)
        print(f"      ✅ Columns converted to TEXT")
    except Exception as e:
        print(f"      ⚠️  {e}")
    
    # Migrate observations
    print(f"\n   MIGRATING: observations")
    try:
        cur.execute("""
            ALTER TABLE observations 
            ALTER COLUMN id TYPE TEXT,
            ALTER COLUMN instance_id TYPE TEXT
        """)
        print(f"      ✅ Columns converted to TEXT")
    except Exception as e:
        print(f"      ⚠️  {e}")
    
    print("\n4. Recreating views...")
    for view, definition in view_definitions.items():
        try:
            # Recreate view
            cur.execute(f"CREATE VIEW {view} AS {definition}")
            print(f"   ✅ {view} recreated")
        except Exception as e:
            print(f"   ⚠️  {view}: {str(e)[:50]}")

conn.commit()

# Final check
print("\n" + "=" * 80)
print("FINAL VERIFICATION...")
print("=" * 80)

with conn.cursor() as cur:
    cur.execute("""
        SELECT COUNT(*) 
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND data_type = 'uuid'
        AND table_type = 'BASE TABLE'
    """)
    count = cur.fetchone()[0]
    
    if count == 0:
        print("\n🎉 SUCCESS! NO UUID COLUMNS IN BASE TABLES!")
        print("✅ Full XID schema migration 100% complete")
    else:
        print(f"\n⚠️  {count} UUID columns still remain in base tables")
    
    # Check views
    cur.execute("""
        SELECT COUNT(*) 
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND data_type = 'uuid'
        AND table_name IN (
            SELECT viewname FROM pg_views WHERE schemaname = 'public'
        )
    """)
    view_count = cur.fetchone()[0]
    
    if view_count > 0:
        print(f"ℹ️  {view_count} UUID columns in views (expected - views reflect base tables)")

conn.close()
print("\n" + "=" * 80)
