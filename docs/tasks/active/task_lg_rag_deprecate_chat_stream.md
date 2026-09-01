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
| **test_strategy_note** | 410 响应断言（状态码 / JSON body 迁移指针 / `Deprecation` 头）；`test_chat_router.py` 四个 stream 用例（L123/143/155/166）改写为 410 断言；保留端点行为不变旧测绿（`test_chat_router.py::TestListModels` · `tests/test_auth.py` L161+ sessions/latest · `tests/test_chat_ws.py` 零 diff）；lg-rag 五测试文件零影响；不连真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md`（chat 行备注）· `docs/_tech_graph/l1/10_flow_chat.graph.yaml` / `10_flow_chat.md` deprecated 备注（该 flow 图存在，10-task 已核） |
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
| HG-AUDIT-R1 | approved | 30 | 2026-08-31 · **00 代签 · 维护者 Prompt 授权** · 见 `docs/harness/reviews/task_lg_rag_deprecate_chat_stream_audit_R1_20260831.md`（R1 pass · 内容零阻塞） |
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
  - 形态建议（不钉死 · 30 落地时定）：`Deprecation: true`（RFC 8594；可附 `Sunset` 或 `Link: </api/ops/lg-rag/stream>; rel="successor-version"`）；body 建议 FastAPI `HTTPException(410, detail={...})` dict 形态，字段名建议 `{"error": "chat_stream_deprecated", "migrate_to": "/api/ops/lg-rag/stream", "message": <人读迁移说明>}`  
  - 鉴权次序建议：410 端点函数 **保留** `Depends(get_current_user)` → 未登录仍 **401**（匿名探针不见迁移指针，语义不变）；若 30 改无条件 410 须在自检写明理由  
- [ ] `GET /chat/models` · `GET /chat/sessions/latest` 行为不变（旧测绿：`test_chat_router.py::TestListModels` · `tests/test_auth.py` L161+ sessions/latest 用例）；WS `app/ops/chat/ws.py` 与 `tests/test_chat_ws.py` 零 diff  
- [ ] `tests/test_chat_router.py` 四个 stream 用例（`test_stream_success` L123 · `test_stream_requires_auth` L143 · `test_stream_invalid_session` L155 · `test_stream_existing_session_ok` L166）改写为 410 断言并绿（requires_auth 按上条鉴权次序定 401 或 410）；`test_chat_service.py` 不动且绿  
- [ ] **旧测 grep 影响面**：lg-rag 五文件（token_stream / sse_stream / sse_resume / lg_rag_session_continuity / session_continuity）零改动绿；`app/ops/lg_rag/**` 零 diff  
- [ ] README / docs 无引导使用 `/chat/stream` 的活引用（grep 检索词：`/chat/stream` · `chat/stream` · `useOpsChatSse`；清单列进自检；done/ 历史归档与 05/旧任务史陈述属历史记录 **不改**，仅改引导新用法的活引用，重点 `docs/ios/api-auth-chat.md` · `docs/deployment/rag-frontend-api-plan.md` · `docs/deployment/qdrant-*.md` · `docs/guides/*.md`；README.md 现网无引用，10-task 已核）  
- [ ] 05 §10.5 回写实现句（410 · 日期 · 保留端点清单）；`01_modules.md` chat 行备注；`10_flow_chat.graph.yaml` / `10_flow_chat.md` 加 deprecated 备注（图存在 · 已核）；**不删** G-L2 indexes 条目  
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
| 未登录调 `/chat/stream` | 建议仍 **401**（鉴权依赖前置 · 先于 410） | — | 登录错误（同现行） |
| 监控告警 | 410 可单独计数告警；**非** 404 洪流 | — | — |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.1 · §10.5 · §11  
3. 只读参考：`app/ops/chat/router.py`（stream L34 · models L97 · sessions/latest L108）· `app/ops/router.py` · `app/ops/chat/ws.py`（WS L79 · demo 未鉴权）· `tests/test_chat_router.py` · `tests/test_auth.py`（sessions/latest 旧测 L161+）· `tests/test_chat_ws.py`  
4. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
5. `docs/_tech_graph/l1/01_modules.md`（chat 行）

---

### 自检结论

> **10-task** · 2026-08-31 · 分支 `task/lg-rag-deprecate-chat-stream` · 思考轮由 SPEC（`05` §4.1/§10.5/§11）+ T0–T5 关账链承载；本文件 **不**预置 R0–R5（lint W4 合法 · 弃用清扫型 task 与 T5 同款处理）。

- [x] slug=`lg-rag-deprecate-chat-stream`；范围 **仅 T6 `/chat/stream` 410 清扫**；非范围钉死删 chat 代码/图/表 · WS/models/sessions.latest 下线 · iOS（另仓）· 本仓改 Vue · lg-rag 主路径 · 重开 T2–T5 · C0–C4 · chat 事件兼容层 · 改 freeze `lg-rag-sse-v1`
- [x] **00 定夺保留（零实质改动）**：410 非 404 非删码 · JSON 迁移指针 + `Deprecation` 头 · `app/ops/chat/**` 零删除 · 保留 models/sessions.latest/WS · iOS 另仓 · Session SoT 仍 lg-rag `thread_id` · lg-rag 零改动 · 勿 auto-merge
- [x] 事实核对（10-task · 现网一致 · 零修正）：`app/ops/chat/router.py` `@router.post("/stream")` 在 **L34** ✓ · `GET /chat/models` L97 ✓ · `GET /chat/sessions/latest` L108 ✓（经 `app/ops/router.py` `/api/ops` 前缀 → 全路径 `/api/ops/chat/*` ✓）；`tests/test_chat_router.py` `/api/ops/chat/stream` 用例在 **L127/147/158/204** ✓（四用例：success 200 · requires_auth 401 · invalid_session 404 · existing_session 200）；`app/ops/chat/ws.py` WS `/chat/ws` L79 · demo 未鉴权 ✓
- [x] 补充事实落点（收紧 · 非 00 定夺改动）：sessions/latest 旧测在 `tests/test_auth.py` L161+（非 test_chat_router.py）；WS 测试在 `tests/test_chat_ws.py`；chat flow 图 `10_flow_chat.graph.yaml/.md` **存在**（验收由「若存在」钉为明确备注要求）；README.md 无 `/chat/stream` 引用；05 §10.5 在 L338
- [x] 验收补钩：`Deprecation` 头取值形态建议（RFC 8594 `Deprecation: true`）· 410 body 字段名建议（`error` / `migrate_to` / `message`）· 鉴权次序建议（未登录仍 401）· grep 清扫检索词（`/chat/stream` · `chat/stream` · `useOpsChatSse` · 历史归档不改）
- [x] 验收 / failure_paths / 非范围 / 必读 / `wiki_delta` / invoke 留档字段齐全（`required_invoke_hats=10,00,30` · profile=`default`）
- [x] `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_deprecate_chat_stream.md` → **PASS**（exit 0 · W4）
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → **PASS**
- [x] HG-AUDIT-R1 **仍 pending**（本帽不签发 · 未动人工闸表）· 可交 **20-task-audit**

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | **00**：T5 CLOSE（#105/#106）后起草 T6；钉 slug=`lg-rag-deprecate-chat-stream`；处置=`/chat/stream` 410（非 404 · 非删码）；保留 models/sessions.latest/WS；iOS 另仓；维护者 Prompt 授权下线窗口 |
| 2026-08-31 | **10-task**：lint PASS（W4 · 思考轮 SPEC 承载）；事实核对现网一致零修正（router L34/L97/L108 · 测试 L127/147/158/204 · WS L79）；补 `### 自检结论`；验收补 `Deprecation` 头/body 字段形态建议 · 鉴权次序建议 · grep 检索词 · sessions/latest（test_auth.py）与 WS（test_chat_ws.py）旧测落点 · chat flow 图存在钉明；00 定夺钉死项 **零实质改动**；HG-AUDIT-R1 未动 |
| 2026-08-31 | **20** R1 **pass**（内容零阻塞；非阻塞 5 条已录审查文）· **00** 代签 `HG-AUDIT-R1` → approved；可派 30 |
