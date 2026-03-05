#!/usr/bin/env python3
"""
pg-memory v3.0.0 - Automated Test Suite
Run: python3 -m pytest tests/ -v
"""

import sys
import os
import uuid
from pathlib import Path

# Add scripts to path
script_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(script_dir))

from pg_memory import PostgresMemory, generate_id
from xid import Xid

class TestPGMemory:
    """Test pg-memory functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        os.environ['PG_MEMORY_DEBUG'] = '1'
        self.mem = PostgresMemory()
        # Initialize connection pool
        self.mem._get_connection().__enter__()
        self.test_session_key = f"test-{uuid.uuid4().hex[:8]}"
        
    def teardown_method(self):
        """Clean up after tests"""
        self.mem.close()
    
    def test_01_xid_generation(self):
        """Test XID ID generation"""
        id1 = generate_id()
        id2 = generate_id()
        
        assert len(id1) == 20, f"Expected XID (20 chars), got {len(id1)}"
        assert len(id2) == 20, f"Expected XID (20 chars), got {len(id2)}"
        assert id1 != id2, "XIDs should be unique"
        print(f"✅ XID generation: {id1}")
    
    def test_02_session_creation(self):
        """Test session creation with XID"""
        session_id = self.mem.start_session(
            session_key=self.test_session_key,
            provider='test',
            user_label='TestUser'
        )
        
        assert len(session_id) == 20, f"Expected XID session (20 chars), got {len(session_id)}"
        print(f"✅ Session created: {session_id}")
    
    def test_03_observation_capture(self):
        """Test observation capture"""
        session_id = self.mem.start_session(
            session_key=f"{self.test_session_key}-obs",
            provider='test'
        )
        
        obs_id = self.mem.capture_observation(
            session_id=session_id,
            content="Test observation for automated testing",
            tags=["test", "automated"],
            importance_score=0.5
        )
        
        assert obs_id is not None, "Observation ID should not be None"
        print(f"✅ Observation captured: {obs_id[:20]}...")
    
    def test_04_natural_language_query(self):
        """Test natural language queries"""
        # Capture a test observation first
        session_id = self.mem.start_session(
            session_key=f"{self.test_session_key}-nl",
            provider='test'
        )
        
        self.mem.capture_observation(
            session_id=session_id,
            content="pg-memory is a PostgreSQL-based memory system for OpenClaw",
            tags=["pg-memory", "definition"],
            importance_score=0.9
        )
        
        # Query it
        results = self.mem.natural_query("what is pg-memory?")
        
        assert len(results) > 0, "Should find at least one result"
        print(f"✅ NL Query found {len(results)} result(s)")
    
    def test_05_semantic_search(self):
        """Test semantic search"""
        results = self.mem.search_observations(
            query="memory system",
            limit=5
        )
        
        assert isinstance(results, list), "Results should be a list"
        print(f"✅ Semantic search found {len(results)} result(s)")
    
    def test_06_multi_instance_safety(self):
        """Test multi-instance session isolation"""
        # Create session with instance A prefix
        session_a = self.mem.start_session(
            session_key="shared-channel",
            provider='test'
        )
        
        # Verify it has instance prefix
        with self.mem._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT session_key FROM sessions WHERE id = %s", (session_a,))
                key = cur.fetchone()[0]
                
        assert '-' in key, f"Session key should be prefixed: {key}"
        assert len(key.split('-')[0]) == 8, f"Instance prefix should be 8 chars: {key}"
        print(f"✅ Multi-instance safety: {key}")
    
    def test_07_database_stats(self):
        """Test database statistics"""
        with self.mem._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sessions")
                sessions = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM observations")
                observations = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM raw_exchanges")
                exchanges = cur.fetchone()[0]
        
        assert sessions >= 0, "Sessions count should be non-negative"
        assert observations >= 0, "Observations count should be non-negative"
        print(f"✅ Database stats: {sessions} sessions, {observations} observations, {exchanges} exchanges")

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])
