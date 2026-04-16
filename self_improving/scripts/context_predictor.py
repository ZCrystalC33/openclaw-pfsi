#!/usr/bin/env python3
"""
Context Predictor for Self-Improving
Analyzes recent conversation context to predict likely user needs.

Design Principles (from Agentic Harness Patterns):
1. Select: Just-in-time context loading, not eager
2. Isolate: Don't pollute parent context with heavy memory loading
3. Context-aware: Respect mutual exclusion when main agent is writing
"""

# Paths - Support both original ~/self-improving/ and merged location
from pathlib import Path

_SCRIPT_DIR = Path(__file__).parent
_ORIGINAL_DIR = Path.home() / "self-improving"
_MERGED_DIR = _SCRIPT_DIR.parent

# Prefer existing installation
if _ORIGINAL_DIR.exists():
    SELF_IMPROVING_DIR = _ORIGINAL_DIR
else:
    SELF_IMPROVING_DIR = _MERGED_DIR

SCRIPTS_DIR = SELF_IMPROVING_DIR / "scripts"

# Standard imports
import os
import re
import sys
from typing import Dict, List, Optional

# Lock file for mutual exclusion check
LOCK_FILE = SELF_IMPROVING_DIR / ".main_agent.lock"


# =============================================================================
# MUTUAL EXCLUSION CHECK
# =============================================================================

