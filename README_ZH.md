# FTS5 - OpenClaw 對話歷史搜尋系統

> 🤖 讓你的 AI 助理記住一切 - 過往的對話、偏好、決定。

[![授權：MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![版本](https://img.shields.io/badge/Version-1.2.0-green.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)

**FTS5** 將你的 OpenClaw AI 助理升級為強大的記憶系統。它索引所有對話歷史並使用 LLM 生成智能摘要 - 就算過了好幾個月，也不會遺失上下文。

## ✨ 為什麼要用 FTS5？

| 沒有 FTS5 | 有 FTS5 |
|-----------|---------|
| ❌ 「上次我們討論什麼？」 | ✅ 立即從歷史中找到答案 |
| ❌ 每次對話都從零開始 | ✅ AI 記得過去的上下文 |
| ❌ 決定和協議遺失 | ✅ 可搜尋的決定歷史 |
| ❌ 重複解釋同樣的事 | ✅ AI 知道你的偏好 |

## 🎯 功能特色

- 🔍 **即時搜尋** - 跨越所有對話歷史的全文搜尋
- 🤖 **LLM 摘要** - 自動生成你的語言的摘要
- 🌐 **多語言** - 支援繁體中文、簡體中文、英文、日文
- 🔒 **安全** - 敏感資料自動遮罩，無硬編碼 Key
- ⚡ **快速** - SQLite FTS5，每分鐘 30 次限制
- 🛡️ **穩健** - 三層錯誤恢復機制
- 🔄 **自動索引** - 增量更新 via cron

## 🚀 快速開始

```bash
# 1. 複製
git clone https://github.com/ZCrystalC33/fts5-openclaw-skill.git ~/.openclaw/skills/fts5

# 2. 設定
cp ~/.openclaw/skills/fts5/config.env.example ~/.openclaw/fts5.env
nano ~/.openclaw/fts5.env  # 填入你的 MINIMAX_API_KEY

# 3. 安裝精靈
python3 ~/.openclaw/skills/fts5/setup.py

# 4. 重啟 OpenClaw
openclaw gateway restart
```

就這樣！現在問「上次我們談的 FTS5 系統」，立即得到答案。

## 💬 使用範例

```python
# 搜尋對話歷史
from skills.fts5 import search
results = search("Docker 設定", limit=5)
for r in results:
    print(f"{r['timestamp']}: {r['content'][:100]}...")

# LLM 智能摘要
from skills.fts5 import summarize
result = summarize("上次討論的專案進度")
print(result['summary'])

# 取得統計
from skills.fts5 import get_stats
stats = get_stats()
print(f"已索引訊息數: {stats['total']}")
```

## 📋 完整安裝指南

### 前置需求

- Python 3.7+
- 已安裝 OpenClaw
- MiniMax API Key（[免費申請](https://platform.minimax.io/)）

### 安裝 FTS5

```bash
# 安裝 FTS5
git clone https://github.com/ZCrystalC33/fts5-openclaw-skill.git ~/.openclaw/skills/fts5

# 設定 FTS5
python3 ~/.openclaw/skills/fts5/setup.py

# 重啟 OpenClaw
openclaw gateway restart
```

## 🔧 設定

### API Key（必填）

```bash
# 方式一：環境變數
export MINIMAX_API_KEY=sk-cp-your-key-here

# 方式二：設定檔
echo "MINIMAX_API_KEY=sk-cp-your-key-here" > ~/.openclaw/fts5.env
```

### 優先順序

1. `MINIMAX_API_KEY` 環境變數
2. `~/.openclaw/fts5.env` 設定檔
3. `~/.openclaw/config.json`

## 📊 自動索引（Cron）

FTS5 每 5 分鐘透過 cron hook 自動索引新對話。

```bash
# 查看 cron hook
cat ~/.openclaw/scripts/fts5-indexer.sh

# 手動索引
python3 ~/.openclaw/skills/fts5/indexer.py

# 檢查索引狀態
cat ~/.openclaw/fts5/indexer_state.json
```

## 🌐 多語言支援

FTS5 自動偵測並用你的語言回應：

| 語言 | 代碼 | 偵測方式 |
|------|------|---------|
| 繁體中文 | zh-TW | 開/龍/體 |
| 簡體中文 | zh-CN | 开/龙/体 |
| English | en | 預設 |
| 日本語 | ja | 平假名/片假名 |

## 🛡️ 安全性

- ✅ 無硬編碼 API Key
- ✅ 只使用使用者提供的憑證
- ✅ 敏感資料自動遮罩
- ✅ 私人設定檔（600 權限）

## 📁 檔案結構

```
~/.openclaw/skills/fts5/
├── __init__.py              # 主程式
├── llm_summary.py            # LLM + 多語言
├── rate_limiter.py           # 每分鐘 30 次
├── error_handling.py         # 三層 fallback
├── indexer.py                # 對話索引器
├── sensitive_filter.py       # 資料遮罩
├── setup.py                  # 互動精靈
├── install.py                # 安裝腳本
├── README.md                 # 英文說明
├── README_ZH.md             # 本檔案
├── SKILL.md                 # OpenClaw 技能
└── CHANGELOG.md             # 版本記錄
```

## 🎯 使用場景

| 情境 | 沒有 FTS5 | 有 FTS5 |
|------|-----------|---------|
| 詢問過去的專案 | 「我不知道」 | 立即摘要 |
| 回顧決定歷史 | 無限滾動 | 搜尋 + 摘要 |
| 繼續中断的工作 | 從頭開始 | AI 記得上下文 |
| 新 session 上線 | 沒有歷史 | 完整對話上下文 |

## 🤝 貢獻

Issues 和 PR 都歡迎！

## 📄 授權

MIT License - 詳見 [LICENSE](./LICENSE)

## 🙏 致謝

- [OpenClaw](https://github.com/openclaw/openclaw) - AI 助理框架
- [MiniMax](https://platform.minimax.io/) - LLM API

---

**由 Ophelia Prime 用 ❤️ 製作**

[GitHub](https://github.com/ZCrystalC33/fts5-openclaw-skill) | [回報問題](https://github.com/ZCrystalC33/fts5-openclaw-skill/issues) | [請求功能](https://github.com/ZCrystalC33/fts5-openclaw-skill/issues)