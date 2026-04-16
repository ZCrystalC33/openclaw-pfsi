# FTS5 - Full-Text Search for OpenClaw

> 🤖 Make your AI assistant remember everything - past conversations, preferences, decisions.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.2.0-green.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)

**FTS5** transforms your OpenClaw AI assistant into a memory powerhouse. It indexes all your conversation history and uses LLM to generate smart summaries - so you never lose context, even from months ago.

## ✨ Why FTS5?

| Without FTS5 | With FTS5 |
|--------------|-----------|
| ❌ "What did we discuss last time?" | ✅ Instant answer from history |
| ❌ Start every conversation from scratch | ✅ AI remembers past context |
| ❌ Lost decisions and agreements | ✅ Searchable decision history |
| ❌ Repetitive explanations | ✅ AI knows your preferences |

## 🎯 Features

- 🔍 **Instant Search** - Full-text search across all conversations
- 🤖 **LLM Summaries** - Auto-generated summaries in your language
- 🌐 **Multi-Language** - zh-TW, zh-CN, en, ja supported
- 🔒 **Secure** - Sensitive data auto-masked, no hardcoded keys
- ⚡ **Fast** - SQLite FTS5, 30 calls/min rate limit
- 🛡️ **Robust** - 3-layer error recovery
- 🔄 **Auto-Index** - Incremental updates via cron

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/ZCrystalC33/fts5-openclaw-skill.git ~/.openclaw/skills/fts5

# 2. Configure
cp ~/.openclaw/skills/fts5/config.env.example ~/.openclaw/fts5.env
nano ~/.openclaw/fts5.env  # Add your MINIMAX_API_KEY

# 3. Setup (interactive wizard)
python3 ~/.openclaw/skills/fts5/setup.py

# 4. Restart OpenClaw
openclaw gateway restart
```

That's it! Now ask things like "上次我們談的 FTS5 系統" and get instant answers.

## 💬 Usage Examples

```python
# Search conversation history
from skills.fts5 import search
results = search("Docker setup", limit=5)
for r in results:
    print(f"{r['timestamp']}: {r['content'][:100]}...")

# LLM-powered summary
from skills.fts5 import summarize
result = summarize("上次討論的專案進度")
print(result['summary'])

# Get statistics
from skills.fts5 import get_stats
stats = get_stats()
print(f"Total messages indexed: {stats['total']}")
```

## 📋 Complete Installation Guide

### Prerequisites

- Python 3.7+
- OpenClaw installed
- MiniMax API Key ([Get one free](https://platform.minimax.io/))

### Install FTS5

```bash
# Install FTS5
git clone https://github.com/ZCrystalC33/fts5-openclaw-skill.git ~/.openclaw/skills/fts5

# Setup FTS5
python3 ~/.openclaw/skills/fts5/setup.py

# Restart OpenClaw
openclaw gateway restart
```

## 🔧 Configuration

### API Key (Required)

```bash
# Option 1: Environment variable
export MINIMAX_API_KEY=sk-cp-your-key-here

# Option 2: Config file
echo "MINIMAX_API_KEY=sk-cp-your-key-here" > ~/.openclaw/fts5.env
```

### Priority Order

1. `MINIMAX_API_KEY` environment variable
2. `~/.openclaw/fts5.env` config file
3. `~/.openclaw/config.json`

## 📊 Auto-Indexing (Cron)

FTS5 automatically indexes new conversations every 5 minutes via cron hook.

```bash
# View cron hook
cat ~/.openclaw/scripts/fts5-indexer.sh

# Manual index
python3 ~/.openclaw/skills/fts5/indexer.py

# Check indexer status
cat ~/.openclaw/fts5/indexer_state.json
```

## 🌐 Multi-Language

FTS5 auto-detects and responds in your language:

| Language | Code | Detection |
|----------|------|-----------|
| 繁體中文 | zh-TW | 開/龍/體 |
| 簡體中文 | zh-CN | 开/龙/体 |
| English | en | Default |
| 日本語 | ja | Hiragana/Katakana |

## 🛡️ Security

- ✅ No hardcoded API keys
- ✅ User-provided credentials only
- ✅ Sensitive data auto-masked
- ✅ Private config file (600 permissions)

## 📁 File Structure

```
~/.openclaw/skills/fts5/
├── __init__.py              # Main API
├── llm_summary.py            # LLM + multi-language
├── rate_limiter.py           # 30 calls/min
├── error_handling.py         # 3-layer fallback
├── indexer.py                # Session indexer
├── sensitive_filter.py       # Data masking
├── setup.py                  # Interactive wizard
├── install.py                # Installer
├── README.md                 # This file
├── README_ZH.md             # 繁體中文
├── SKILL.md                 # OpenClaw skill
└── CHANGELOG.md             # Version history
```

## 🎯 Use Cases

| Scenario | Without FTS5 | With FTS5 |
|----------|--------------|-----------|
| Ask about past project | "I don't know" | Instant summary |
| Review decision history | Scroll forever | Search + summarize |
| Continue interrupted work | Start over | AI recalls context |
| Onboarding new session | No history | Full conversation context |

## 🤝 Contributing

Issues and PRs welcome! 

## 📄 License

MIT License - See [LICENSE](./LICENSE)

## 🙏 Credits

- [OpenClaw](https://github.com/openclaw/openclaw) - AI Assistant Framework
- [MiniMax](https://platform.minimax.io/) - LLM API

---

**Made with ❤️ by Ophelia Prime**

[GitHub](https://github.com/ZCrystalC33/fts5-openclaw-skill) | [Report Bug](https://github.com/ZCrystalC33/fts5-openclaw-skill/issues) | [Request Feature](https://github.com/ZCrystalC33/fts5-openclaw-skill/issues)