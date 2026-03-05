#!/usr/bin/env python3
"""
OpenClaw Agent Memory Integration v3.0.0
Pre-compaction and Post-compaction handlers with Intelligent Context Management

Usage:
    # Pre-compaction (before context reset):
    python3 memory_handler.py pre-compaction
    
    # Post-compaction (after context reset):
    python3 memory_handler.py post-compaction [session_key]
    
    # Get context for a query:
    python3 memory_handler.py retrieve "what port is Rasa on?"
    
Configure with ~/.openclaw/workspace/config/memory.yaml
"""

import sys
import os
import json
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Add to path - works regardless of install location
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from pg_memory import PostgresMemory  # Updated to use pg_memory directly

# Default config path - override with MEMORY_CONFIG_PATH env var
CONFIG_PATH = os.environ.get('MEMORY_CONFIG_PATH', 
                              str(Path.home() / '.openclaw' / 'workspace' / 'config' / 'memory.yaml'))

def load_config() -> Dict:
    """Load memory configuration"""
    defaults = {
        'memory': {
            'primary_backend': 'postgresql',
            'markdown_backup': True,
            'retention_days': 7,
            'agent_id': 'arty',
            'fallback_on_pgdb_down': True
        },
        'postgresql': {
            'host': 'localhost',
            'port': 5432,
            'database': 'openclaw_memory',
            'user': 'postgres'
        }
    }
    
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                config = yaml.safe_load(f)
                # Merge with defaults
                merged = defaults.copy()
                merged.update(config)
                return merged
    except Exception as e:
        print(f"Config load failed: {e}, using defaults")
    
    return defaults

def get_memory() -> PostgresMemory:
    """Get configured memory instance (v3.0.0)"""
    # PostgresMemory uses environment variables, not constructor args
    import os
    config = load_config()
    
    # Set environment variables for PostgresMemory
    os.environ['PG_MEMORY_HOST'] = str(config['postgresql'].get('host', 'localhost'))
    os.environ['PG_MEMORY_PORT'] = str(config['postgresql'].get('port', 5432))
    os.environ['PG_MEMORY_DB'] = config['postgresql'].get('database', 'openclaw_memory')
    os.environ['PG_MEMORY_USER'] = config['postgresql'].get('user', 'postgres')
    if config['postgresql'].get('password'):
        os.environ['PG_MEMORY_PASSWORD'] = config['postgresql']['password']
    
    mem = PostgresMemory()
    return mem

