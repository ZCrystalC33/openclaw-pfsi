---
name: FTS5 Full-Text Search
slug: fts5
version: 1.2.0
description: "🎓 SQLite FTS5 full-text search with LLM summarization for OpenClaw. Make your AI remember everything."
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

**FTS5** makes your OpenClaw AI assistant remember everything - past conversations, decisions, preferences. It indexes all history and uses LLM to generate smart summaries.

> *"The AI that forgets what you discussed is frustrating. FTS5 solves that."*

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Full-Text Search** | Instant search across all history |
| 🤖 **LLM Summaries** | Auto-generated in your language |
| 🌐 **Multi-Language** | zh-TW, zh-CN, en, ja |
| 🔒 **Secure** | No hardcoded keys, data auto-masked |
| ⚡ **Fast** | SQLite FTS5, 30 calls/min |
| 🛡️ **Robust** | 3-layer error recovery |
| 🔄 **Auto-Index** | Cron-based incremental updates |

## 🚀 Installation

### Prerequisites

- Python 3.7+
- OpenClaw installed
- MiniMax API Key

### Quick Install

```bash
# Install FTS5
git clone https://github.com/ZCrystalC33/fts5-openclaw-skill.git ~/.openclaw/skills/fts5

# Configure API key
cp ~/.openclaw/skills/fts5/config.env.example ~/.openclaw/fts5.env
nano ~/.openclaw/fts5.env  # Add MINIMAX_API_KEY

# Run setup wizard
python3 ~/.openclaw/skills/fts5/setup.py

# Restart OpenClaw
openclaw gateway restart
```

## 🎓 For Best Experience

Install the **Full Stack** for a truly intelligent AI assistant:

```bash
# FTS5 - Remember conversations
git clone https://github.com/ZCrystalC33/fts5-openclaw-skill.git ~/.openclaw/skills/fts5
```

| Skill | Purpose | Link |
|-------|---------|------|
| **FTS5** | Remember WHAT you discussed | [GitHub](https://github.com/ZCrystalC33/fts5-openclaw-skill) |

## 📋 Installation with Cron Hook

```bash
# Run installer (creates cron hook)
python3 ~/.openclaw/skills/fts5/install.py

# Setup API key
cp ~/.openclaw/skills/fts5/config.env.example ~/.openclaw/fts5.env
nano ~/.openclaw/fts5.env

# Run setup wizard
python3 ~/.openclaw/skills/fts5/setup.py
```

### Cron Hook Location

```
~/.openclaw/scripts/fts5-indexer.sh  (auto-created by install.py)
```

Runs every 5 minutes to index new conversations.

## 💬 Usage

```python
from skills.fts5 import search, summarize

# Search
results = search("Docker", limit=5)

# LLM Summary
result = summarize("上次討論的內容")
print(result['summary'])

# Stats
from skills.fts5 import get_stats
print(get_stats())
```

## 📊 File Structure

```
fts5/
├── __init__.py              # Main API
├── llm_summary.py            # LLM + multi-language
├── rate_limiter.py           # 30 calls/min
├── error_handling.py         # 3-layer fallback
├── indexer.py                # Session indexer
├── sensitive_filter.py       # Data masking
├── setup.py                  # Interactive wizard
├── install.py                # Cron hook installer
├── SKILL.md                 # This file
└── README_*.md              # Documentation
```

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

- [README_EN.md](README_EN.md) - English
- [README_ZH.md](README_ZH.md) - 繁體中文

## 📄 License

MIT License - See LICENSE file

## 🙏 Credits

- [OpenClaw](https://github.com/openclaw/openclaw)
- [MiniMax](https://platform.minimax.io/)

---

**Version:** 1.2.0 | **Author:** Ophelia Prime