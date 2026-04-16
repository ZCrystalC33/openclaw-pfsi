#!/usr/bin/env python3
"""
Cold/Hot Layer Auto-Exchange Engine
Manages automatic promotion/demotion of memory entries.

Design Principles (from Agentic Harness Patterns):
1. TWO-STEP SAVE INVARIANT: Write topic file first, then update index
2. MUTUAL EXCLUSION: If main agent wrote memory, skip extraction

Memory Layers:
- HOT (memory.md): ≤100 lines, one-liner summaries with references
- WARM (topics/, domains/): full topic files
- COLD (archive/): not referenced in 30+ days

Rules:
- HOT (memory.md): recently referenced (< 7 days)
- WARM (topics/): referenced 3+ times
- COLD (archive/): not referenced in 30+ days
"""

import os
import re
import shutil
import fcntl
import errno
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Paths - Priority: Existing ~/self-improving/ > Merged location
_SCRIPT_DIR = Path(__file__).parent
_ORIGINAL_DIR = Path.home() / "self-improving"
_MERGED_DIR = _SCRIPT_DIR.parent  # ~/.openclaw/skills/fts5/self_improving

# Prefer existing installation (don't overwrite user's data)
if _ORIGINAL_DIR.exists():
    SELF_IMPROVING_DIR = _ORIGINAL_DIR
    print(f"📌 Using existing Self-Improving: {SELF_IMPROVING_DIR}")
elif (_MERGED_DIR / "memory.md").exists():
    SELF_IMPROVING_DIR = _MERGED_DIR
    print(f"📌 Using merged Self-Improving: {SELF_IMPROVING_DIR}")
else:
    # New install - use merged location
    SELF_IMPROVING_DIR = _MERGED_DIR
    print(f"📌 New installation at: {SELF_IMPROVING_DIR}")

# Core files
MEMORY_FILE = SELF_IMPROVING_DIR / "memory.md"
INDEX_FILE = SELF_IMPROVING_DIR / "index.md"
TOPICS_DIR = SELF_IMPROVING_DIR / "topics"
DOMAINS_DIR = SELF_IMPROVING_DIR / "domains"
PROJECTS_DIR = SELF_IMPROVING_DIR / "projects"
ARCHIVE_DIR = SELF_IMPROVING_DIR / "archive"

# Lock file for mutual exclusion
LOCK_FILE = SELF_IMPROVING_DIR / ".exchange.lock"

# Configuration
HOT_THRESHOLD_DAYS = 7       # Days before demoting from hot
COLD_THRESHOLD_DAYS = 30    # Days before archiving
PROMOTE_THRESHOLD = 3        # References needed to promote to warm
MAX_MEMORY_LINES = 100       # Hard cap for memory.md
MAX_MEMORY_BYTES = 25000     # ~25KB cap for memory.md

# Pattern to detect last access timestamps in files
LAST_ACCESS_PATTERN = r'<!-- last_access: (\d{4}-\d{2}-\d{2}) -->'
# Pattern to detect topic ID references
TOPIC_REF_PATTERN = r'\[topic:([^\]]+)\]'


# =============================================================================
# MUTUAL EXCLUSION - From Agentic Harness Patterns
# =============================================================================

class ExchangeLock:
    """
    Mutual exclusion lock for exchange engine.
    
    Implements the "mutual exclusion per turn" pattern from Harness Patterns:
    - If main agent wrote to memory during this turn, skip extraction
    - Prevents two writers (main agent + extractor) from conflicting
    """
    
    def __init__(self, lock_file: Path, timeout: int = 5):
        self.lock_file = lock_file
        self.timeout = timeout
        self.lock_fd = None
        self.acquired = False
    
    def __enter__(self):
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.acquired = True
            self.lock_fd.write(f"{datetime.now().isoformat()}|exchange\n")
            self.lock_fd.flush()
            return True
        except (IOError, OSError) as e:
            if e.errno == errno.EWOULDBLOCK:
                # Lock held by main agent
                return False
            raise
        finally:
            if self.lock_fd and self.acquired:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd:
            try:
                self.lock_fd.close()
            except:
                pass
        if self.acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except:
                pass
        return False


def exchange_lock():
    """
    Context manager factory for exchange engine lock.
    
    Usage:
        with exchange_lock() as acquired:
            if acquired:
                run_exchange_cycle()
            else:
                print("Skipped: main agent wrote memory")
    """
    return ExchangeLock(LOCK_FILE)