def pre_compaction(context_data: Dict) -> bool:
    """
    V3.0.0: Called before OpenClaw context reset.
    Saves current session state + creates intelligent checkpoint.
    
    context_data should contain:
    {
        'session_key': 'uuid',
        'exchanges': [{...}],
        'observations': [{...}],
        'metadata': {...},
        'context_stats': {  # NEW: Context window metrics
            'current_tokens': 12500,
            'max_tokens': 16000,
            'compression_count': 2
        }
    }
    """
    try:
        mem = get_memory()
        
        session_key = context_data.get('session_key', 'unknown')
        
        # Get session_key from OpenClaw
        original_session_key = context_data.get('session_key', 'unknown')
        
        # Get instance identifier for prefixing (same logic as start_session)
        instance_identifier = os.getenv('OPENCLAW_INSTANCE_ID', str(mem.instance_id))
        prefixed_session_key = f"{instance_identifier[:8]}-{original_session_key}"
        
        # Start session and get session_id FIRST
        # NOTE: start_session() automatically prefixes with instance_id for multi-instance safety
        session_id = mem.start_session(
            session_key=original_session_key,  # Will be prefixed automatically
            provider=context_data.get('metadata', {}).get('provider'),
            channel_id=context_data.get('metadata', {}).get('channel_id'),
            user_id=context_data.get('metadata', {}).get('user', {}).get('id'),
            user_label=context_data.get('metadata', {}).get('user', {}).get('label')
        )
        
        # Save all exchanges using the PREFIXED session_key (to match what start_session created)
        for i, ex in enumerate(context_data.get('exchanges', [])):
            mem.save_exchange(
                session_key=prefixed_session_key,  # Use prefixed key to match session
                exchange_number=i + 1,
                user_message=ex.get('user_message', ''),
                assistant_response=ex.get('assistant_response', ''),
                assistant_thinking=ex.get('thinking', ''),
                tool_calls=ex.get('tool_calls', []),
                user_metadata=ex.get('metadata', {})
            )
        
        # V3.0.0: Extract and log decisions from observations
        decisions_created = 0
        for obs in context_data.get('observations', []):
            try:
                mem.capture_observation(
                    session_id=session_id,
                    content=obs.get('content', ''),
                    tags=obs.get('tags', []),
                    importance_score=obs.get('importance', 0.5),
                    source=obs.get('type', 'manual')
                )
                
                # If it's a decision-type observation, log it structured
                if obs.get('type') == 'decision':
                    mem.log_decision(
                        session_id=session_id,
                        title=obs.get('title', 'Decision'),
                        description=obs.get('content', ''),
                        decision_type=obs.get('decision_type', 'general'),
                        rationale=obs.get('rationale', ''),
                        impact_level=obs.get('impact', 'medium'),
                        requires_followup=obs.get('requires_followup', False),
                        followup_date=datetime.fromisoformat(obs['followup_date']) if obs.get('followup_date') else None,
                        tags=obs.get('tags', [])
                    )
                    decisions_created += 1
            except Exception as e:
                print(f"⚠️  Failed to capture observation: {e}")
                # Continue with next observation
        
        # V3.0.0: AUTO-GENERATE SUMMARY before compaction (TIERED approach)
        exchanges = context_data.get('exchanges', [])
        num_exchanges = len(exchanges)
        summary_created = False
        
        # Tiered summary generation based on session length
        if num_exchanges >= 30:  # Major session (45-60+ min)
            min_importance = 0.5
            time_window = timedelta(hours=6)
            summary_type = 'comprehensive'
            should_summarize = True
            
        elif num_exchanges >= 15:  # Standard session (20-45 min)
            min_importance = 0.6
            time_window = timedelta(hours=4)
            summary_type = 'standard'
            should_summarize = True
            
        elif num_exchanges >= 8:  # Minimal session (10-20 min)
            min_importance = 0.7
            time_window = timedelta(hours=2)
            summary_type = 'brief'
            should_summarize = True
            
        else:
            # Skip summary - too short (< 10 exchanges = quick chat)
            should_summarize = False
        
        if should_summarize:
            try:
                summary_id = mem.generate_summary(
                    from_date=datetime.now() - time_window,
                    min_importance=min_importance
                )
                summary_created = True
                print(f"   📝 Auto-generated {summary_type} summary ({num_exchanges} exchanges, ID: {summary_id})")
            except Exception as e:
                print(f"   ⚠️  {summary_type} summary generation skipped: {e}")
                summary_created = False
        
        # V3.0.0: Create context checkpoint BEFORE compaction
        context_stats = context_data.get('context_stats', {})
        checkpoint_summary = _generate_checkpoint_summary(context_data)
        
        # Include summary reference in checkpoint if created
        if summary_created:
            checkpoint_summary += f" [Summary auto-generated]"
        
        try:
            checkpoint_id = mem.create_checkpoint(
                session_id=session_id,  # Use session_id, not session_key!
                checkpoint_type='auto',
                title=f'Pre-Compaction Checkpoint #{context_stats.get("compression_count", 0) + 1}',
                summary_content=checkpoint_summary,
                key_decisions=_extract_decisions(context_data),
                open_tasks=_extract_open_tasks(context_data),
                important_context=_extract_important_context(context_data)
            )
        except Exception as e:
            print(f"⚠️  Checkpoint creation failed: {e}")
            print(f"   Session ID: {session_id}")
            # Verify session exists
            with mem._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM sessions WHERE id = %s", (session_id,))
                    row = cur.fetchone()
                    print(f"   Session exists in DB: {row is not None}")
            checkpoint_id = None
            # Continue anyway - checkpoint is nice-to-have, not critical
        
        # V3.0.0: Log context state
        if context_stats:
            mem.log_context_state(
                session_id=session_id,
                current_tokens=context_stats.get('current_tokens', 0),
                max_tokens=context_stats.get('max_tokens', 16000),
                compression_count=context_stats.get('compression_count', 0),
                oldest_accessible_timestamp=context_stats.get('oldest_accessible'),
                metadata={'checkpoint_id': str(checkpoint_id)}
            )
        
        # Prune old markdown
        try:
            pruned = mem.prune_old_observations(days=7)
            if pruned > 0:
                print(f"   Pruned {pruned} old markdown files")
        except (AttributeError, NameError, TypeError):
            # Method might not exist in this version
            pass
        
        mem.end_session(session_key)
        mem.close()
        
        # Build summary status message
        if summary_created:
            summary_msg = f" + {summary_type} summary"
        else:
            summary_msg = ""
        
        print(f"✅ Pre-compaction v3.0.0: Session saved{summary_msg} + checkpoint created ({decisions_created} decisions logged)")
        
        # Also write minimal context marker (for post-compaction verification)
        marker_path = '/tmp/last_compaction_marker.json'
        with open(marker_path, 'w') as f:
            json.dump({
                'session_key': session_key,
                'timestamp': datetime.now().isoformat(),
                'agent': context_data.get('metadata', {}).get('user', {}).get('label', 'unknown'),
                'checkpoint_id': str(checkpoint_id),
                'decisions_logged': decisions_created
            }, f)
        
        return True
        
    except Exception as e:
        print(f"⚠️  Pre-compaction v3.0.0 failed: {e}")
        # Fallback to just markdown write
        return _emergency_markdown_write(context_data)

