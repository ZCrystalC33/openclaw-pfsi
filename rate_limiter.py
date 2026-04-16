"""
Rate Limiter for FTS5/LLM API calls
Simple in-memory rate limiting with sliding window.
"""

import time
from typing import Dict, List
from collections import deque

# Configuration
MAX_CALLS_PER_MINUTE = 30
WINDOW_SECONDS = 60

# In-memory tracking (per-process)
_call_history: deque = deque(maxlen=MAX_CALLS_PER_MINUTE * 10)


def can_call() -> bool:
    """Check if we can make a call within rate limits."""
    now = time.time()
    
    # Remove old entries outside the window
    while _call_history and _call_history[0] < now - WINDOW_SECONDS:
        _call_history.popleft()
    
    return len(_call_history) < MAX_CALLS_PER_MINUTE


def record_call():
    """Record a call."""
    _call_history.append(time.time())


def get_remaining() -> int:
    """Get remaining calls in current window."""
    now = time.time()
    while _call_history and _call_history[0] < now - WINDOW_SECONDS:
        _call_history.popleft()
    return max(0, MAX_CALLS_PER_MINUTE - len(_call_history))


def wait_if_needed():
    """Wait if rate limit is exceeded."""
    if not can_call():
        # Calculate wait time
        oldest = _call_history[0] if _call_history else time.time()
        wait_time = WINDOW_SECONDS - (time.time() - oldest) + 1
        if wait_time > 0:
            time.sleep(wait_time)
    record_call()


# Decorator for automatic rate limiting
def rate_limited(func):
    """Decorator to apply rate limiting to a function."""
    def wrapper(*args, **kwargs):
        wait_if_needed()
        return func(*args, **kwargs)
    return wrapper
