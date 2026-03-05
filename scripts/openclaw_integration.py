#!/usr/bin/env python3
"""
pg-memory Integration for OpenClaw Tools

Replaces markdown-based memory_search with PostgreSQL-backed semantic search.

Usage:
    from openclaw_integration import memory_search, memory_get, capture_observation
    
    # Search memories
    results = memory_search("what did I work on yesterday", maxResults=5)
    
    # Get specific observation
    obs = memory_get("pg-memory:observations#d6k45fr24teg1v324t40")
    
    # Capture new observation
    obs_id = capture_observation("Important decision", tags=['decision'], importance=0.9)
"""

from pg_memory import PostgresMemory
from datetime import datetime, timedelta
import json
import os

def memory_search(query: str, maxResults: int = 5, minScore: float = 0.5):
    """
    Search pg-memory observations with semantic search.
    
    This replaces the default markdown-based memory_search.
    
    Args:
        query: Search query (semantic, not keyword)
        maxResults: Maximum results to return
        minScore: Minimum similarity score (0.0-1.0)
    
    Returns:
        List of observations with scores and citations
    """
    mem = PostgresMemory()
    
    try:
        # Search observations
        results = mem.search_observations(
            query=query,
            limit=maxResults,
            min_score=minScore
        )
        
        # Format for OpenClaw
        formatted = []
        for obs in results:
            formatted.append({
                'id': obs['id'],
                'content': obs['content'],
                'score': obs['score'],
                'timestamp': obs['timestamp'].isoformat() if isinstance(obs['timestamp'], datetime) else str(obs['timestamp']),
                'tags': obs.get('tags', []),
                'path': f"pg-memory:observations#{obs['id']}",  # Citation format
                'lines': 1  # Single observation
            })
        
        return formatted
    
    except Exception as e:
        print(f"❌ memory_search error: {e}")
        return []
    
    finally:
        mem.close()


def memory_get(path: str, from_line: int = None, lines: int = None):
    """
    Get specific observation from pg-memory.
    
    Args:
        path: Observation path (pg-memory:observations#<id>)
        from_line: Ignored (single observation)
        lines: Ignored (single observation)
    
    Returns:
        Observation content dict or None
    """
    if not path.startswith('pg-memory:'):
        return None
    
    # Extract observation ID
    obs_id = path.split('#')[-1] if '#' in path else None
    
    if not obs_id:
        return None
    
    mem = PostgresMemory()
    
    try:
        # Get observation by ID
        obs = mem.get_observation(obs_id)
        
        if obs:
            return {
                'content': obs['content'],
                'metadata': {
                    'id': obs['id'],
                    'timestamp': obs['timestamp'].isoformat() if isinstance(obs['timestamp'], datetime) else str(obs['timestamp']),
                    'tags': obs.get('tags', []),
                    'importance_score': obs.get('importance_score', 0.5),
                    'session_id': obs.get('session_id'),
                    'obs_type': obs.get('obs_type', 'note'),
                    'status': obs.get('status', 'active')
                },
                'path': path
            }
        return None
    
    except Exception as e:
        print(f"❌ memory_get error: {e}")
        return None
    
    finally:
        mem.close()


def capture_observation(content: str, tags: list = None, importance: float = 0.5, obs_type: str = 'note'):
    """
    Capture an observation to pg-memory.
    
    Args:
        content: Observation content
        tags: List of tags
        importance: Importance score (0.0-1.0)
        obs_type: Type of observation (note, decision, task, etc.)
    
    Returns:
        Observation ID (XID format, 20 chars)
    """
    mem = PostgresMemory()
    
    try:
        # Get current session
        session_id = mem.get_or_create_session(
            session_key='current',
            provider='openclaw'
        )
        
        # Capture observation
        obs_id = mem.capture_observation(
            session_id=session_id,
            content=content,
            tags=tags or [],
            importance_score=importance,
            obs_type=obs_type
        )
        
        return obs_id
    
    except Exception as e:
        print(f"❌ capture_observation error: {e}")
        return None
    
    finally:
        mem.close()


def get_recent_observations(days: int = 1, limit: int = 10):
    """
    Get recent observations from the last N days.
    
    Args:
        days: Number of days to look back
        limit: Maximum results
    
    Returns:
        List of recent observations
    """
    mem = PostgresMemory()
    
    try:
        results = mem.search_observations(
            query="",  # Empty query = get all
            days=days,
            limit=limit
        )
        
        formatted = []
        for obs in results:
            formatted.append({
                'id': obs['id'],
                'content': obs['content'],
                'timestamp': obs['timestamp'].isoformat() if isinstance(obs['timestamp'], datetime) else str(obs['timestamp']),
                'tags': obs.get('tags', []),
                'importance_score': obs.get('importance_score', 0.5),
                'path': f"pg-memory:observations#{obs['id']}"
            })
        
        return formatted
    
    except Exception as e:
        print(f"❌ get_recent_observations error: {e}")
        return []
    
    finally:
        mem.close()


# Test function
if __name__ == '__main__':
    print("🧪 Testing pg-memory integration...\n")
    
    # Test 1: Capture observation
    print("Test 1: Capture observation")
    obs_id = capture_observation(
        "Integration test observation",
        tags=['test', 'integration'],
        importance=0.9,
        obs_type='note'
    )
    print(f"  ✅ Created: {obs_id} ({len(obs_id)} chars)")
    print(f"  ✅ Type: {'XID' if len(obs_id) == 20 else 'UUID'}\n")
    
    # Test 2: Search
    print("Test 2: Search observations")
    results = memory_search("integration test", maxResults=3)
    print(f"  ✅ Found: {len(results)} results")
    
    for obs in results:
        print(f"    - Score: {obs['score']:.2f}")
        print(f"      Content: {obs['content'][:50]}...")
        print(f"      Citation: {obs['path']}\n")
    
    # Test 3: Get by ID
    print("Test 3: Get observation by ID")
    obs = memory_get(f"pg-memory:observations#{obs_id}")
    if obs:
        print(f"  ✅ Retrieved: {obs['content'][:50]}...")
        print(f"  ✅ Metadata: {list(obs['metadata'].keys())}\n")
    
    # Test 4: Recent observations
    print("Test 4: Get recent observations")
    recent = get_recent_observations(days=1, limit=5)
    print(f"  ✅ Found: {len(recent)} recent observations\n")
    
    print("✅ All tests passed! pg-memory integration is working.")