def is_main_agent_writing() -> bool:
    """
    Check if main agent is currently writing to memory.
    
    If true, context predictor should avoid triggering memory operations
    that might conflict with the main agent's write.
    """
    if not LOCK_FILE.exists():
        return False
    
    try:
        mtime = datetime.fromtimestamp(LOCK_FILE.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds()
        
        # If lock is less than 30 seconds old, main agent is writing
        if age < 30:
            return True
        else:
            # Stale lock, clean up
            try:
                LOCK_FILE.unlink()
            except:
                pass
    except:
        pass
    
    return False


# Import datetime for the check
from datetime import datetime


# =============================================================================
# CONTEXT TRIGGERS
# =============================================================================

# Context trigger patterns
CONTEXT_TRIGGERS = {
    "openclaw": {
        "keywords": ["openclaw", "open claw", "技能", "agent"],
        "memory_hint": "OpenClaw 框架與技能開發"
    },
    "fts5": {
        "keywords": ["fts5", "搜尋", "歷史", "上次", "全文", "search"],
        "memory_hint": "FTS5 系統架構與優化"
    },
    "github": {
        "keywords": ["github", "git clone", "push", "repo", "repository"],
        "memory_hint": "GitHub 操作與 Repo 管理"
    },
    "python": {
        "keywords": ["python", "安裝", "套件", "pip", "import"],
        "memory_hint": "Python 開發與除錯"
    },
    "api": {
        "keywords": ["api", "key", "token", "endpoint", "請求"],
        "memory_hint": "API 整合與金鑰管理"
    },
    "docker": {
        "keywords": ["docker", "container", "image", "containerized"],
        "memory_hint": "Docker 容器化部署"
    },
    "trade": {
        "keywords": ["freqtrade", "交易", "策略", "量化", "crypto"],
        "memory_hint": "量化交易策略"
    },
    "chinese": {
        "keywords": ["繁體", "中文", "台灣", "Taiwan"],
        "memory_hint": "繁體中文使用者偏好"
    }
}

# User intent patterns
INTENT_PATTERNS = {
    "explanation": {
        "patterns": ["什麼是", "怎麼", "如何", "為什麼", "why", "how", "what is"],
        "memory_type": "concept"
    },
    "task": {
        "patterns": ["幫我", "做", "執行", "build", "create", "do", "make"],
        "memory_type": "task"
    },
    "correction": {
        "patterns": ["不對", "錯誤", "應該", "wrong", "incorrect", "should"],
        "memory_type": "correction"
    },
    "status": {
        "patterns": ["怎麼樣", "狀態", "進度", "status", "progress", "how's"],
        "memory_type": "status_check"
    },
    "history": {
        "patterns": ["上次", "之前", "曾經", "last time", "before", "previously"],
        "memory_type": "context_recall"
    }
}


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def analyze_text(text: str, include_fts5_context: bool = False) -> Dict:
    """
    Analyze text and return contextual predictions.
    
    Returns:
        dict with keys: topics, intents, suggested_memory_load, 
                        should_defer (if main agent is writing)
    """
    if not text:
        return {
            "topics": [],
            "intents": [],
            "suggested_memory_load": [],
            "should_defer": False
        }
    
    # MUTUAL EXCLUSION CHECK
    # If main agent is writing, defer memory operations
    main_agent_busy = is_main_agent_writing()
    
    text_lower = text.lower()
    
    # Detect topics
    detected_topics = []
    for topic, config in CONTEXT_TRIGGERS.items():
        for keyword in config["keywords"]:
            if keyword in text_lower:
                detected_topics.append({
                    "topic": topic,
                    "hint": config["memory_hint"]
                })
                break
    
    # Detect intents
    detected_intents = []
    for intent, config in INTENT_PATTERNS.items():
        for pattern in config["patterns"]:
            if pattern in text_lower:
                detected_intents.append({
                    "intent": intent,
                    "memory_type": config["memory_type"]
                })
                break
    
    # Build memory load suggestion
    suggested_memory_load = []
    
    # If main agent is busy, mark as deferred
    # Don't load heavy context during writes
    if main_agent_busy:
        suggested_memory_load.append("_deferred:await_main_agent")
    
    # If history intent, suggest FTS5
    if any(i["intent"] == "history" for i in detected_intents):
        suggested_memory_load.append("fts5:recent_conversations")
    
    # If correction intent, note for corrections log
    if any(i["intent"] == "correction" for i in detected_intents):
        suggested_memory_load.append("corrections:log_this")
    
    # Add topic-specific memory hints
    for topic_info in detected_topics:
        suggested_memory_load.append(f"domains/{topic_info['topic']}")
    
    return {
        "topics": detected_topics,
        "intents": detected_intents,
        "suggested_memory_load": suggested_memory_load,
        "should_defer": main_agent_busy
    }


def predict_next_action(current_context: str) -> Optional[str]:
    """
    Predict what the user might want to do next.
    
    Args:
        current_context: Latest user message or conversation summary
        
    Returns:
        Suggested next action or None
    """
    analysis = analyze_text(current_context)
    
    # If main agent is writing, suggest waiting
    if analysis["should_defer"]:
        return "⏳ 主代理正在寫入記憶，建議等待後再執行記憶操作"
    
    # Simple rule-based predictions
    if not analysis["topics"] and not analysis["intents"]:
        return None
    
    # If user asks about something technical, suggest related topics
    if any(t["topic"] == "fts5" for t in analysis["topics"]):
        return "建議搜尋 FTS5 相關的歷史對話"
    
    if any(i["intent"] == "task" for i in analysis["intents"]):
        return "任務開始，記錄相關偏好於 memory.md"
    
    if any(i["intent"] == "correction" for i in analysis["intents"]):
        return "捕捉到修正，寫入 corrections.md 並評估是否更新 memory.md"
    
    return None


def get_memory_load_suggestions(text: str) -> List[str]:
    """
    Get which memory files should be loaded for this context.
    
    Returns:
        List of file paths or identifiers
    """
    analysis = analyze_text(text)
    return analysis["suggested_memory_load"]


def should_load_fts5_context(text: str) -> bool:
    """
    Check if FTS5 context should be loaded for this query.
    
    Uses just-in-time loading principle:
    - Only load FTS5 context when explicitly needed
    - Don't eagerly load expensive context
    
    Returns:
        True if FTS5 context would help
    """
    analysis = analyze_text(text)
    
    # Don't load if deferred
    if analysis["should_defer"]:
        return False
    
    # Load for history recall or complex queries
    history_intents = ["history", "explanation"]
    return any(
        i["intent"] in history_intents 
        for i in analysis["intents"]
    )


def format_analysis_report(text: str) -> str:
    """
    Format analysis into a readable report.
    """
    analysis = analyze_text(text)
    
    lines = ["📊 Context Analysis Report"]
    lines.append("=" * 40)
    
    # Note if deferred
    if analysis["should_defer"]:
        lines.append("\n⚠️ Main agent is writing - memory ops deferred")
    
    if analysis["topics"]:
        lines.append("\n🔍 Detected Topics:")
        for t in analysis["topics"]:
            lines.append(f"  • {t['topic']}: {t['hint']}")
    else:
        lines.append("\n🔍 Topics: None detected")
    
    if analysis["intents"]:
        lines.append("\n🎯 Detected Intents:")
        for i in analysis["intents"]:
            lines.append(f"  • {i['intent']} ({i['memory_type']})")
    else:
        lines.append("\n🎯 Intents: None detected")
    
    if analysis["suggested_memory_load"]:
        lines.append("\n💡 Suggested Memory Load:")
        for m in analysis["suggested_memory_load"]:
            lines.append(f"  → {m}")
    
    return "\n".join(lines)


# =============================================================================
# CLI FOR TESTING
# =============================================================================

if __name__ == "__main__":
    import sys
    
    test_text = sys.argv[1] if len(sys.argv) > 1 else "我想了解 FTS5 的使用方法"
    
    print(f"Input: {test_text}")
    print()
    print(format_analysis_report(test_text))
    print()
    print(f"Predicted next action: {predict_next_action(test_text)}")
    print(f"Suggested memory load: {get_memory_load_suggestions(test_text)}")
    print(f"Should load FTS5 context: {should_load_fts5_context(test_text)}")
