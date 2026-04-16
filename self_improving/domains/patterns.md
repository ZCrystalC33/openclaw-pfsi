# Pattern Registry - FTS5 程式碼規範

集中管理壞味道與最佳實踐，供 linter 自動檢測。

## 壞味道（Anti-Patterns）

### 1. 路徑硬編碼
```python
# ❌ 錯誤
path = "/home/snow/self-improving"

# ✅ 正確
from pathlib import Path
_ORIGINAL_DIR = Path.home() / "self-improving"
if _ORIGINAL_DIR.exists():
    USE_IT
```

### 2. 跨層直接呼叫
```python
# ❌ 錯誤（scripts 直接 import core）
from skills.fts5 import search

# ✅ 正確（透過 fts5_integration）
import fts5_integration
fts5_integration.do_search()
```

### 3. 魔法數字
```python
# ❌ 錯誤
if days > 7:
    demote()

# ✅ 正確
HOT_THRESHOLD_DAYS = 7
if days > HOT_THRESHOLD_DAYS:
    demote()
```

### 4. 無錯誤處理的 decode
```python
# ❌ 錯誤
data = response.read().decode()

# ✅ 正確
try:
    data = response.read().decode('utf-8')
except UnicodeDecodeError:
    data = response.read().decode('latin-1')
```

### 5. YOLO 註解
```python
# ❌ 錯誤
# TODO: YOLO just make it work

# ✅ 正確
# TODO: Refactor after getting user feedback
```

## 最佳實踐（Best Practices）

### 1. 路徑檢測
```python
# 支援既有安裝 + 合併位置
_SCRIPT_DIR = Path(__file__).parent
_ORIGINAL_DIR = Path.home() / "self-improving"
_MERGED_DIR = _SCRIPT_DIR.parent

if _ORIGINAL_DIR.exists():
    USE_DIR = _ORIGINAL_DIR
else:
    USE_DIR = _MERGED_DIR
```

### 2. 分層依賴
```
Layer 0 (Core):      __init__.py, llm_summary.py
Layer 1 (Infra):     indexer.py, error_handling.py
Layer 2 (Scripts):   self_improving/scripts/*.py
```

### 3. 錯誤恢復三層
```python
# Layer 1: Retry
# Layer 2: Fallback template
# Layer 3: Raw results
```

### 4. 權限要求
```bash
# Scripts 必須 755
chmod 755 script.sh
```

## Linter 規則（自動檢測）

| 規則 | 檢測模式 | 狀態 |
|------|---------|------|
| 路徑硬編碼 | `expanduser("~/...")` | ✅ 已實作 |
| 跨層呼叫 | `from skills.fts5 import` in scripts | ✅ 已實作 |
| 魔法數字 | 需手動 code review | 📋 待實作 |
| 權限錯誤 | mode != 755 | ✅ 已實作 |
| YOLO 註解 | `# TODO.*YOLO` | ✅ 已實作 |

## 更新規則

當發現新的壞味道模式時：
1. 更新本檔案
2. 在 linter.py 新增檢測規則
3. 執行 linter 確認通過
4. Commit 並推送

---
*本檔案由 linter.py 自動驗證結構正確性*
