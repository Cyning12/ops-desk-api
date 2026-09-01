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

- [x] `POST /api/ops/chat/stream` → **410**；JSON body 含迁移指针（`/api/ops/lg-rag/stream`）；响应含 `Deprecation` 头（测试断言）  
  - 形态建议（不钉死 · 30 落地时定）：`Deprecation: true`（RFC 8594；可附 `Sunset` 或 `Link: </api/ops/lg-rag/stream>; rel="successor-version"`）；body 建议 FastAPI `HTTPException(410, detail={...})` dict 形态，字段名建议 `{"error": "chat_stream_deprecated", "migrate_to": "/api/ops/lg-rag/stream", "message": <人读迁移说明>}`  
  - 鉴权次序建议：410 端点函数 **保留** `Depends(get_current_user)` → 未登录仍 **401**（匿名探针不见迁移指针，语义不变）；若 30 改无条件 410 须在自检写明理由  
- [x] `GET /chat/models` · `GET /chat/sessions/latest` 行为不变（旧测绿：`test_chat_router.py::TestListModels` · `tests/test_auth.py` L161+ sessions/latest 用例）；WS `app/ops/chat/ws.py` 与 `tests/test_chat_ws.py` 零 diff  
- [x] `tests/test_chat_router.py` 四个 stream 用例（`test_stream_success` L123 · `test_stream_requires_auth` L143 · `test_stream_invalid_session` L155 · `test_stream_existing_session_ok` L166）改写为 410 断言并绿（requires_auth 按上条鉴权次序定 401 或 410）；`test_chat_service.py` 不动且绿  
- [x] **旧测 grep 影响面**：lg-rag 五文件（token_stream / sse_stream / sse_resume / lg_rag_session_continuity / session_continuity）零改动绿；`app/ops/lg_rag/**` 零 diff  
- [x] README / docs 无引导使用 `/chat/stream` 的活引用（grep 检索词：`/chat/stream` · `chat/stream` · `useOpsChatSse`；清单列进自检；done/ 历史归档与 05/旧任务史陈述属历史记录 **不改**，仅改引导新用法的活引用，重点 `docs/ios/api-auth-chat.md` · `docs/deployment/rag-frontend-api-plan.md` · `docs/deployment/qdrant-*.md` · `docs/guides/*.md`；README.md 现网无引用，10-task 已核）  
- [x] 05 §10.5 回写实现句（410 · 日期 · 保留端点清单）；`01_modules.md` chat 行备注；`10_flow_chat.graph.yaml` / `10_flow_chat.md` 加 deprecated 备注（图存在 · 已核）；**不删** G-L2 indexes 条目  
- [x] `app/ops/chat/graph.py` 等 chat 源码 **零删除**（仅 router.py stream 端点函数改 410）  
- [x] `ruff check` 触及路径绿；`pytest tests` 全绿（**CI 等价全绿 exit 0**；本机带 PG 余 2 个 **pre-existing** 环境失败 · 干净树 A/B 实证非本次回归 · 见自检结论执行者表）；`./scripts/graph-compile.sh` exit 0  
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

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

### 自检结论（执行者 · 30+40）

> **30+40** · 2026-08-31 · 分支 `task/lg-rag-deprecate-chat-stream` · GATE_VERIFY PASS（三闸 approved · verify exit 0）后开工。

| 自检命令 | 退出码 | 结果 |
|---|---|---|
| `npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_deprecate_chat_stream.md` | **0** | VERIFY: PASS（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 approved） |
| `.venv/bin/ruff check app/ops/chat/router.py tests/test_chat_router.py`（触及路径） | **0** | All checks passed |
| `.venv/bin/pytest tests -q`（全量 · 本机带 PG） | **1** | 500 passed · 1 skipped · **2 failed（pre-existing 环境项 · 非本次回归 · 证据见下）** |
| `DATABASE_URL=<不可达> .venv/bin/pytest tests -q`（**CI 等价** · 无 PG） | **0** | **464 passed · 39 skipped · 全绿**（CI 语义：`.github/workflows/pytest.yml` 无 postgres service → DB 用例 skip） |
| `./scripts/graph-compile.sh` | **0** | 9 graphs compile/check OK · mermaid normalize OK |
| `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` | **0** | LINT-WIKI-DELTA: PASS（scanned 98 · issues 0） |
| `git diff master -- app/ops/lg_rag` | **空（0 行）** | lg-rag 零 diff |

