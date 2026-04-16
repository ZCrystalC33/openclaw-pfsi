---
name: FTS5 Full-Text Search + Self-Improving
slug: fts5
version: 1.3.0
description: "🎓 SQLite FTS5 full-text search with LLM summarization + built-in Self-Improving intelligence for OpenClaw."
metadata: {
  "clawdbot": {
    "emoji": "🔍",
    "requires": {
      "bins": ["sqlite3"],
      "python": ["json", "re", "datetime", "urllib"]
    },
    "os": ["linux", "darwin", "win32"],
    "configPaths": ["~/.openclaw/fts5.env"]
  }
}
---

## 🎯 What is FTS5?

**FTS5** makes your OpenClaw AI assistant remember everything - past conversations, decisions, preferences. It indexes all history and uses LLM to generate smart summaries. Includes built-in **Self-Improving** for automatic learning from corrections.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Full-Text Search** | Instant search across all history |
| 🤖 **LLM Summaries** | Auto-generated in your language |
| 🌐 **Multi-Language** | zh-TW, zh-CN, en, ja |
| 🧠 **Self-Improving** | Learn from corrections, track patterns |
| 🔄 **Auto-Index** | Cron-based incremental updates |
| ⚡ **Rate Limiting** | 30 calls/min |
| 🛡️ **Error Recovery** | 3-layer fallback |
| 🔒 **Secure** | No hardcoded keys, data auto-masked |

## 🚀 Installation

### Prerequisites

- Python 3.7+
- OpenClaw installed
- MiniMax API Key

### Quick Install

```bash
# Install FTS5 + Self-Improving (combined)
git clone https://github.com/ZCrystalC33/fts5-openclaw-skill.git ~/.openclaw/skills/fts5

# Configure API key
cp ~/.openclaw/skills/fts5/config.env.example ~/.openclaw/fts5.env
nano ~/.openclaw/fts5.env  # Add MINIMAX_API_KEY

# Run setup wizard
python3 ~/.openclaw/skills/fts5/setup.py

# Run installer (creates cron hooks)
python3 ~/.openclaw/skills/fts5/install.py

# Restart OpenClaw
openclaw gateway restart
```

## 📋 Cron Hooks

Two automated tasks keep your system running:

| Task | Frequency | Hook |
|------|-----------|------|
| FTS5 Indexer | Every 5 min | `~/.openclaw/scripts/fts5-indexer.sh` |
| Self-Improving Exchange | 3 AM daily | `~/.openclaw/skills/fts5/self_improving/scripts/exchange-cron.sh` |

## 💬 Usage

### FTS5 Search

```python
from skills.fts5 import search, summarize, get_stats

# Search
results = search("Docker", limit=5)

# LLM Summary
result = summarize("上次討論的內容")
print(result['summary'])

# Stats
print(get_stats())
```

### Self-Improving Context Prediction

```python
from skills.fts5.self_improving.scripts.context_predictor import analyze_text

analysis = analyze_text("上次我們談的 FTS5")
print(analysis['topics'])       # [{'topic': 'fts5', ...}]
print(analysis['suggested_memory_load'])  # ['fts5:recent', 'domains/fts5']
```

## 📊 File Structure

```
fts5/
├── __init__.py                  # Main API: search, summarize, get_stats
├── llm_summary.py                # LLM + multi-language
├── rate_limiter.py               # 30 calls/min
├── error_handling.py             # 3-layer fallback
├── indexer.py                    # Session indexer with state tracking
├── sensitive_filter.py           # API key / token masking
├── setup.py                      # Interactive setup wizard
├── install.py                    # Cron hook installer
├── linter.py                     # Architectural enforcement tool
├── SKILL.md                      # This file
├── README.md                     # Bilingual documentation (EN/ZH)
└── self_improving/               # Self-Improving integration
    ├── memory.md                 # Hot layer (≤100 lines)
    ├── corrections.md            # Corrections log
    ├── index.md                  # Auto-generated index
    ├── heartbeat-state.md        # Heartbeat tracking
    ├── domains/
    │   ├── openclaw-fts5.md
    │   └── patterns.md           # Pattern registry
    └── scripts/
        ├── context_predictor.py   # P1: Context prediction
        ├── reindex.py            # P1: Auto-index
        ├── exchange_engine.py    # P2: Cold/Hot exchange
        ├── exchange-cron.sh      # P2: Cron hook (3 AM)
        └── fts5_integration.py   # P3: Bidirectional sync
```

## 🧠 Self-Improving Layer Rules

| Layer | Location | Trigger |
|-------|----------|---------|
| **HOT** | `memory.md` | < 7 days referenced |
| **WARM** | `domains/` | 3+ references |
| **COLD** | `archive/` | 30+ days unreferenced |

## 🔧 Configuration

| Method | How |
|--------|-----|
| Environment | `export MINIMAX_API_KEY=sk-cp-xxx` |
| Config file | `~/.openclaw/fts5.env` |

## 🛡️ Security

- ✅ No hardcoded API keys
- ✅ User-provided credentials only
- ✅ Sensitive data auto-masked
- ✅ Private config (600 permissions)

## 📄 Documentation

- [README.md](README.md) - Bilingual EN/ZH documentation
- [linter.py](linter.py) - Run `python3 linter.py` to verify architecture

## 🏗️ Architecture Enforcement

This project follows **Harness Engineering** principles:

```bash
# Verify architectural rules
python3 ~/.openclaw/skills/fts5/linter.py
```

**Linter checks:**
- Public API exports only
- No hardcoded paths
- Script permissions (755)
- Path detection consistency
- Layer dependencies
- Exchange engine rules
- YOLO anti-patterns

## 📄 License

MIT License - See LICENSE file

---

**Version:** 1.3.0 | **Author:** Ophelia Prime
