# FTS5 OpenClaw Skill

SQLite FTS5 full-text search with LLM summarization for OpenClaw conversations.

## Features

- 🔍 **FTS5 Full-Text Search** - Instant search across all conversation history
- 🤖 **LLM Summarization** - Automatic summary generation with MiniMax
- 🌐 **Multi-Language** - Supports Traditional Chinese, Simplified Chinese, English, Japanese
- 🔒 **Sensitive Data Filter** - Auto-masks API keys, tokens, private keys
- ⚡ **Rate Limiting** - Protects API from overuse (10 calls/min)
- 🛡️ **Error Recovery** - 3-layer fallback on API failure
- 📊 **Context Management** - Auto-adjusts based on query complexity
- 🔄 **Incremental Indexing** - Only processes changed session files

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/kiwi760303/fts5-openclaw-skill.git ~/.openclaw/skills/fts5
```

### 2. Setup configuration

```bash
# Copy example config
cp ~/.openclaw/skills/fts5/config.env.example ~/.openclaw/fts5.env

# Edit and add your MiniMax API key
nano ~/.openclaw/fts5.env
# MINIMAX_API_KEY=sk-cp-your-actual-key-here
```

### 3. Run onboarding (interactive setup)

```bash
python3 ~/.openclaw/skills/fts5/setup.py
```

This will verify your API key and test connectivity.

### 4. Index existing conversations

```bash
python3 ~/.openclaw/skills/fts5/indexer.py
```

## Usage

### Simple Search

```python
from skills.fts5 import search

results = search("Discord Bot", limit=5)
for r in results:
    print(f"{r['timestamp']}: {r['content'][:100]}")
```

### Search with LLM Summary

```python
from skills.fts5 import summarize

result = summarize("Discord Bot")
print(result['summary'])  # LLM-generated summary
```

### Statistics

```python
from skills.fts5 import get_stats

stats = get_stats()
print(f"Total messages: {stats['total']}")
```

## Workflow Integration

When user asks about past conversations:

1. User: "我們上次討論的 Discord Bot 怎麼樣了？"
2. Agent: `result = summarize("Discord Bot")`
3. Agent: Display `result['summary']` + relevant references

## Configuration

### API Key Priority

1. `MINIMAX_API_KEY` environment variable (highest)
2. `~/.openclaw/fts5.env` config file
3. `~/.openclaw/config.json` (fts5.api_key)

### Get MiniMax API Key

Visit [https://platform.minimax.io/](https://platform.minimax.io/) to get your API key.

## File Structure

```
fts5/
├── __init__.py           # Main module (search, summarize, add_message)
├── llm_summary.py        # LLM summarization with multi-language prompts
├── rate_limiter.py       # Rate limiting (10 calls/min)
├── error_handling.py     # 3-layer error recovery
├── indexer.py            # Incremental session indexer
├── sensitive_filter.py   # Sensitive data masking
├── setup.py              # Interactive onboarding setup
├── config.env.example    # Example configuration
├── SKILL.md             # OpenClaw skill definition
└── README.md            # This file
```

## Requirements

- Python 3.7+
- SQLite3 (built-in with Python)
- Internet connection (for MiniMax API)

## Troubleshooting

### "MINIMAX_API_KEY not found"

```bash
# Run setup
python3 ~/.openclaw/skills/fts5/setup.py

# Or manually set environment variable
export MINIMAX_API_KEY=sk-cp-your-key
```

### "API connection failed"

1. Check API key is correct
2. Verify internet connection
3. Run setup to test: `python3 ~/.openclaw/skills/fts5/setup.py`

## License

MIT License - See LICENSE file for details.

## Author

Ophelia Prime (OpenClaw AI Assistant)