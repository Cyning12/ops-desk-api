# invoke · 00 · 维护者选 E3 + Wave B 实现方案（产品口径）

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 本窗方案/签录 · 未改 `app/`） |
| **维护者令** | 「走 E3」+ 产品：① 可见部分回复 ② 后端补全失败 → 用户点「继续回复」再生成 |
| **前置** | TC5 live×3 FAIL · `invoke_20261014_00_escalate_tc5.md` |

## 裁定落录

| ID | 原值 | 新值 |
|----|------|------|
| 升级口 | E1–E4 待选 | **E3** |
| **D1** | A-only | **A+B**（B 为主交付；A 降为 worker 死掉/无终帧时的补偿沉降，**不再**赌 ASGI disconnect 钩） |
| **D2** | `done{disconnected}` | **保留**作补偿/未知断流；Wave B 成功终态仍为普通 `done`（无 status 或 completed） |
| **D3** | api-only | **须开 web task**（部分回复展示 +「继续回复」CTA · 与 api 同波或紧随） |

---

## 产品路径（你要的两句）

```text
连接中：SSE 照常刷进度 + answer.delta（部分回复实时可见）
    │
    ├─ 客户端断/刷新 ──► worker 继续跑（与 HTTP 脱钩）
    │                      ├─ 成功 → 落盘 done → History 完整 · 续看/replay 200 补后半段
    │                      └─ 失败 → 落盘 error（+可选 done）→ History 半截 + terminal=error
    │                                              → 用户点「继续回复」→ 新 run 再生成
    └─ 一直连着 ──► 与今日一致至 done
```

**「继续回复」≠ HITL resume，≠ 同 run_id 从 seq N 续调 LLM。**  
= **同 `thread_id` 新开 `/stream`（新 `run_id`）**，把已落盘的部分答案当草稿注入 prompt（或显式 `continue_from_run_id`），整段重生成。

---

## 帧类型要不要升级？

### 结论（推荐）

| 面 | 是否新 `event_type` | 做法 |
|----|---------------------|------|
| 部分回复 | **否** | 继续用既有 `answer`（`delta` / `content`+`final`）+ `node.progress` / `subtask.progress` |
| 跑完成功 | **否** | 既有 `done`（可无 status ≡ completed） |
| worker 补全失败 | **否**（优先） | 既有 `error` + payload.`stage` 钉死如 `lg_rag.worker_failed`；`run_stream_closed` 已认 `error` |
| 补偿断流（进程被杀） | **否** | 沿用 D2 `done{status:'disconnected'}` 或 `error{stage:…}` |
| 前端 CTA | **否新帧** | History `terminal_status`：`running` / `completed` / `error` / `waiting_approval`（+ `disconnected` 若补偿）驱动按钮 |

**freeze 仍 `lg-rag-sse-v1`**：扩的是 **`done.status` / `error.stage` 字面量 + 传输架构**，**禁止** silent 新 `event_type`（与既有纪律一致）。  
仅当产品强要「半截但仍可续」机读态、且不愿复用 `error` 时，再批 **一个** `done.status:'incomplete'`（仍非新 event_type）——默认可不加，`error` 足够驱动「继续回复」。

### 明确不做什么

- 不把 `replay` 改成隐式再调 LLM（与 HITL resume 冲突）。
- 不为「继续回复」新增 `event_type=continue` 帧（浪费协议面；用 REST/新 run 即可）。

---

## 后端实现方案（Wave B 骨架）

### 1. 拆两段生命周期

```text
RunWorker（持有 astream · 只负责 emit→event_store）
    ↑ 进程内 asyncio.Task（MVP）· run_id 单飞租约
StreamSubscriber（HTTP SSE · 只读 event_store / 内存 fanout）
    ↑ 断连只取消 subscriber，不 cancel Worker
```

| 模块（建议） | 职责 |
|--------------|------|
| `app/ops/lg_rag/run_worker.py`（新） | 启动/单飞/跑图/落盘至 terminal；失败打 `error` |
| `app/ops/lg_rag/sse_subscribe.py`（新或从 sse_stream 拆） | 按 `run_id`+`after_seq` 订阅已落盘(+可选 live queue) 推 SSE |
| `router.py` `/stream` | 鉴权 → 分配 `run_id` → **先** start worker → **再** StreamingResponse(subscribe) |
| `event_store` | 基本零 diff；可选 `list_open_runs` 给补偿扫描 |
| `history` | 透传 `error` / `disconnected`；半截 answer 已从 delta 聚合 |