def _generate_checkpoint_summary(context_data: Dict) -> str:
    """Generate a concise summary for the checkpoint."""
    exchanges = context_data.get('exchanges', [])
    observations = context_data.get('observations', [])
    
    summary_parts = []
    
    # Count exchanges
    if exchanges:
        summary_parts.append(f"Session had {len(exchanges)} exchanges.")
    
    # Key topics from observations
    if observations:
        topics = list(set(obs.get('tags', ['general'])[0] if obs.get('tags') else 'general' 
                         for obs in observations[:5]))
        summary_parts.append(f"Key topics: {', '.join(topics)}.")
    
    # Decisions made
    decisions = [obs for obs in observations if obs.get('type') == 'decision']
    if decisions:
        summary_parts.append(f"{len(decisions)} decisions made.")
    
    return ' '.join(summary_parts) if summary_parts else "Regular session checkpoint."

def _extract_decisions(context_data: Dict) -> List[Dict]:
    """Extract key decisions from context."""
    decisions = []
    for obs in context_data.get('observations', []):
        if obs.get('type') == 'decision':
            decisions.append({
                'title': obs.get('title', 'Decision'),
                'rationale': obs.get('rationale', obs.get('content', ''))
            })
    return decisions[:5]  # Top 5

def _extract_open_tasks(context_data: Dict) -> List[Dict]:
    """Extract open tasks from context."""
    tasks = []
    for obs in context_data.get('observations', []):
        if obs.get('type') == 'task' and obs.get('status') != 'complete':
            tasks.append({
                'task': obs.get('title', 'Task'),
                'status': obs.get('status', 'pending')
            })
    return tasks[:5]

def _extract_important_context(context_data: Dict) -> List[Dict]:
    """Extract critical context to preserve."""
    context = []
    for obs in context_data.get('observations', []):
        if obs.get('importance', 0) >= 0.8:
            context.append({
                'fact': obs.get('content', '')[:200],
                'importance': obs.get('importance')
            })
    return context[:5]

def _emergency_markdown_write(context_data: Dict) -> bool:
    """Emergency fallback when PostgreSQL is down"""
    try:
        config = load_config()
        markdown_dir = os.path.expanduser(
            config['memory'].get('markdown_dir', '~/.openclaw/workspace/memory')
        )
        
        if not os.path.exists(markdown_dir):
            os.makedirs(markdown_dir, exist_ok=True)
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(markdown_dir, f"{date_str}.md")
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"\n## EMERGENCY BACKUP ({datetime.now().strftime('%H:%M:%S')})\n")
            f.write(f"Session: {context_data.get('session_key', 'unknown')}\n\n")
            
            for obs in context_data.get('observations', []):
                f.write(f"### {obs.get('title', 'Observation')}\n")
                f.write(f"{obs.get('content', '')}\n\n")
        
        print("   ✅ Emergency save to markdown successful")
        return True
        
    except Exception as e2:
        print(f"   ❌ Emergency save failed: {e2}")
        return False

