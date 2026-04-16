# Agentic Harness Patterns 完整研究報告

> 資料來源：https://github.com/keli-wen/agentic-harness-patterns-skill
> 從 Claude Code 512,000 行原始碼萃取的生產級設計模式
> 閱讀進度：13/13 ✅

---

## 總覽：十大設計模式

| Pattern | 解決問題 | 核心原則 |
|---------|---------|---------|
| **Memory Persistence** | 代理忘記一切 | 分層持久化、雙步儲存、相互排斥萃取 |
| **Skill Runtime** | 每次都要重新解釋 | Lazy-loaded、預算約束發現 |
| **Tool & Safety** | 工具強大但安全 | Fail-closed、per-call 并發 |
| **Select** | 看到太多/太少 | 三層漸進揭露、Memoization |
| **Compress** | Context 太長 | Truncate + Recovery Pointer |
| **Isolate** | 委託邊界汙染 | Zero-inheritance、單層fork、filesystem isolation |
| **Agent Orchestration** | 多代理協調混亂 | Coordinator 必須綜合、深度有界 |
| **Hook Lifecycle** | 擴展性鉤子失控 | 單一 dispatch、trust 全有全無、deny>ask>allow |
| **Task Decomposition** | 長期工作管理 | Typed IDs、磁盤輸出、兩階段驅逐 |
| **Bootstrap Sequence** | 初始化順序混亂 | 依賴排序、memoized 並發、trust 分割 |

---

## 1. Memory Persistence（記憶持久化）⭐

### 問題
代理每次 fresh start 都忘記一切，無法累积经验。

### 解決方案：四層指令階層 + 雙步儲存

```
Priority 低 → 高：
1. Organization (組織級)  → 全域共享設定
2. User (用戶級)         → 個人偏好
3. Project (專案級)      → 專案上下文
4. Local (本地覆蓋)      → 永不進版控

重要：本地覆蓋永遠贏！
```

### 四型 Auto-Memory

| 類型 | 內容 | 範例 |
|------|------|------|
| `user` | 用戶身份、偏好 | "使用者喜歡用繁體中文" |
| `feedback` | 行為修正 | "糾正：不要用 npm，要用 bun" |
| `project` | 專案上下文 | "這個專案使用 TypeScript" |
| `reference` | 穩定參考事實 | "API 文件在 /docs" |

### 雙步儲存 invariant

```python
# ❌ 錯誤：直接寫入 index
memory_index.append(full_content)

# ✅ 正確：先寫 topic file，再更新 index
write_topic_file(topic_id, content)  # Step 1
append_to_index(topic_id, summary)   # Step 2
```

**為什麼？** 如果在兩個步驟之間崩潰，index 保持一致，只會產生孤立的 topic file（無害）。

### Session Extraction 的相互排斥

```python
# 如果主代理在這個 turn 寫入了記憶，extractor 跳過
if main_agent_wrote_memory(turn):
    extractor.skip()
    advance_cursor()
else:
    extractor.run()
```

---

## 2. Skill Runtime（技能執行期）

### 問題
每次都要重新解釋指令，浪費 token。

### 解決方案：Lazy Loading + 預算約束

```
Discovery: 預算約束
├── 只載入 metadata（cheap）
├── Full body 只在 activation 時載入
└── 總上限 ≈ 1% context window

Loading: Lazy
├── Idle token cost ≈ 0
└── Activation 時才 full load
```

### 觸發語言要放在前面

```
# ❌ 錯誤：描述在前面
description: "A skill for Python development"
trigger: "python, pip, virtualenv"

# ✅ 正確：觸發關鍵字在前面
trigger: "python, pip, virtualenv"
description: "A skill for Python development"
```

**原因：** 目錄有字數上限，尾巴會被截斷。

---

## 3. Tool & Safety（工具與安全）

### Fail-Closed 預設

```
預設行為：
├── 新工具 = 非並發 + 非唯讀
├── 必須明確 opt-in 才能並發
└── 防止意外平行執行狀態改變操作
```

### Per-Call 不是 Per-Tool

```
同一個工具對不同輸入有不同行為：
tool.read("config.json")     → safe for concurrent
tool.write("config.json")    → unsafe for concurrent
```

**重點：** 並發分類是針對每次呼叫，不是每個工具。

---

## 4. Select（選擇性載入）⭐

### 問題
看到太多/太少/錯誤的上下文。

### 三層漸進揭露

```
Tier 1 (Always):      Metadata (~100 tokens) → 總是在 context
Tier 2 (Activation):   Instructions (<5000 tokens) → skill 啟動時
Tier 3 (On-demand):   Resources (無上限) → 按需載入
```

### Memoization 要 memoize promise

```python
# ❌ 錯誤：只 memoize 結果
cache = {key: expensive_result}

# ✅ 正確：memoize promise（防止並發 races）
in_flight = {}
if key not in in_flight:
    in_flight[key] = expensive_async_call()
result = await in_flight[key]
```

### Invalidation 原則

```
❌ 不要用 timer 或 reactive subscriptions
✅ 在 mutation site 明確呼叫 invalidation
```

---