MVP **进程内 Task** 即可验证产品；多副本再加 DB 租约（对照 `task_multi_replica_verify` · FP-3）。

### 2. 部分回复如何「看得到」

| 场景 | 机制 |
|------|------|
| 仍连着 | 现网 SSE `answer.delta`（不改帧） |
| 刷新/换机 · worker 仍在跑 | **History** 读已落盘事件（勿走 `refuse_in_flight`）；UI 标 `running` + 已有半截 |
| worker 已 done | `POST /replay` 200 补 `after_seq` 之后帧（含后半段 delta + done） |
| worker 仍在跑且点「续看」 | 保持 **409+Retry-After**（TC3）或短轮询 History——**不要**用 replay 当 LLM 续跑 |

要点：部分可见依赖 **落盘先于/并行于 yield**（现 emit 已 persist）；Wave B 只要 worker 不断，半截一定在 DB。

### 3. 补全失败 →「继续回复」

1. Worker `except` → `emit error{stage:'lg_rag.worker_failed', message}`（必要）→ `run_stream_closed=True`（解除 409）。
2. History：`terminal_status=error` + 已聚合的 partial `answer`。
3. Web：「继续回复」→ `POST /lg-rag/stream`：
   - 同 `thread_id`
   - **新** `run_id`
   - body 可加可选 `continue_from_run_id`（api 读该 run 的 partial answer 拼进 history/system 草稿提示）
   - **禁止**调用 HITL `/resume`

### 4. Wave A 在 E3 下的角色（降级）

| 原 A 目标 | E3 后 |
|-----------|--------|
| ASGI disconnect 钩 | **停赌**（三次 live 已否） |
| 孤儿永久 409 | 改由 **worker 必打 terminal** + 可选 **定时补偿**：扫描超时仍 `!run_stream_closed` → 补 `error`/`disconnected` |
| `done{disconnected}` | 仅补偿/未知中止，不再当主路径 |

### 5. 测试 / 验收（建议写入 task 修订）

- **TC-B1**：起 stream → 中途关客户端 → worker 日志仍前进 → DB 最终 `done` → replay 200 含后半段。
- **TC-B2**：worker 注入失败 → `error` 落盘 → replay 200 → History `error` + partial。
- **TC-B3**：`continue_from_run_id`（或等价）新 run 绿；HITL resume 零 diff。
- **TC-B4**：真在飞 409 零 diff。
- **TC5 live**：用 B 语义重定义（断连后等 settle 再 replay），替换「同连接内 ASGI 钩」验收。

### 6. 图谱 / 文档

- `graph_change_layer`：**升 G-L1**（新 `run_worker` 模块须写 `01_modules.md`）→ **HG-GRAPH-MODULES 再签**。
- 回写 `05` §10.3：**恢复「断连尽量跑完」应然**（以 worker 为准）+ 实然注 MVP 单进程。
- freeze：`lg-rag-sse-v1` 不新开；§4.2 表注 `error.stage` / 可选 `done.status` 字面量。

### 7. 建议交付切片

| 切片 | 内容 | 仓 |
|------|------|-----|
| B0 | task 修订（D1=A+B · 产品口径 · TC-B*）+ 20 R2 | api |
| B1 | RunWorker + /stream 订阅拆分 + TC-B1/B4 | api |
| B2 | worker 失败 error.stage + continue_from_run_id | api |
| B3 | History CTA + 续看/继续回复文案 | **web** |
| B4 | 40 live + 补偿扫描（薄） | api |

---

## 下一棒（待你一句确认）

回复例如：

- 「确认方案，派 10 修订 task」→ 00 派 **10-task** 把 D1/验收改成 A+B 并开 web 提示  
- 「确认方案，直接派 30 做 B1」→ 须先 **重签 D1 + HG-GRAPH-MODULES**（范围变了）再 30  

本窗未改实现码 · 待派：等确认 · 已落盘本方案