def post_compaction(session_key: Optional[str] = None) -> Dict:
    """
    V3.0.0: Called after OpenClaw context reset.
    Retrieves intelligent context (anchors + working memory + recent).
    
    Returns:
    {
        'session_key': 'uuid',
        'recent_exchanges': [...],
        'observations': [...],
        'context_anchors': [...],  # NEW: Always-loaded info
        'working_memory': [...],   # NEW: Fast-access cache
        'full_context': '...',     # NEW: Assembled context string
        'last_session_summary': '...',
        'status': 'ok' | 'fallback'
    }
    """
    try:
        mem = get_memory()
        
        result = {
            'session_key': session_key or 'new_session',
            'recent_exchanges': [],
            'observations': [],
            'context_anchors': [],
            'working_memory': [],
            'full_context': '',
            'last_session_summary': None,
            'status': 'ok'
        }
        
        # V3.0.0: Get session ID from session_key
        session_id = session_key
        if not session_id:
            # Get most recent session
            with mem._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM sessions 
                        ORDER BY started_at DESC 
                        LIMIT 1
                    """)
                    row = cur.fetchone()
                    session_id = row[0] if row else None
        
        if session_id:
            # V3.0.0: Get context anchors (always-loaded critical info)
            anchors = mem.get_context_anchors(session_id)
            result['context_anchors'] = anchors
            
            # V3.0.0: Get working memory cache (priority-ordered)
            working = mem.get_working_memory(session_id, limit=20)
            result['working_memory'] = working
            
            # V3.0.0: Assemble full context (anchors + working memory)
            full_context = mem.get_full_context(session_id, max_tokens=4000)
            result['full_context'] = full_context
            
            # Get recent exchanges from this session
            exchanges = mem.search_exchanges('', days=1, limit=20)
            result['recent_exchanges'] = exchanges
            
            # Get high-importance recent observations (use importance_score not min_importance)
            obs = mem.get_recent_observations(hours=24, limit=20)
            # Filter by importance manually
            result['observations'] = [o for o in obs if o.get('importance_score', 0) >= 0.7][:10]
            
            # V3.0.0: Get latest checkpoint summary
            with mem._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT summary_content 
                        FROM context_checkpoints 
                        WHERE session_id = %s 
                        ORDER BY checkpoint_number DESC 
                        LIMIT 1
                    """, (session_id,))
                    row = cur.fetchone()
                    if row:
                        result['last_session_summary'] = row[0]
        
        # Get stats
        result['stats'] = mem.get_memory_stats()
        
        mem.close()
        
        print(f"✅ Post-compaction v3.0.0: Loaded {len(result['context_anchors'])} anchors, " +
              f"{len(result['working_memory'])} cache entries, {len(result['observations'])} observations")
        return result
        
    except Exception as e:
        print(f"⚠️  Post-compaction v3.0.0 failed: {e}")
        # Return minimal fallback
        return {
            'session_key': session_key or 'new_session',
            'recent_exchanges': [],
            'observations': [],
            'context_anchors': [],
            'working_memory': [],
            'full_context': '',
            'last_session_summary': None,
            'status': 'fallback',
            'error': str(e)
        }

def retrieve_context(query: str, days: int = 7) -> List[Dict]:
    """
    Proactive context retrieval during conversation.
    Called when user asks about past information.
    """
    try:
        mem = get_memory()
        
        # Search for relevant observations
        results = mem.search(query, days=days, min_importance=0.3)
        
        if not results or len(results) < 3:
            # Also search raw exchanges for full context
            exchanges = mem.search_exchanges(query, days=days, limit=5)
            results.extend(exchanges)
        
        mem.close()
        return results
        
    except Exception as e:
        print(f"Context retrieval failed: {e}")
        return []

def main():
    if len(sys.argv) < 2:
        print("Usage: memory_handler.py [pre-compaction|post-compaction|retrieve] [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'pre-compaction':
        # Read context data from stdin (JSON)
        try:
            context_data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except:
            context_data = {}
        
        success = pre_compaction(context_data)
        sys.exit(0 if success else 1)
    
    elif command == 'post-compaction':
        session_key = sys.argv[2] if len(sys.argv) > 2 else None
        result = post_compaction(session_key)
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)
    
    elif command == 'retrieve':
        query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
        days = 7
        
        # Parse --days if provided
        for i, arg in enumerate(sys.argv):
            if arg == '--days' and i + 1 < len(sys.argv):
                try:
                    days = int(sys.argv[i + 1])
                except:
                    pass
        
        results = retrieve_context(query, days=days)
        print(json.dumps(results, indent=2, default=str))
        sys.exit(0)
    
    elif command == 'stats':
        mem = get_memory()
        stats = mem.stats()
        print(json.dumps(stats, indent=2, default=str))
        mem.close()
        sys.exit(0)
    
    elif command == 'prune':
        mem = get_memory()
        pruned = mem.prune_old_markdown()
        print(f"Pruned {pruned} old markdown files")
        mem.close()
        sys.exit(0)
    
    else:
        print(f"Unknown command: {command}")
        print("Commands: pre-compaction, post-compaction, retrieve, stats, prune")
        sys.exit(1)

if __name__ == '__main__':
    main()
