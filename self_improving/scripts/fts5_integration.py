#!/usr/bin/env python3
"""
FTS5 ↔ Self-Improving Integration Module
Bidirectional sync between conversation history and learning memory.

Design Principles (from Agentic Harness Patterns):
1. TWO-STEP SAVE: Log to FTS5 first, then update memory file
2. MUTUAL EXCLUSION: Track when main agent writes to prevent extraction conflicts
"""

import os
import sys
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from contextmanager import contextmanager

# Try to import FTS5
FTS5_AVAILABLE = False
try:
    sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/fts5"))
    from skills.fts5 import search, summarize, add_message
    FTS5_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    # Try alternative path
    try:
        sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/fts5"))
        from __init__ import search, summarize, add_message
        FTS5_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        pass


# Paths - Support both original ~/self-improving/ and merged location
from pathlib import Path

_SCRIPT_DIR = Path(__file__).parent
_ORIGINAL_DIR = Path.home() / "self-improving"
_MERGED_DIR = _SCRIPT_DIR.parent  # ~/.openclaw/skills/fts5/self_improving

# Prefer existing installation (don't overwrite user's data)
if _ORIGINAL_DIR.exists():
    SELF_IMPROVING_DIR = _ORIGINAL_DIR
elif (_MERGED_DIR / "memory.md").exists():
    SELF_IMPROVING_DIR = _MERGED_DIR
else:
    SELF_IMPROVING_DIR = _MERGED_DIR

CORRECTIONS_FILE = SELF_IMPROVING_DIR / "corrections.md"
MEMORY_FILE = SELF_IMPROVING_DIR / "memory.md"
FTS5_LOG = Path.home() / ".openclaw/fts5.log"

# Lock file for mutual exclusion (shared with exchange_engine.py)
LOCK_FILE = SELF_IMPROVING_DIR / ".main_agent.lock"


# =============================================================================
# MUTUAL EXCLUSION - Main Agent Lock
# =============================================================================

@contextmanager
def main_agent_lock(timeout_seconds: int = 10):
    """
    Context manager for main agent write lock.
    
    When the main agent writes to memory, it acquires this lock
    to prevent the extraction agent (exchange_engine) from running.
    
    Usage:
        with main_agent_lock():
            write_correction(...)
            log_to_fts5(...)
    """
    lock_acquired = False
    try:
        with open(LOCK_FILE, 'w') as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                lock_acquired = True
                
                # Write lock info
                f.write(f"{datetime.now().isoformat()}|main_agent\n")
                f.flush()
                
                yield True
                
            except BlockingIOError:
                # Shouldn't happen for main agent, but handle gracefully
                yield False
            finally:
                if lock_acquired:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    finally:
        if lock_acquired and LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
            except:
                pass