**pre-existing 失败证据（A/B · 非本次回归）**：`git stash`（干净树 3b510f7）→ `pytest tests/test_chat_ws.py` 同 2 失败 → `git stash pop` 后复跑一致。失败用例 `test_ws_message_streams_events` / `test_ws_second_message_while_active_rejected`：本机同时存在 PG + 带生产数据的 qdrant + embedder，RAG 链真实执行，WS 用例旧期望序列（`thinking×2 → answer×2` · 2026-07 chat-websocket 时代）不含 R-3 后新增的 `tool_result`（retrieve/grade）帧；`tests/test_chat_ws.py` 本 task 钉死 **零 diff**（00 定夺），修旧期望不在本 task 范围。环境修复尝试（向 opsdesk_test 补建 `ops_knowledge_chunks`）已 **回滚**，本机库恢复开工前状态。

**ruff 全量补充**：`ruff check app tests` 余 2 个 **pre-existing** 错误（`app/ops/rag/tokenizer.py` UP035 · `tests/test_rag_chunker.py` I001），均非触及路径、干净树即红；触及路径全绿。

**410 最终形态**（30 落地定 · 对照验收条 1 形态建议全采纳）：

- 鉴权次序：**保留 `Depends(get_current_user)`** → 未登录仍 **401**（先于 410，匿名探针不见迁移指针）
- body：`{"detail": {"error": "chat_stream_deprecated", "migrate_to": "/api/ops/lg-rag/stream", "message": "POST /api/ops/chat/stream 已于 2026-08-31 下线（lg-rag T6）。请迁移到 POST /api/ops/lg-rag/stream（lg-rag SSE · freeze lg-rag-sse-v1）。"}}`
- 响应头：`Deprecation: true`（RFC 8594）+ `Link: </api/ops/lg-rag/stream>; rel="successor-version"`

**grep 清扫清单分类**（检索词 `/chat/stream` · `chat/stream` · `useOpsChatSse`）：

| 命中 | 分类 | 处置 |
|---|---|---|
| `docs/ios/api-auth-chat.md`（6 处 + 时序/curl/错误码） | **活引用**（iOS 联调引导） | **已改**：顶部 410 横幅 + 概览表/§4/错误码/时序/curl/对比表注记，迁移指针 → lg-rag stream；iOS 迁移另仓 task |
| `docs/deployment/rag-frontend-api-plan.md`（L15/27/51/200/220） | **活引用**（前端路径引导） | **已改**：顶部 T6 注 + 关键行改指 `/lg-rag/stream`；L170「不替代 chat/stream」非目标陈述与 L236 文件指针保留 |
| `docs/deployment/qdrant-server-upgrade.md` L265 · `qdrant-migration-narrative.md` L185 | **活引用**（运维验收看板语句） | **已改**：加注「2026-08-31 T6 起为 `POST .../lg-rag/stream`」 |
| `docs/guides/DESIGN_...phase2` L112 · `IMPL_...phase1` L450 · `PLAN-...framework` L17 | 历史陈述（旧设计约束/状态记录，非引导用法） | 不改 |
| `docs/spec/agent-infra/README.md` L110 · `session/README.md` L17（R1 非阻塞 3 点名） | 边界陈述（「不以兼容 chat/stream 为验收」· 非引导用法） | 不改 |
| `docs/spec/agent-infra/05` §4.1/§9/§10.5 计划行/§11 · 旧 SPEC（lc-evidence 两篇） | SPEC 旧陈述 / 历史计划 | 不改（§10.5 另加「api 实现」回写行） |
| `docs/tasks/done/**` · `docs/harness/{reviews,invokes,evidence}/**` | 历史归档 | 不改 |
| `docs/_tech_graph`（10_flow_chat 两文件 · 11_flow_sync_to_chat · graph.json · l2 indexes） | 拓扑记录 | 10_flow_chat 已加 deprecated 备注（不删节点/边/indexes）；11_flow 节点仍在服务拓扑，不动 |
| `tests/test_chat_router.py`（4 处 URL） | 410 断言用例 | 已改写为 410 断言 |
| README.md | 无引用（10-task 已核 · 复跑确认） | — |