## 5. Compress（壓縮）⭐

### 問題
Session 太長時效能下降。

### 三層機制

| 機制 | 說明 |
|------|------|
| **Truncate + Recovery Pointer** | 截斷內容時附上"如何復原"的具體指示 |
| **Reactive Compaction** | 當 fill ratio 達到門檻時觸發（不是定時）|
| **Snapshot Labeling** | 所有快照都要標記"這是時間 T 的快照" |

### Truncation 黃金法則

```
❌ 錯誤：只說 "output was truncated"
✅ 正確："Run `cat filename` to see full output"
```

截斷時必須包含：
1. 具體的工具名稱
2. 具體的參數
3. 明確說明這是截斷的

---

## 6. Isolate（隔離）⭐⭐⭐

### 問題
委託工作時 shared state 造成碰撞：context 洩漏、檔案競爭、遞迴 fork 指數成本。

### 核心原則

```
Zero-inheritance is the safest default
├── Worker 從零 context 開始
├── 只有 explicit prompt 被繼承
└── 不繼承父的完整 context

Full-inheritance forks must be single-level
├── Child 繼承父的全部 context
├── 只能單層（不能遞迴 fork）
└── 防止 context cost 指數增長
```

### Filesystem Isolation

```
當 sub-agent 修改檔案時：
1. 建立 isolated copy (worktree/temp/cow-clone)
2. 注入 path translations
3. 完工後透過 controlled integration point 合併
```

### 決策框架：Blast Radius

| 隔離層級 | Worker 最多能破壞什麼 |
|---------|---------------------|
| Zero-inheritance | 只有自己的輸出 |
| Full-inheritance fork | 與 parent state 不一致 |
| Shared-filesystem | Parent 的 working directory |

**永遠從最窄的邊界開始，確定需要時才拓寬。**

---

## 7. Agent Orchestration（代理協調）⭐

### 三種模式

| 模式 | Context 共享 | 適用場景 |
|------|-------------|---------|
| **Coordinator** | 無（worker 從零開始）| 複雜多階段任務 |
| **Fork** | 完全繼承 | 快速平行分割 |
| **Swarm** | Peer-to-peer（共享 task list）| 長時獨立工作流 |

### Coordinator 的關鍵原則

```
❌ Anti-pattern:
"Based on your findings, fix it"

✅ 正確做法：
Coordinator 必須综合理解，不是只委託
→ 研究結果 → 綜合 → 精確規格 → 派遣實現
```

### 深度必須有界

```
❌ 危險：遞迴 delegation
├── Fork children 不能 fork
├── Swarm peers 不能 spawn other peers
└── 防止指數級 fan-out
```

---

## 8. Hook Lifecycle（鉤子生命週期）⭐⭐⭐

### 問題
沒有 centralized hook lifecycle：trust enforcement 不一致、ordering 不確定、blocking 決策傳播混亂。

### 核心原則

```
All hooks flow through a single dispatch point
├── 信任檢查
├── Source 合併
├── Type 路由
└── 結果聚合
```

### Trust 是全有或全無

```python
# 在任何 hook 觸發之前檢查一次
if workspace.untrusted:
    skip_all_hooks()  # 不是只跳過可疑的，全部跳過
```

### Multi-source Merge Priority

```
Priority 高 → 低：
1. Persisted configuration (settings files)
2. SDK-registered callbacks
3. Session-scoped registrations

當 policy 限制時，整層排除而不是個別過濾。
```

### Exit Codes 語義

| Exit Code | 語義 |
|-----------|------|
| 0 | 成功 |
| 特定 blocking code | block + inject error message |
| 其他非零 | warn but don't block |

### Deny > Ask > Allow Precedence

```
當多個 hooks 返回衝突的 permission 決策：
deny > ask > allow > passthrough

單一 security-minded hook 可以否決所有 permissive hooks。
```

### 六種 Hook 類型

| 類型 | 使用時機 |
|------|---------|
| `command` | Shell-level side effects |
| `prompt` | Hook 本身需要 reasoning |
| `agent` | Full sub-agent delegation |
| `http` | External service integration |
| `callback` | Full structured output control |
| `function` | Lightweight boolean gate only |

### Session Hooks 是 Ephemeral

```
Hooks 綁定到特定 session ID，session 結束時自動清理。
不寫入持久化設定。
Parent session 的 hooks 不會在 sub-agent session 觸發。
```

---

## 9. Task Decomposition（任務分解）

### 問題
並發工作造成 shared state 碰撞、輸出腐敗、無法追蹤完成狀態。

### 核心原則

```
Every work unit gets a typed identity
├── Prefix encodes work type (agent/shell/remote/teammate)
├── Collision-resistant random suffix
└── ~2.8 trillion combinations per prefix
```

### State Machine

```
States: pending → running → completed/failed/killed
Terminal states are permanent。
用 canonical check function 而不是 inline 比較。
```

### 磁盤輸出 + 偏移量

```
記憶體只存 read offset。
輸出寫到 per-work-unit 檔案。
poll 時讀取 delta 並 atomically advance offset。
→ 記憶體佔用恆定，與工作時長無關
```