def check_main_agent_wrote() -> bool:
    """
    Check if main agent wrote memory since last extraction.
    
    Returns True if main agent holds the lock (extractor should skip).
    """
    if not LOCK_FILE.exists():
        return False
    
    try:
        # Check lock age - if very recent, main agent probably still writing
        mtime = datetime.fromtimestamp(LOCK_FILE.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds()
        
        # If lock is less than 10 seconds old, assume main agent is active
        if age < 10:
            return True
    except:
        pass
    
    return False


# =============================================================================
# TWO-STEP SAVE INVARIANT - From Agentic Harness Patterns
# =============================================================================

def two_step_save(topic_id: str, content: str, summary: str) -> bool:
    """
    Implement two-step save invariant: write topic file first, then update index.
    
    Step 1: Write full content to topics/{topic_id}.md
    Step 2: Update memory.md with one-liner summary
    
    This ensures:
    - If crash between steps: index is consistent (won't point to missing file)
    - Orphaned topic files are harmless
    - Index always reflects existing files
    
    Args:
        topic_id: Unique identifier for the topic
        content: Full content to save in topic file
        summary: One-liner summary for memory.md index
        
    Returns:
        True if both steps succeeded
    """
    try:
        # Ensure topics directory exists
        TOPICS_DIR.mkdir(parents=True, exist_ok=True)
        
        # STEP 1: Write topic file first
        topic_file = TOPICS_DIR / f"{topic_id}.md"
        timestamp = get_current_time()
        
        # Add frontmatter
        frontmatter = f"""---
name: {topic_id}
created: {timestamp}
type: auto-memory
---

"""
        with open(topic_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter)
            f.write(content)
        
        # STEP 2: Update memory.md index (append one-liner)
        _append_to_memory_index(topic_id, summary, timestamp)
        
        print(f"  ✅ Two-step save complete: {topic_id}")
        return True
        
    except Exception as e:
        print(f"  ❌ Two-step save failed for {topic_id}: {e}")
        # If step 1 succeeded but step 2 failed, we have an orphan
        # This is acceptable - orphans are harmless
        return False


def _append_to_memory_index(topic_id: str, summary: str, timestamp: str) -> None:
    """
    Append one-liner to memory.md index.
    
    Maintains the invariant that memory.md only contains one-liners
    that reference existing topic files.
    """
    # Check if already exists
    existing = _find_in_memory_index(topic_id)
    if existing:
        # Update existing entry instead of duplicating
        _update_memory_entry(topic_id, summary, timestamp)
        return
    
    # Build entry line
    entry = f"- [{topic_id}] {summary} <!-- last_access: {timestamp} -->\n"
    
    # Check memory.md size before appending
    if MEMORY_FILE.exists():
        size = MEMORY_FILE.stat().st_size
        if size >= MAX_MEMORY_BYTES:
            print(f"  ⚠️ Warning: memory.md approaching size cap ({size} bytes)")
            _compact_memory_index()
    
    # Append to memory.md
    with open(MEMORY_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)


def _find_in_memory_index(topic_id: str) -> Optional[str]:
    """Find existing entry for topic_id in memory.md."""
    if not MEMORY_FILE.exists():
        return None
    
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for [topic_id] or [topic:topic_id]
        patterns = [
            rf'\[{re.escape(topic_id)}\]',
            rf'\[topic:{re.escape(topic_id)}\]'
        ]
        
        for pattern in patterns:
            match = re.search(rf'{pattern}.*$', content, re.MULTILINE)
            if match:
                return match.group(0)
    except:
        pass
    
    return None


def _update_memory_entry(topic_id: str, summary: str, timestamp: str) -> None:
    """Update existing entry in memory.md."""
    if not MEMORY_FILE.exists():
        return
    
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace old entry with new
        old_entry = _find_in_memory_index(topic_id)
        if old_entry:
            new_entry = f"[{topic_id}] {summary} <!-- last_access: {timestamp} -->"
            content = content.replace(old_entry, new_entry)
            
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
    except Exception as e:
        print(f"  ❌ Failed to update memory entry: {e}")


def _compact_memory_index() -> None:
    """
    Compact memory.md if it exceeds size cap.
    
    Keeps most recent entries, removes oldest.
    """
    if not MEMORY_FILE.exists():
        return
    
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Keep only recent entries
        # Remove oldest entries until under cap
        # This is a simplified version - could be smarter
        
        if len(lines) > MAX_MEMORY_LINES:
            # Keep header lines (until first entry)
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith('- ['):
                    header_end = i
                    break
            
            # Keep header + most recent entries
            kept_lines = lines[:header_end] + lines[-MAX_MEMORY_LINES:]
            
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                f.writelines(kept_lines)
            
            print(f"  📦 Compacted memory.md: kept {len(kept_lines)} lines")
    except Exception as e:
        print(f"  ❌ Failed to compact memory: {e}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def parse_date(date_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None


def get_file_last_modified(file_path: Path) -> Optional[datetime]:
    """Get last modified time of a file."""
    if not file_path.exists():
        return None
    return datetime.fromtimestamp(file_path.stat().st_mtime)


def get_last_access_from_content(content: str) -> Optional[datetime]:
    """Parse last access timestamp from file content comments."""
    match = re.search(LAST_ACCESS_PATTERN, content)
    if match:
        return parse_date(match.group(1))
    return None


def update_last_access(file_path: Path) -> None:
    """Add/update last access comment in file."""
    if not file_path.exists():
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove existing last_access comment
    content = re.sub(LAST_ACCESS_PATTERN, '', content)
    
    # Add new comment at the top
    timestamp = get_current_time()
    new_content = f"<!-- last_access: {timestamp} -->\n{content}"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


def count_references_in_memory(topic_id: str) -> int:
    """Count references to a topic in memory.md."""
    if not MEMORY_FILE.exists():
        return 0
    
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count mentions of the topic
        patterns = [
            rf'\b{re.escape(topic_id)}\b',
            rf'\[topic:{re.escape(topic_id)}\]'
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, content))
        
        return count
    except:
        return 0


def get_memory_entries() -> List[Dict]:
    """Extract hot topics from memory.md."""
    if not MEMORY_FILE.exists():
        return []
    
    entries = []
    # Match lines like: - [topic-id] Summary text <!-- last_access: YYYY-MM-DD -->
    entry_pattern = re.compile(r'^-\s+\[([^\]]+)\]\s+(.+?)(?:<!--.*-->)?$', re.MULTILINE)
    
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for match in entry_pattern.finditer(content):
            topic_id = match.group(1).strip()
            summary = match.group(2).strip()
            last_access = get_last_access_from_content(match.group(0))
            
            entries.append({
                "topic_id": topic_id,
                "summary": summary,
                "last_access": last_access,
                "references": count_references_in_memory(topic_id)
            })
    except:
        pass
    
    return entries


def scan_warm_entries() -> List[Dict]:
    """Scan topics/ directory for warm entries."""
    if not TOPICS_DIR.exists():
        return []
    
    entries = []
    for f in TOPICS_DIR.glob("*.md"):
        if f.name.startswith('.'):
            continue
        
        last_modified = get_file_last_modified(f)
        references = count_references_in_memory(f.stem)
        
        try:
            content = open(f, 'r', encoding='utf-8').read()
            last_access = get_last_access_from_content(content) or last_modified
        except:
            last_access = last_modified
        
        entries.append({
            "topic_id": f.stem,
            "file": f,
            "last_modified": last_modified,
            "references": references,
            "last_access": last_access
        })
    
    return entries


def scan_cold_entries() -> List[Dict]:
    """Scan archive/ directory for cold entries."""
    if not ARCHIVE_DIR.exists():
        return []
    
    entries = []
    for f in ARCHIVE_DIR.glob("*.md"):
        if f.name.startswith('.'):
            continue
        
        last_modified = get_file_last_modified(f)
        references = count_references_in_memory(f.stem)
        
        try:
            content = open(f, 'r', encoding='utf-8').read()
            last_access = get_last_access_from_content(content) or last_modified
        except:
            last_access = last_modified
        
        entries.append({
            "topic_id": f.stem,
            "file": f,
            "last_modified": last_modified,
            "references": references,
            "last_access": last_access
        })
    
    return entries


def should_archive(entry: Dict) -> bool:
    """Check if entry should be moved to archive."""
    last_access = entry.get("last_access") or entry.get("last_modified")
    
    if not last_access:
        return True
    
    if isinstance(last_access, str):
        last_access = parse_date(last_access)
    
    if last_access and (datetime.now() - last_access).days >= COLD_THRESHOLD_DAYS:
        return True
    
    return False


def should_promote_to_warm(entry: Dict) -> bool:
    """Check if entry should be promoted from archive to warm."""
    if entry.get("references", 0) >= PROMOTE_THRESHOLD:
        return True
    return False


def archive_entry(entry: Dict) -> bool:
    """Move entry from topics/ to archive/."""
    try:
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        
        archive_file = ARCHIVE_DIR / entry["file"].name
        shutil.move(str(entry["file"]), str(archive_file))
        
        print(f"  📦 Archived: {entry['topic_id']}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to archive {entry['topic_id']}: {e}")
        return False


def restore_from_archive(entry: Dict) -> bool:
    """Restore entry from archive/ to topics/."""
    try:
        topic_file = TOPICS_DIR / entry["file"].name
        shutil.move(str(entry["file"]), str(topic_file))
        
        # Update last_access
        update_last_access(topic_file)
        
        print(f"  ♻️ Restored from archive: {entry['topic_id']}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to restore {entry['topic_id']}: {e}")
        return False


# =============================================================================
# MAIN EXCHANGE CYCLE
# =============================================================================

def run_exchange_cycle(skip_if_main_wrote: bool = True) -> Dict:
    """
    Run one complete exchange cycle.
    
    Args:
        skip_if_main_wrote: If True, skip cycle if main agent wrote memory
        
    Returns:
        dict with counts of promotions/demotions/archives
    """
    results = {
        "promoted_to_hot": 0,
        "demoted_to_warm": 0,
        "archived": 0,
        "restored": 0,
        "skipped": 0
    }
    
    # MUTUAL EXCLUSION CHECK
    if skip_if_main_wrote:
        with exchange_lock() as acquired:
            if not acquired:
                print("⏭️ Skipping cycle: main agent wrote memory (mutual exclusion)")
                results["skipped"] = 1
                return results
            # Lock acquired, proceed with extraction
    else:
        # Check without blocking
        if check_main_agent_wrote():
            print("⏭️ Skipping cycle: main agent is active")
            results["skipped"] = 1
            return results
    
    # Ensure topics directory exists
    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Scan all layers
    memory_entries = get_memory_entries()
    warm_entries = scan_warm_entries()
    cold_entries = scan_cold_entries()
    
    print("🔄 Running Cold/Hot Exchange Cycle...")
    print(f"   Hot entries in memory.md: {len(memory_entries)}")
    print(f"   Warm entries in topics/: {len(warm_entries)}")
    print(f"   Cold entries in archive/: {len(cold_entries)}")
    
    # Check warm entries - archive if cold
    print("\n📋 Checking warm entries...")
    for entry in warm_entries:
        # Update last access
        update_last_access(entry["file"])
        
        if should_archive(entry):
            if archive_entry(entry):
                results["archived"] += 1
        else:
            # Update reference count
            entry["references"] = count_references_in_memory(entry["topic_id"])
    
    # Check cold entries - restore if referenced
    print("\n📋 Checking archived entries...")
    for entry in cold_entries:
        if should_promote_to_warm(entry):
            if restore_from_archive(entry):
                results["restored"] += 1
    
    # Check hot entries - update access times
    print("\n📋 Checking hot entries...")
    for entry in memory_entries[:5]:  # Top 5
        print(f"   ✅ {entry['topic_id']}: {entry['references']} refs")
    
    return results


def main():
    print("=" * 50)
    print("🧠 Self-Improving Cold/Hot Exchange Engine")
    print("   [Two-Step Save + Mutual Exclusion]")
    print("=" * 50)
    
    results = run_exchange_cycle()
    
    print("\n" + "=" * 50)
    print("📊 Exchange Results")
    print("=" * 50)
    print(f"   Promoted to hot: {results['promoted_to_hot']}")
    print(f"   Demoted to warm: {results['demoted_to_warm']}")
    print(f"   Archived: {results['archived']}")
    print(f"   Restored: {results['restored']}")
    print(f"   Skipped (mutual exclusion): {results['skipped']}")
    print("=" * 50)


if __name__ == "__main__":
    main()