**R1 非阻塞 5 条处置**：

1. 行号双口径 → 以**用例名**为准改写，四用例名全保留（`test_stream_success/requires_auth/invalid_session/existing_session_ok`）
2. import 连带清理 → 已做：router.py 移除 9 项失效 import（uuid / AsyncGenerator / Request / StreamingResponse / AsyncSessionLocal / ChatStreamRequest / make_sse_event / ChatState / ChatEventStreamer / _create_run_record / _resolve_chat_session / compress_window+load_session_turns）；测试文件同步移除失效 import（json / BaseProviderImpl / LlmChunk / engine）与随之失效的 helper（_parse_sse / FakeProvider / fake_provider / no_persist / _db_available / DB_AVAILABLE / _reset_engine）——**文件内清理，零文件/模块删除**
3. 边角命中分类 → 上表（spec/agent-infra 两篇 README 均判边界陈述，不改）
4. `test_stream_existing_session_ok` 回归意图 → docstring 保留一行说明（原 uuid 404 回归对象随端点弃用不复存在，R1 非阻塞 4）
5. WS demo 未鉴权 → 不在本 task 范围（ws.py 自述 + `OPS_CHAT_WS_ENABLED` 闸均不动）；后续真鉴权 follow-up 提醒已知悉

**已知未测项**：真 LLM / 真客户端联调（task 钉死不连真 LLM）；iOS 迁移（另仓）；web 删 `useOpsChatSse`（另 task · Prompt 已落盘 `_prompts/PROMPT_web_00_t6_remove_chat_sse.md`）；本机带 PG 环境下 2 个 WS 旧测期望过时（pre-existing · 建议另 task 对齐 R-3 事件面或按 CI 语义 skip）。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | **00**：T5 CLOSE（#105/#106）后起草 T6；钉 slug=`lg-rag-deprecate-chat-stream`；处置=`/chat/stream` 410（非 404 · 非删码）；保留 models/sessions.latest/WS；iOS 另仓；维护者 Prompt 授权下线窗口 |
| 2026-08-31 | **10-task**：lint PASS（W4 · 思考轮 SPEC 承载）；事实核对现网一致零修正（router L34/L97/L108 · 测试 L127/147/158/204 · WS L79）；补 `### 自检结论`；验收补 `Deprecation` 头/body 字段形态建议 · 鉴权次序建议 · grep 检索词 · sessions/latest（test_auth.py）与 WS（test_chat_ws.py）旧测落点 · chat flow 图存在钉明；00 定夺钉死项 **零实质改动**；HG-AUDIT-R1 未动 |
| 2026-08-31 | **20** R1 **pass**（内容零阻塞；非阻塞 5 条已录审查文）· **00** 代签 `HG-AUDIT-R1` → approved；可派 30 |
| 2026-08-31 | **30+40**：`/chat/stream` → 410（`error/migrate_to/message` + `Deprecation: true` + `Link` successor-version · 保留 `Depends(get_current_user)` → 未登录仍 401）；四 stream 用例改 410 断言（用例名保留 · R1 非阻塞 4 回归意图入 docstring）；import 连带清理（R1 非阻塞 2）；05 §10.5 回写实现句 + §11.4 修订；iOS/deployment 活引用清扫（边角命中分类落自检表 · R1 非阻塞 3）；图谱 chat 行 + `10_flow_chat` deprecated 备注 + 人签记录（不删节点/边/indexes）；自检六命令：verify 0 · ruff 触及路径 0 · pytest CI 等价 0（本机带 PG 2 pre-existing 环境失败 · A/B 实证）· graph-compile 0 · lint-wiki-delta 0 · lg_rag diff 空；验收 9 条勾选；**不 CLOSE（留给 00）** |

---

> **30+40 交付完毕 · 不 CLOSE（留给 00）**：验收 9 条已勾（pytest 条附 CI 等价绿 + 本机 pre-existing 环境失败证据）；invoke `docs/harness/invokes/by-task/lg-rag-deprecate-chat-stream/invoke_20260831_30_40_lg-rag-deprecate-chat-stream.md`；本 PR **勿 auto-merge**（00 定夺 · 05 §11.1）。