def is_main_agent_active() -> bool:
    """
    Check if main agent is currently writing.
    
    Returns True if lock file exists and is recent (< 30 seconds).
    """
    if not LOCK_FILE.exists():
        return False
    
    try:
        mtime = datetime.fromtimestamp(LOCK_FILE.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds()
        
        # If lock is less than 30 seconds old, main agent is active
        if age < 30:
            return True
        else:
            # Stale lock, clean it up
            try:
                LOCK_FILE.unlink()
            except:
                pass
    except:
        pass
    
    return False


# =============================================================================
# FTS5 LOGGING (Step 1 of Two-Step Save)
# =============================================================================

def log_to_fts5(event_type: str, content: str, metadata: Optional[Dict] = None):
    """
    Log an event to FTS5 for future search.
    
    This is STEP 1 of the two-step save process.
    FTS5 is the permanent record; memory files are derived from it.
    
    Args:
        event_type: 'correction', 'preference', 'pattern', 'learning'
        content: The content to index
        metadata: Additional metadata (source, timestamp, etc.)
    """
    if not FTS5_AVAILABLE:
        print("⚠️ FTS5 not available, skipping indexing")
        return False
    
    try:
        sender_label = "self-improving"
        channel = "self-improving"
        session_key = "self-improving-memory"
        
        # Format content with event type for better search
        formatted_content = f"[{event_type.upper()}] {content}"
        
        if metadata:
            formatted_content += f"\nMeta: {metadata}"
        
        add_message(
            sender="system",
            sender_label=sender_label,
            content=formatted_content,
            channel=channel,
            session_key=session_key
        )
        
        # Also log to local file for debugging
        os.makedirs(os.path.dirname(FTS5_LOG), exist_ok=True)
        with open(FTS5_LOG, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {event_type}: {content}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to log to FTS5: {e}")
        return False


# =============================================================================
# CORRECTIONS & PREFERENCES (with mutual exclusion)
# =============================================================================

def index_correction(correction_text: str, context: Optional[str] = None):
    """
    Index a correction from Self-Improving into FTS5.
    
    When user corrects something, this logs it so future FTS5 searches
    can find and reference it.
    
    Uses TWO-STEP SAVE:
    1. Log to FTS5 (permanent record)
    2. Update corrections.md (derived file)
    
    Uses MUTUAL EXCLUSION to prevent extraction conflicts.
    """
    content = correction_text
    if context:
        content += f"\nContext: {context}"
    
    # Acquire lock before writing (mutual exclusion)
    with main_agent_lock():
        # STEP 1: Log to FTS5 first (this is the authoritative record)
        success = log_to_fts5("correction", content, {
            "source": "self-improving",
            "indexed_at": datetime.now().isoformat()
        })
        
        # STEP 2: Update corrections.md (derived, not authoritative)
        if success:
            _append_correction(correction_text, context)
        
        return success


def _append_correction(correction_text: str, context: Optional[str] = None):
    """Append a correction to corrections.md file."""
    try:
        os.makedirs(SELF_IMPROVING_DIR, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d")
        entry = f"\n- [{timestamp}] {correction_text}"
        if context:
            entry += f" | Context: {context[:100]}"
        
        with open(CORRECTIONS_FILE, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception as e:
        print(f"⚠️ Failed to append correction to file: {e}")


def index_preference(preference_text: str, project: Optional[str] = None):
    """
    Index a user preference into FTS5.
    
    Uses TWO-STEP SAVE + MUTUAL EXCLUSION.
    """
    content = preference_text
    if project:
        content += f"\nProject: {project}"
    
    with main_agent_lock():
        success = log_to_fts5("preference", content, {
            "source": "self-improving",
            "indexed_at": datetime.now().isoformat()
        })
        
        return success


def index_learning(learning_text: str, topic: str):
    """
    Index a learned pattern or knowledge into FTS5.
    
    Uses TWO-STEP SAVE + MUTUAL EXCLUSION.
    """
    with main_agent_lock():
        success = log_to_fts5("learning", learning_text, {
            "source": "self-improving",
            "topic": topic,
            "indexed_at": datetime.now().isoformat()
        })
        
        return success


# =============================================================================
# SEARCH FUNCTIONS
# =============================================================================

def search_corrections(query: str, limit: int = 5) -> List[Dict]:
    """
    Search FTS5 for related corrections.
    
    Used when user asks about past corrections or mistakes.
    """
    if not FTS5_AVAILABLE:
        return []
    
    try:
        results = search(f"correction {query}", limit=limit)
        return [r for r in results if r.get('channel') == 'self-improving']
    except Exception as e:
        print(f"❌ FTS5 search failed: {e}")
        return []


def search_preferences(query: str, limit: int = 5) -> List[Dict]:
    """
    Search FTS5 for related preferences.
    """
    if not FTS5_AVAILABLE:
        return []
    
    try:
        results = search(f"preference {query}", limit=limit)
        return [r for r in results if r.get('channel') == 'self-improving']
    except Exception as e:
        print(f"❌ FTS5 search failed: {e}")
        return []


def get_fts5_context_for_topic(topic: str) -> Optional[str]:
    """
    Get relevant FTS5 conversation history for a topic.
    
    Used by context_predictor to enhance memory loading suggestions.
    """
    if not FTS5_AVAILABLE:
        return None
    
    try:
        result = summarize(topic, limit=3)
        if result and not result.get('fallback'):
            return result.get('summary')
    except Exception as e:
        print(f"❌ Failed to get FTS5 context: {e}")
    
    return None


# =============================================================================
# MEMORY SUGGESTIONS
# =============================================================================

def suggest_memory_for_query(query: str) -> List[str]:
    """
    Analyze a query and suggest which Self-Improving memories to load.
    
    Returns list of file paths/identifiers to load.
    """
    suggestions = []
    
    # Keywords that suggest needing specific memories
    topic_keywords = {
        "domains/fts5": ["fts5", "搜尋", "歷史", "全文", "index"],
        "domains/openclaw": ["openclaw", "技能", "agent", "框架"],
        "domains/python": ["python", "安裝", "程式"],
        "domains/github": ["github", "git", "repo"],
        "domains/trading": ["交易", "freqtrade", "策略", "量化"],
        "memory.md": ["偏好", "設定", "我的", "I prefer", "我喜歡"],
        "corrections.md": ["錯誤", "修正", "不對", "wrong", "mistake"]
    }
    
    query_lower = query.lower()
    
    for memory_path, keywords in topic_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                suggestions.append(memory_path)
                break
    
    # If FTS5 available and query seems like history recall
    history_keywords = ["上次", "之前", "曾經", "last time", "before", "previously"]
    if any(kw in query_lower for kw in history_keywords):
        suggestions.append("fts5:context_recall")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)
    
    return unique_suggestions


# =============================================================================
# SYNC & STATUS
# =============================================================================

def sync_self_improving_to_fts5():
    """
    Sync existing Self-Improving memories to FTS5.
    
    Run this once to index all corrections and preferences.
    """
    print("🔄 Syncing Self-Improving → FTS5...")
    
    synced = 0
    
    # Sync corrections
    if os.path.exists(CORRECTIONS_FILE):
        try:
            with open(CORRECTIONS_FILE, 'r') as f:
                content = f.read()
            
            # Split into lines and index last N corrections
            lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
            for line in lines[-20:]:  # Last 20
                if line.startswith('-'):
                    line = line[1:].strip()
                if line and len(line) > 10:
                    if log_to_fts5("correction", line, {"synced": True}):
                        synced += 1
        except Exception as e:
            print(f"❌ Failed to sync corrections: {e}")
    
    print(f"✅ Synced {synced} entries to FTS5")
    return synced


def get_integration_status() -> Dict:
    """
    Get status of FTS5 ↔ Self-Improving integration.
    """
    return {
        "fts5_available": FTS5_AVAILABLE,
        "fts5_log_exists": os.path.exists(FTS5_LOG),
        "corrections_file": str(CORRECTIONS_FILE),
        "memory_file": str(MEMORY_FILE),
        "self_improving_dir": str(SELF_IMPROVING_DIR),
        "main_agent_active": is_main_agent_active(),
        "lock_file_exists": LOCK_FILE.exists()
    }


# CLI for testing
if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("🔗 FTS5 ↔ Self-Improving Integration")
    print("   [Two-Step Save + Mutual Exclusion]")
    print("=" * 50)
    print()
    
    status = get_integration_status()
    print(f"FTS5 Available: {status['fts5_available']}")
    print(f"FTS5 Log: {status['fts5_log_exists']}")
    print(f"Main Agent Active: {status['main_agent_active']}")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "sync":
            sync_self_improving_to_fts5()
        
        elif command == "status":
            for k, v in status.items():
                print(f"  {k}: {v}")
        
        elif command == "suggest" and len(sys.argv) > 2:
            query = sys.argv[2]
            suggestions = suggest_memory_for_query(query)
            print(f"Query: {query}")
            print(f"Suggestions: {suggestions}")
        
        elif command == "context" and len(sys.argv) > 2:
            topic = sys.argv[2]
            context = get_fts5_context_for_topic(topic)
            if context:
                print(f"FTS5 Context for '{topic}':")
                print(context[:500] + "..." if len(context) > 500 else context)
            else:
                print("No context found or FTS5 unavailable")
    
    else:
        print("Commands:")
        print("  python3 fts5_integration.py sync          - Sync existing memories to FTS5")
        print("  python3 fts5_integration.py status        - Show integration status")
        print("  python3 fts5_integration.py suggest <query> - Suggest memories for query")
        print("  python3 fts5_integration.py context <topic> - Get FTS5 context for topic")