### 兩階段 Eviction

```
Phase 1 (Eager):  Terminal state 時磁盤檔案刪除
Phase 2 (Lazy):   Parent 收到通知後記憶體記錄才刪除

通知閘門是關鍵：否則 race condition。
```

---

## 10. Bootstrap Sequence（引導序列）

### 問題
安全關鍵初始化步驟執行順序錯誤：TLS 在第一個連接後才載入、proxy 在第一個 TCP 連接後才配置、trust-gated 子系統在同意之前就激活。

### 四層初始化順序

```
1. Config parsing（最先）
2. Safe env vars（無 secrets）
3. TLS CA certificates（任何網絡連接之前）
4. Graceful shutdown registration
5. mTLS configuration
6. Global HTTP agent
7. API preconnection
```

### Trust Boundary 是關鍵轉折點

```
安全敏感的子系統（telemetry, secret env vars）
必須在 trust 建立之後才能激活。
```

### Memoized Init

```python
# 併發 callers 共享同一個 promise，不會 double-init
init_promise = memoized_async_init()
# 而不是：
if not initialized:
    initialize()  # 可能並發執行兩次
```

### Trivial Commands Fast-path

```
在任何 dynamic import 之前檢查：
version, help, schema dump → 立即返回，零模組載入
```

### Cleanup 在 Init 註冊

```
所有 cleanup handlers 在初始化時註冊，不是分散在 usage sites。
確保所有 exit paths 都會執行清理。
```

---

## 跨模式：共同主題

### 1. 枚舉勝過魔法
```
Typed IDs > string IDs
State machine > ad-hoc status
Canonical check function > inline comparisons
```

### 2. 兩階段勝過單階段
```
雙步儲存：topic file → index
兩階段 eviction：磁盤 → 記憶體
Bootstrap：config → trust → subsystems
```

### 3. 窄邊界是預設
```
Zero-inheritance > Full-inheritance
Local cleanup > Global GC
Fail-closed > Fail-open
```

### 4. 明確勝過隱式
```
Path translations must cover ALL file-operation tools
Memoize promises, not results
Trust is all-or-nothing, not gradual
```

---

## 對實際系統的啟示

### 設計檢查清單

```
□ 所有初始化步驟有明確的依賴順序嗎？
□ 並發 callers 會不會造成 double-init？
□ 環境變數有沒有 security implications？
□ Sub-agents 的 blast radius 受限嗎？
□ Hooks 有沒有 single dispatch point？
□ 長期工作有沒有 disk-backed output？
□ Eviction 有沒有 notification gate？
□ Cleanup handlers 在 init 註冊了嗎？
□ Local 覆蓋能勝過 organization 設定嗎？
□ 雙步儲存 invariant 成立了嗎？
```

---

## Gotchas 快速參考

| Pattern | Trap |
|---------|------|
| Memory | Index truncation is silent |
| Memory | Local overrides always win |
| Memory | Extraction timing creates race window |
| Memory | Don't store derivable content |
| Skills | Trigger language must be front-loaded |
| Select | Memoize promises, not results |
| Select | Invalidate at mutation site |
| Compress | Truncation needs recovery pointer |
| Isolate | Recursive forks = exponential cost |
| Isolate | Path translations must cover ALL tools |
| Isolate | Zero-inheritance prompts must be self-contained |
| Isolate | Merging isolated agents can conflict |
| Orchestration | Fork children cannot fork |
| Hooks | Trust gate blocks ALL hook types |
| Hooks | Missing script = same exit as intentional block |
| Hooks | Policy-restricted modes drop session hooks silently |
| Task | Don't evict before parent is notified |
| Task | Retained work units are never auto-evicted |
| Task | Update functions must not mutate existing state |
| Bootstrap | Memoization hides retry failures |
| Bootstrap | TLS cert store cached at boot |

---

## 參考文檔

- [Agentic Harness Patterns Repo](https://github.com/keli-wen/agentic-harness-patterns-skill)
- [Memory Persistence Pattern](references/memory-persistence-pattern.md) ✅
- [Skill Runtime Pattern](references/skill-runtime-pattern.md) ✅
- [Tool Registry Pattern](references/tool-registry-pattern.md) ✅
- [Permission Gate Pattern](references/permission-gate-pattern.md) ✅
- [Context Engineering Pattern](references/context-engineering-pattern.md) ✅
  - [Select Pattern](references/context-engineing/select-pattern.md) ✅
  - [Compress Pattern](references/context-engineing/compress-pattern.md) ✅
  - [Isolate Pattern](references/context-engineering/isolate-pattern.md) ✅
- [Agent Orchestration Pattern](references/agent-orchestration-pattern.md) ✅
- [Hook Lifecycle Pattern](references/hook-lifecycle-pattern.md) ✅
- [Task Decomposition Pattern](references/task-decomposition-pattern.md) ✅
- [Bootstrap Sequence Pattern](references/bootstrap-sequence-pattern.md) ✅
- [Isolate Pattern (context-engineering)](references/context-engineering/isolate-pattern.md) ✅

---

*研究日期：2026-04-16 | 閱讀進度：13/13 ✅*
