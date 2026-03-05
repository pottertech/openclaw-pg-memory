#!/usr/bin/env python3
"""
Migrate Markdown Memory Files to pg-memory

Imports all daily markdown files into PostgreSQL as observations.
"""

from pg_memory import PostgresMemory
from pathlib import Path
from datetime import datetime
import re

def migrate_markdown_to_pgmemory():
    """Migrate all markdown memory files to pg-memory."""
    
    memory_dir = Path.home() / '.openclaw' / 'workspace' / 'memory'
    
    if not memory_dir.exists():
        print(f"❌ Memory directory not found: {memory_dir}")
        return
    
    print("🦞 Markdown to pg-memory Migration")
    print("=" * 50)
    print()
    
    # Initialize pg-memory
    mem = PostgresMemory()
    print(f"✅ Connected to pg-memory")
    print(f"✅ Instance: {mem.instance_id[:8]}...")
    print()
    
    # Create migration session
    session_id = mem.start_session(
        session_key='markdown-migration',
        provider='migration',
        user_label='system'
    )
    print(f"✅ Migration session: {session_id}")
    print()
    
    # Find all daily files (exclude archive, working-buffer, index files)
    daily_files = []
    for f in memory_dir.glob('20*.md'):
        if 'working-buffer' in f.name or 'INDEX' in f.name:
            continue
        daily_files.append(f)
    
    # Sort by date (oldest first)
    daily_files.sort(key=lambda x: x.name)
    
    print(f"📁 Found {len(daily_files)} daily files to migrate")
    print()
    
    migrated = 0
    failed = 0
    
    for md_file in daily_files:
        try:
            print(f"📄 Migrating: {md_file.name}...")
            
            # Read content
            content = md_file.read_text()
            
            # Extract date from filename
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})', md_file.name)
            file_date = date_match.group(1) if date_match else 'unknown'
            
            # Capture as observation
            obs_id = mem.capture_observation(
                session_id=session_id,
                content=content,
                tags=['imported', 'markdown', 'daily-log', file_date],
                importance_score=0.7,
                metadata={
                    'source_file': str(md_file),
                    'source_filename': md_file.name,
                    'import_date': datetime.now().isoformat(),
                    'import_type': 'markdown_migration',
                    'file_date': file_date
                }
            )
            
            print(f"   ✅ Created observation: {obs_id}")
            migrated += 1
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed += 1
    
    print()
    print("=" * 50)
    print("📊 Migration Summary")
    print("=" * 50)
    print(f"✅ Migrated: {migrated} files")
    print(f"❌ Failed: {failed} files")
    print(f"📈 Total: {migrated + failed} files")
    print()
    
    # Verify migration
    print("🔍 Verifying migration...")
    results = mem.search_observations(
        query="markdown migration daily log",
        tags=['imported', 'markdown'],
        limit=5
    )
    print(f"✅ Search test: Found {len(results)} migrated observations")
    print()
    
    mem.close()
    print("✅ Migration complete!")
    print()
    print("Next steps:")
    print("1. Restart OpenClaw: openclaw gateway restart")
    print("2. Test memory_search: Ask 'what did I work on last week?'")
    print("3. Verify citations show pg-memory:observations#<xid>")

if __name__ == '__main__':
    migrate_markdown_to_pgmemory()
