# Task：lg-rag T3 · Session 连续性（thread / 历史注入 / 窗口压缩）

> **状态**：in_progress（2026-08-31 · 00 起草 · 维护者 Prompt 授权开工 T3）  
> **类型**：session / 传输配套  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) §4 · §9 · §10.2 · [`session/ROADMAP_lg_rag_session_continuity_v0.md`](../../spec/agent-infra/session/ROADMAP_lg_rag_session_continuity_v0.md) L-a / L-b / L-d  
> **前置**：T2 CLOSE · [`task_lg_rag_sse_stream_updates`](../done/task_lg_rag_sse_stream_updates.md) · api [#97](https://github.com/Cyning12/ops-desk-api/pull/97) · web [#23](https://github.com/Cyning12/ops-desk-web/pull/23)  
> **分支**：`task/lg-rag-session-continuity`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现（00 **不**改 `app/` / `tests/`）。  
> **参考（勿兼容）**：[`ROADMAP_chat_continuity_v0.md`](../../spec/agent-infra/session/ROADMAP_chat_continuity_v0.md)（H3 归档）· `app/ops/session/continuity.py`  
> **无关**：T4 cursor/replay · T5 token delta · T6 删 `/chat/stream` · C0–C4 · 改 `chat/graph.py` 拓扑 · 强合并 chat 表

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-session-continuity` |
| **git_branch** | `task/lg-rag-session-continuity` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 窗口压缩纯函数单测；历史加载 mock DB；stream 同 `thread_id` 续写注入断言；鉴权 401 / 非法 thread 422 / 跨用户 404；不连真 LLM；**不测 replay** |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` · `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 备注：stream/invoke 按 `thread_id` 加载历史 + 窗口压缩后注入图输入；不新增一级模块 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 行为真值在 `05` §10.2 + session ROADMAP + 本 task；不晋升 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（扩展字段；不新开 freeze；不新增 event_type） |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | T3 仅 L-a/L-b/L-d；L-c = T4 另 task；web 另开 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-31 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-31 · **00 代签 · 维护者 Prompt 授权** · 见 `docs/harness/reviews/task_lg_rag_session_continuity_audit_R1_20260831.md` |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** · 仅 `lg_rag` 行/flow 备注；若增 `implementedBy` 同步 G-L2 indexes（`05` §9） |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| SoT | **`thread_id`**（lg-rag thread/session）；**不**以 chat `session_id` / `GET /chat/sessions/latest` 为 SoT |
| freeze | 沿用 **`lg-rag-sse-v1`**：请求已有可选 `thread_id`；`run.start` 已回写；缺省服务端生成并设 `X-Ops-Lg-Rag-Thread-Id`。本波 **不**新开 freeze、**不**新增 SSE `event_type` |
| 图输入 | 现网 `_ainvoke/_astream` 每轮只注入当前 `HumanMessage(query)`。T3 改为：加载历史 → 窗口压缩 → 装配 `messages`（历史 + 本轮 query）再进图 |
| 压缩 | 纯函数落 **`app/ops/lg_rag/`**（可参考 chat `compress_window` **允许重写**）。**禁止** `lg_rag` 新增 → `chat` 依赖边。默认 **`max_full_turns=6` · `group_size=2`**（对齐 H3） |
| 持久化 | **独立表**：`ops_lg_rag_threads`（id=`thread_id`、`user_id`、时间戳）+ `ops_lg_rag_turns`（thread_id、role、content、created_at）。**禁止**强合并 `ops_sessions_chat` / 把 `ops_runs.session_id` 当 SoT。stream **尽量**在 `done` 后落盘本轮 user/assistant |
| checkpointer | 进程内 InMemorySaver / 可选 PG **不是**跨请求产品 SoT；可保留作补充 |
| 合入 | **可 api-only 先合**（web 带稳定 `thread_id` 后置）。本 PR **勿 auto-merge** 直至 task 本节仍写明该策略。web 00 另开 task，本仓不改 Vue |
| 模块 | 不新增一级模块；`01_modules.md` 只改 `lg_rag` 备注 |
| 本波切片 | **仅 L-a / L-b / L-d**；**L-c = T4** 另 task。本文件验收 **禁止** replay / cursor / resume 断言 |
| 跨用户 thread | **404**（不泄露他用户 thread 是否存在）；**禁止**静默当本用户新会话并加载他用户 turns |

---

## 范围

仅 **L-a / L-b / L-d**（L-c 见非范围）：

1. **L-a · 产品模型与加载**：`thread_id` 归属当前用户；stream/invoke 可稳定续写；新 `thread_id` 隔离；缺省生成合法 id（≤255，与现网截断一致）  
2. **L-b · 历史注入 + 窗口压缩**：参数可配（默认对齐 H3 思路：近 N 轮全量、更早分组摘要）；压缩失败降级截断尾部；纯函数单测  
3. **L-d · session 面**：文档冻结（`05` §10.2 回写实现句 + 可选短 GUIDE）；HTTP **不**强制新 REST，但须能从现有 stream 请求（可选 `thread_id`）续上同一 thread  
4. **G-L2**：若新装配符号挂 `10_flow_lg_rag` `implementedBy` → 同步 `by_path_lg_rag` / `by_symbol_lg_rag`（`05` §9）  
5. 若新建独立表：Alembic 迁移 + SQLAlchemy 模型；**不**改 chat 表 schema  
6. api pytest + ruff + `./scripts/graph-compile.sh`

## 非范围

- **L-c / T4**：`seq` / cursor、断线 replay / resume、`sse_replay` 迁入 lg-rag、新 `cursor` 事件  
- **T5** token 流（`answer` delta）· **T6** 删除 `/chat/stream` 或 chat 下线窗口  
- **C0–C4** Host 沟通轨  
- 改 `app/ops/chat/graph.py` 拓扑（验收：该文件 **零 diff**）  
- 要求 lg-rag 与 `/chat/stream` **双写兼容**，或 chat `thinking` 事件全集 1:1  
- 强合并 `ops_sessions_chat`；把 `ops_runs.session_id` / `GET /chat/sessions/latest` 当 SoT  
- `app/ops/lg_rag/**` 新增 → `app.ops.chat` / `app.ops.session` 依赖边  
- 新开 freeze 或新增 SSE `event_type`（沿用 `lg-rag-sse-v1`）  
- 本仓改 Vue / web；完整长期记忆产品

---

## 验收标准

- [x] 同 `thread_id` 第二次 `/lg-rag/stream`（或装配函数）注入的 `messages` **含**上一轮 user/assistant（mock DB / 纯函数，不连真 LLM）  
- [x] 不同 `thread_id` **不**串历史  
- [x] 窗口压缩：超过 `max_full_turns` 时头部分组摘要、尾部全量；过短 noop；失败截断尾部  
- [x] 缺 `thread_id` 仍 200 stream 且响应头带回生成的 id  
- [x] 鉴权 401；非法 `thread_id`（超长等）422；跨用户 `thread_id` **404**（不注入他用户历史）  
- [x] **旧测 grep 影响面**：`tests/test_lg_rag_sse_stream.py` 帧序仍绿；`tests/test_session_continuity.py`（chat H3）零破坏；`chat/graph.py` 零 diff  
- [x] 不 import `app.ops.session` / `app.ops.chat` 于 `app/ops/lg_rag/**`  
- [x] `05` §10.2 回写实现句；G-L1 `lg_rag` 备注；若增 `implementedBy` 则 G-L2 indexes 同步  
- [x] `ruff check app tests` 触及路径绿；相关 pytest 绿；`./scripts/graph-compile.sh` exit 0  
- [x] `npx --yes dsh-coding-kit task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 历史加载失败 | 本轮按无历史继续；打日志；不 500 打断 SSE | 是 | 可能丢多轮上下文 |
| 压缩失败 | 截断为尾部 `max_full_turns` | 否 | 较早轮被丢 |
| `thread_id` 超长 / 非法 | 422 | 否 | 校验错误 |
| 落盘失败（done 后写 turns） | 日志；不阻断已发出的 SSE `done` | 是 | 下次可能缺本轮 |
| 图异常 | 维持 T2：SSE `error` + flush_traces；HTTP 仍 200 stream | 视异常 | `event_type=error` |
| 未登录 | 401 | 是 | 登录 |
| 跨用户 thread_id | **404**；不注入他用户历史；不 500 | 否 | 校验错误 |

---

## 给执行帽的必读列表

1. `AGENTS.md` · `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
2. `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4 · §9 · §10.2  
3. `docs/spec/agent-infra/session/ROADMAP_lg_rag_session_continuity_v0.md`  
4. `docs/_tech_graph/l1/01_modules.md`（`lg_rag` 依赖出边 **无** chat）  
5. `app/ops/lg_rag/router.py` · `graph.py`（当前只注入本轮 query）· `sse_stream.py`  
6. 参考实现（勿依赖）：`app/ops/session/continuity.py` · `tests/test_session_continuity.py`

---

## 合入 / 联调策略

- api PR：**勿 auto-merge**  
- **允许 api-only 先合**（web 未带稳定 `thread_id` 时，每问仍可能新 uuid，行为不低于现网 T2）  
- web：另开 `task_web_lg_rag_sse_t3`（Chat 发送稳定 `thread_id` · 刷新续会话）；api 00 只出 Prompt，不改 Vue  
- 联调：同 thread 续问 · 新 thread 隔离 · 超长历史压缩后 SSE 仍 `done`（`05` §10.2）

---

## CLOSE（待）

| 项 | 值 |
|---|---|
| PR | [#100](https://github.com/Cyning12/ops-desk-api/pull/100) · **勿 auto-merge** · 可 api-only 先合（见上节） |
| web task | 另开；本仓不改 web 码 |
| Spec | `05` §10.2 回写 |

---

### 自检结论

> **30/40** · 2026-08-31 · 分支 `task/lg-rag-session-continuity`（基于 `212402d`）

| 命令 | cwd | 退出码 |
|---|---|---|
| `npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_session_continuity.md` | 仓根 | **0** · `VERIFY: PASS` |
| `.venv/bin/pytest tests/test_lg_rag_*.py tests/test_session_continuity.py` | 仓根 | **0** · 87 passed |
| `.venv/bin/ruff check app/ops/lg_rag app/db/models.py tests/test_lg_rag_session_continuity.py tests/test_lg_rag_sse_stream.py` | 仓根 | **0** |
| `.venv/bin/ruff check app tests` | 仓根 | **1**（既有 `app/ops/rag/tokenizer.py` UP035 · `tests/test_rag_chunker.py` I001；**非本波路径**） |
| `./scripts/graph-compile.sh` | 仓根 | **0** |
| `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` | 仓根 | **0** · `LINT-WIKI-DELTA: PASS` |

`app/ops/chat/graph.py`：`git diff` 空（零 diff）。`lg_rag/**` 无 `app.ops.chat` / `app.ops.session` import（T2 `make_sse_event` 已内联为 `_sse_frame`）。

**未测**：真 LLM · 真 PG 落盘 round-trip · T4 replay/cursor · web 带稳定 `thread_id`。

思考轮由 SPEC（`05` + session ROADMAP）承载；本文件 **不**预置 R0–R5（lint W4 合法）。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | 00 起草 · 维护者 Prompt 授权 T3 · 闸 HG-TASK-DRAFT / HG-GRAPH-MODULES 代签 |
| 2026-08-31 | **10-task**：补 `### 自检结论` 占位；收紧非范围（L-c/T4/T5/T6/C0–C4）；钉跨用户 thread→404；lint 目标 PASS（允 W4） |
| 2026-08-31 | **00**：R1 pass 后代签 `HG-AUDIT-R1`；钉压缩默认 6/2 与独立表名 |
| 2026-08-31 | **30/40**：独立表 + 压缩装配 + HTTP 404/422/401；自检回填；验收全勾 |
