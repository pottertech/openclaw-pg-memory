#!/usr/bin/env python3
"""
pg-memory v3.1.0 - Automated Test Suite
Run: python3 tests/run_tests.py
"""

import sys
import os
from pathlib import Path

# Add scripts to path
script_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(script_dir))

os.environ['PG_MEMORY_DEBUG'] = '0'

from pg_memory import PostgresMemory, generate_id
from xid import Xid

def reset_singleton():
    """Reset PostgresMemory singleton for test isolation"""
    PostgresMemory._instance = None
    PostgresMemory._initialized = False

def test_xid_generation():
    """Test XID ID generation"""
    print("\n📝 Test 1: XID Generation")
    id1 = generate_id()
    id2 = generate_id()
    
    assert len(id1) == 20, f"Expected XID (20 chars), got {len(id1)}"
    assert len(id2) == 20, f"Expected XID (20 chars), got {len(id2)}"
    assert id1 != id2, "XIDs should be unique"
    print(f"   ✅ XID generation: {id1}")
    return True

def test_session_creation():
    """Test session creation with XID"""
    print("\n📝 Test 2: Session Creation")
    reset_singleton()
    mem = PostgresMemory()
    session_id = mem.start_session(
        session_key="test-session",
        provider='test',
        user_label='TestUser'
    )
    
    assert len(session_id) == 20, f"Expected XID session (20 chars), got {len(session_id)}"
    print(f"   ✅ Session created: {session_id}")
    mem.close()
    return True

def test_observation_capture():
    """Test observation capture"""
    print("\n📝 Test 3: Observation Capture")
    reset_singleton()
    mem = PostgresMemory()
    session_id = mem.start_session(
        session_key="test-obs",
        provider='test'
    )
    
    obs_id = mem.capture_observation(
        session_id=session_id,
        content="Test observation for automated testing",
        tags=["test", "automated"],
        importance_score=0.5
    )
    
    assert obs_id is not None, "Observation ID should not be None"
    print(f"   ✅ Observation captured: {obs_id[:20]}...")
    mem.close()
    return True

def test_natural_language_query():
    """Test natural language queries"""
    print("\n📝 Test 4: Natural Language Query")
    reset_singleton()
    mem = PostgresMemory()
    session_id = mem.start_session(
        session_key="test-nl",
        provider='test'
    )
    
    mem.capture_observation(
        session_id=session_id,
        content="pg-memory is a PostgreSQL-based memory system for OpenClaw",
        tags=["pg-memory", "definition"],
        importance_score=0.9
    )
    
    results = mem.natural_query("what is pg-memory?")
    # NLQueryResult object has .results attribute
    if hasattr(results, 'results'):
        results_list = results.results
    elif hasattr(results, '__iter__') and not isinstance(results, str):
        results_list = list(results)
    else:
        results_list = results
    
    assert len(results_list) > 0, "Should find at least one result"
    print(f"   ✅ NL Query found {len(results_list)} result(s)")
    mem.close()
    return True

def test_semantic_search():
    """Test semantic search"""
    print("\n📝 Test 5: Semantic Search")
    reset_singleton()
    mem = PostgresMemory()
    
    results = mem.search_observations(
        query="memory system",
        limit=5
    )
    
    assert isinstance(results, list), "Results should be a list"
    print(f"   ✅ Semantic search found {len(results)} result(s)")
    mem.close()
    return True

def test_multi_instance_safety():
    """Test multi-instance session isolation"""
    print("\n📝 Test 6: Multi-Instance Safety")
    reset_singleton()
    mem = PostgresMemory()
    
    session_id = mem.start_session(
        session_key="shared-channel",
        provider='test'
    )
    
    with mem._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT session_key FROM sessions WHERE id = %s", (session_id,))
            key = cur.fetchone()[0]
    
    assert '-' in key, f"Session key should be prefixed: {key}"
    assert len(key.split('-')[0]) == 8, f"Instance prefix should be 8 chars: {key}"
    print(f"   ✅ Multi-instance safety: {key}")
    mem.close()
    return True

def test_database_stats():
    """Test database statistics"""
    print("\n📝 Test 7: Database Statistics")
    reset_singleton()
    mem = PostgresMemory()
    
    with mem._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sessions")
            sessions = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM observations")
            observations = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM raw_exchanges")
            exchanges = cur.fetchone()[0]
    
    assert sessions >= 0, "Sessions count should be non-negative"
    print(f"   ✅ Database stats: {sessions} sessions, {observations} observations, {exchanges} exchanges")
    mem.close()
    return True

if __name__ == '__main__':
    print("=" * 70)
    print("PG-MEMORY v3.1.0 - AUTOMATED TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("XID Generation", test_xid_generation),
        ("Session Creation", test_session_creation),
        ("Observation Capture", test_observation_capture),
        ("Natural Language Query", test_natural_language_query),
        ("Semantic Search", test_semantic_search),
        ("Multi-Instance Safety", test_multi_instance_safety),
        ("Database Statistics", test_database_stats),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {name} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    sys.exit(0 if failed == 0 else 1)
