# Task：lg-rag T6 · 弃用 chat stream（api 清扫）

> **状态**：active  
> **类型**：弃用 / 传输下线  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) §4.1（T0 弃用通道声明）· §10.5 · §11  
> **前置**：T5 CLOSE · [`task_lg_rag_sse_token_stream`](../done/task_lg_rag_sse_token_stream.md) · [#105](https://github.com/Cyning12/ops-desk-api/pull/105)（+ 关账 [#106](https://github.com/Cyning12/ops-desk-api/pull/106)）；维护者下线窗口 = **维护者 Prompt 授权可开**（串行波次 2）  
> **分支**：`task/lg-rag-deprecate-chat-stream`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现。  
> **无关**：重开 T2–T5 · C0–C4 · 删 chat 代码/图/表 · 本仓改 Vue · iOS 改造（另仓）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-deprecate-chat-stream` |
| **git_branch** | `task/lg-rag-deprecate-chat-stream` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 410 响应断言（状态码 / JSON 报文迁移指针 / Deprecation 头）；旧 chat stream 路由用例改写为 410 断言；保留端点（models / sessions.latest / WS）行为不变旧测绿；lg-rag 五测试文件零影响 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（chat 行备注）· chat flow 图备注（若存在） |
| **graph_delta_note** | 仅备注「`/chat/stream` 已 410 下线（T6）」；**不删**节点/边/indexes 条目（05 §9.3 T6：文档为主） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 行为真值在 `05` §4.1/§10.5 + 本 task；不晋升 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（不改 lg-rag 契约；本波仅 chat 下线） |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | T6 仅 `/chat/stream` 410；web 删死代码另 task（00 出 Prompt）；iOS 若仍用 chat 另仓 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-31 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | pending | 30 | 待 **20-task-audit** R1 落盘后 00 代签 |
| HG-GRAPH-MODULES | approved | — | 不新增/不删一级模块 · **00 代签** · 仅 chat 行/flow 备注 |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`lg-rag-deprecate-chat-stream`** |
| **处置** | `POST /api/ops/chat/stream` → **410 Gone**：JSON 报文含迁移指针（指向 `POST /api/ops/lg-rag/stream`）+ `Deprecation` 响应头。**不**返回 404（避免监控「404 洪流」语义混淆，05 §10.5） |
| **代码保留** | **本波仅路由 410，不删 chat 代码/图/表**（延续 T0 §4.1 非范围「不删 chat 代码」；`app/ops/chat/**` 零删除；后续是否删码另 task 另议） |
| **保留端点** | `GET /chat/models` · `GET /chat/sessions/latest` · WS `/chat/ws`（demo · 未鉴权 · iOS 未采用）**本波不动**；列入验收「行为不变」 |
| **iOS** | 若仍用 chat stream → **另仓 task**；本仓不挡；410 报文自带迁移指针 |
| **兼容声明** | Session SoT 仍 lg-rag `thread_id`；**禁止**兼容 chat 事件全集；lg-rag 主路径 **零改动** |
| **测试清理** | `tests/test_chat_router.py` 的 `/chat/stream` 用例改写为 410 断言；`test_chat_service.py`（service 层）不动 |
| **文档** | README / docs 中引导用 `/chat/stream` 的活引用 grep 清扫改指 lg-rag；05 §10.5 回写实现句（含日期） |
| **图谱** | `01_modules.md` chat 行备注「stream 已 410（T6）」；chat flow 图加 deprecated 备注（若该图存在）；**不删**节点/边/indexes |
| **合入** | 本 PR **勿 auto-merge**。web 删 `useOpsChatSse` 死代码另 task（00 出 Prompt `PROMPT_web_00_t6_remove_chat_sse`，本仓不改 Vue） |
| **模块** | 不新增/不删一级模块 |

---

## 范围

1. `POST /api/ops/chat/stream` → 410 Gone（JSON 迁移指针 + `Deprecation` 头）  
2. 测试清理：`test_chat_router.py` stream 用例改 410 断言；其余 chat 测试不动  
3. 文档：README/docs 活引用清扫；05 §10.5 回写实现句  
4. 图谱：chat 行/flow 备注（不删节点/边/indexes）  
5. api pytest + ruff + `./scripts/graph-compile.sh`  
6. web Prompt 落盘 `_prompts/`（PROMPT_web_00_t6_remove_chat_sse）

## 非范围

- **删 chat 代码 / 图 / 表**（`app/ops/chat/**` 零删除；chat 拓扑不动）  
- WS `/chat/ws` · `GET /chat/models` · `GET /chat/sessions/latest` 下线或改动  
- iOS 改造（另仓）· 本仓改 Vue（web 另 task）  
- lg-rag 主路径任何行为改动（stream/replay/thread/token 全不动）  
- 重开 T2–T5 · **C0–C4** Host 沟通轨  
- chat 事件全集兼容层 / 双写桥  
- 改 freeze `lg-rag-sse-v1` 契约字段

---

## 验收标准

- [ ] `POST /api/ops/chat/stream` → **410**；JSON body 含迁移指针（`/api/ops/lg-rag/stream`）；响应含 `Deprecation` 头（测试断言）  
- [ ] `GET /chat/models` · `GET /chat/sessions/latest` 行为不变（旧测绿）；WS 文件零 diff  
- [ ] `tests/test_chat_router.py` stream 用例改写为 410 断言并绿；`test_chat_service.py` 不动且绿  
- [ ] **旧测 grep 影响面**：lg-rag 五文件（token_stream / sse_stream / sse_resume / lg_rag_session_continuity / session_continuity）零改动绿；`app/ops/lg_rag/**` 零 diff  
- [ ] README / docs 无引导使用 `/chat/stream` 的活引用（grep 清单列进自检）  
- [ ] 05 §10.5 回写实现句（410 · 日期 · 保留端点清单）；`01_modules.md` chat 行备注；**不删** G-L2 indexes 条目  
- [ ] `app/ops/chat/graph.py` 等 chat 源码 **零删除**（仅 router.py stream 端点函数改 410）  
- [ ] `ruff check` 触及路径绿；`pytest tests` 全绿；`./scripts/graph-compile.sh` exit 0  
- [ ] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 旧客户端调 `/chat/stream` | **410** + JSON 迁移指针 | 否（应迁 lg-rag） | 明确弃用错误 |
| iOS 未迁移仍调 chat stream | 同上 410（另仓 task 跟踪） | 否 | 同上 |
| 误调保留端点 | `/chat/models` · `/chat/sessions/latest` 正常服务（不变） | — | 无 |
| 监控告警 | 410 可单独计数告警；**非** 404 洪流 | — | — |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.1 · §10.5 · §11  
3. 只读参考：`app/ops/chat/router.py` · `app/ops/router.py` · `tests/test_chat_router.py`  
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
5. `docs/_tech_graph/l1/01_modules.md`（chat 行）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | **00**：T5 CLOSE（#105/#106）后起草 T6；钉 slug=`lg-rag-deprecate-chat-stream`；处置=`/chat/stream` 410（非 404 · 非删码）；保留 models/sessions.latest/WS；iOS 另仓；维护者 Prompt 授权下线窗口 |
