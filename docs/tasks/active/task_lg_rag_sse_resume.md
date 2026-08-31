# Task：lg-rag T4 · 断联 / replay（L-c · seq/cursor）

> **状态**：active  
> **类型**：传输 / SSE resume  
> **上游**：[`05_lg_rag_transport_and_session_plan_v0.md`](../../spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md) §4.2 · §4.3 · §9 · §10.3 · [`session/ROADMAP_lg_rag_session_continuity_v0.md`](../../spec/agent-infra/session/ROADMAP_lg_rag_session_continuity_v0.md) **仅 L-c**  
> **前置**：T2 CLOSE · [`task_lg_rag_sse_stream_updates`](../done/task_lg_rag_sse_stream_updates.md) · [#97](https://github.com/Cyning12/ops-desk-api/pull/97)；T3 CLOSE · [`task_lg_rag_session_continuity`](../done/task_lg_rag_session_continuity.md) · [#100](https://github.com/Cyning12/ops-desk-api/pull/100)  
> **分支**：`task/lg-rag-sse-resume`  
> **帽子**：00 起草闸；**10** 补全；**20** 审；**30+40** 实现。  
> **参考（勿兼容 / 勿 import）**：`app/ops/session/sse_replay.py` · `tests/test_session_continuity.py`（H3 思想）  
> **无关**：T3 重做 · T5 token delta · T6 删 `/chat/stream` · C0–C4 · 改 `chat/graph.py` 拓扑 · 强合并 chat 表

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `lg-rag-sse-resume` |
| **git_branch** | `task/lg-rag-sse-resume` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | cursor/replay 纯函数单测（mock 事件列表）；stream 落盘后 after_seq 重放断言；鉴权 401 / 跨用户·未知 run_id 404；不连真 LLM；不测 token delta |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml` · `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 备注 / flow：SSE 帧带 cursor · 事件落盘 · `POST /lg-rag/replay`；不新增一级模块；若增 `implementedBy` → 同步 G-L2 `by_path_lg_rag` / `by_symbol_lg_rag`（05 §9） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 行为真值在 `05` §4.2/§10.3 + session ROADMAP L-c + 本 task；不晋升 coding_wiki |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（扩展：帧内可选 `cursor` + replay HTTP；不 silent 扩；回写 05） |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | T4 仅 L-c；L-a/L-b/L-d 已合入 #100 勿重开；web T3/T4 不阻塞 api-only 先合 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-31 · **00 代签 · 维护者 Prompt 授权** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-31 · **00 代签 · 维护者 Prompt 授权** · 见 `docs/harness/reviews/task_lg_rag_sse_resume_audit_R1_20260831.md` |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** · 仅 `lg_rag` 行/flow 备注；若增 `implementedBy` 同步 G-L2 indexes |

---

## 00 定夺（草案 · 人可后签）

| 项 | 钉死 |
|---|---|
| **slug** | **`lg-rag-sse-resume`**（不用 `lg-rag-sse-replay`） |
| **SoT（会话）** | 仍为 T3 **`thread_id`**；本波 SoT（续看）= **`run_id` + `seq` / `cursor`** |
| **cursor 语义** | `cursor = "{run_id}:{seq}"`（对齐 H3 思想）。每帧 SSE `data` JSON **带可选顶层 `cursor` 字段**（与 `run_id`/`seq` 并列）。**不强制**每帧另发 `event_type=cursor` |
| **freeze** | 沿用 **`lg-rag-sse-v1`**：规范化可选 `cursor` + 新增 replay 面；契约写回 `05` §4.2 / §10.3。**禁止** silently 扩 event_type；若 20 坚持拆新 freeze id → 退回 00 改钉 |
| **存储** | **新独立表** `ops_lg_rag_run_events`（建议列：`run_id` · `seq` · `user_id` · `thread_id` · `event_type` · `payload` JSON/事件全文 · `created_at`）。stream 发出每帧后**尽量**落盘。**禁止**复用 chat SSE 事件表 / import `app.ops.session` / `app.ops.chat`。**不做**仅内存短窗（产品断线续看需跨请求） |
| **API 面** | ① 现有 `POST /api/ops/lg-rag/stream`：帧内带 `cursor`（行为扩展，路径不变）② **新** `POST /api/ops/lg-rag/replay`：body `{run_id, after_seq}` 或等价 `{cursor}`（解析出 run_id+seq）→ **SSE** 重放该 run 且 `seq > after_seq` 的已存帧（形状同 live）。**不**把 live 与 replay 混在同一请求语义里用 query 切换 |
| **断连服务端** | **仍「尽量跑完图」**（相对 T2 **不**引入 cancel）。T4 变更=事件可落盘 + 客户端可 replay 补齐；**不保证**断连瞬间客户端收齐 live 帧 |
| **鉴权 / 归属** | replay 须登录；`run_id` 须归属当前用户；未知 / 跨用户 → **404**（对齐 T3 不泄露） |
| **重复 seq** | replay 只返回 `seq > after_seq`；契约声明客户端对同 `run_id+seq` **去重不重复渲染**（api mock 测断言不重复下发已收 seq） |
| **合入** | **可 api-only 先合**；与进行中的 web T3 `thread_id` **不互堵**。本 PR **勿 auto-merge**。web「断网恢复 / 存 cursor」另 task（00 可出 Prompt，本仓不改 Vue） |
| **模块** | 不新增一级模块；`01_modules.md` 只改 `lg_rag` 备注 |

---

## 范围

仅 **L-c**（L-a/L-b/L-d 已随 T3 交付）：

1. **seq / cursor 产品语义**：与现网 `run_id`+递增 `seq` 帧对齐；每帧可选 `cursor`；文档钉死解析与 `after_seq` 关系  
2. **事件存储**：Alembic + SQLAlchemy 模型 `ops_lg_rag_run_events`；stream 路径尽量落盘  
3. **replay 契约**：`POST /lg-rag/replay`；按 `after_seq`/`cursor` 重放；鉴权与 run 归属  
4. **相对 T2**：客户端可从 cursor 续看；重复 seq 不重复下发/渲染（api 契约 + mock）  
5. **文档 / 图谱**：`05` §4.2（cursor 字段说明）· §10.3 回写实现句；G-L1 `lg_rag` 备注；若增 `implementedBy` → G-L2 indexes（`05` §9）  
6. api pytest（mock 流 / 纯函数优先）+ ruff + `./scripts/graph-compile.sh`

## 非范围

- **T3 重做**：thread 表 / 窗口压缩 / 历史注入（已合入 #100）  
- **T5** token 流（`answer` delta）· **T6** 删除 `/chat/stream` 或 chat 下线窗口  
- **重开 L-a / L-b / L-d**（已随 T3 #100）；本波 **仅 L-c**  
- **C0–C4** Host 沟通轨  
- 改 `app/ops/chat/graph.py` 拓扑（验收：该文件 **零 diff**）  
- 保证 `/chat/stream` 行为不变或双写兼容；chat `thinking` 全集 1:1  
- 强合并 chat 表；`lg_rag` → `chat` / `session` **新依赖边**；import `app.ops.session` / `app.ops.chat`  
- 复用 chat SSE 事件表 / 仅内存短窗 replay  
- 强制每帧另发 `event_type=cursor`（§4.2 可选行；本波 SoT=顶层 `cursor` 字段）  
- 拆新 freeze id（除非 20 退回 00 改钉）  
- 引入服务端 cancel / 中断图执行  
- 本仓改 Vue；完整 web 断网 UI（可另开 web task）  
- 保证 replay 覆盖「图仍在跑、尚未落盘」的竞态完整一致（可降级：仅已落盘帧；failure_paths 写明）

---

## 验收标准

- [x] 每帧 live SSE `data` 含 `run_id` · `seq` · 可选 `cursor`（`run_id:seq`）；纯函数/mock 可断言  
- [x] stream 过程尽量落盘 `ops_lg_rag_run_events`；同 `run_id` 按 `seq` 可查询  
- [x] `POST /lg-rag/replay`：给定 `after_seq`（或 cursor）只重放 `seq > after_seq`；形状对齐 live  
- [x] 重复请求同一 `after_seq` **不**重发已收区间（契约：仅 `>`）  
- [x] 未登录 → 401；未知 / 跨用户 `run_id` → **404**  
- [x] **旧测 grep 影响面**：`tests/test_lg_rag_sse_stream.py` 帧序仍绿（可扩展 cursor 字段断言）；`tests/test_session_continuity.py`（chat H3）零破坏；`tests/test_lg_rag_session_continuity.py`（T3）零破坏；`app/ops/chat/graph.py` **零 diff**  
- [x] `app/ops/lg_rag/**` **不** import `app.ops.session` / `app.ops.chat`（无新依赖边）  
- [x] `05` §4.2（顶层 `cursor` 字段说明；**不**强制新增必选 `event_type=cursor`）· §10.3 回写实现句；G-L1 备注；若增 `implementedBy` → G-L2 indexes（`05` §9）  
- [x] `ruff check` 触及路径绿；相关 pytest 绿（含上列旧测）；`./scripts/graph-compile.sh` exit 0  
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 客户端断连（live） | 服务端**仍尽量跑完**并尽量落盘；不 cancel | 是（replay） | live 可能缺帧；可用 replay 补 |
| 事件落盘失败 | 日志；**不**阻断已发出的 SSE | 是 | replay 可能缺部分帧 |
| replay 时 run 仍在写 | 只返回**已提交**帧；可短于最终全集 | 是 | 可再次 replay |
| 未知 / 跨用户 `run_id` | **404**；不泄露他用户是否存在 | 否 | 校验错误 |
| 非法 `after_seq` / cursor 格式 | 422 | 否 | 校验错误 |
| 未登录 | 401 | 是 | 登录 |
| 图异常（live） | 维持 T2：SSE `error` + flush；尽量落盘 error 帧 | 视异常 | `event_type=error` |

---

## 给执行帽的必读列表

1. 本 task（含 **00 定夺**）  
2. `docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2 · §4.3 · §9 · §10.3  
3. `docs/spec/agent-infra/session/ROADMAP_lg_rag_session_continuity_v0.md`（**仅 L-c**）  
4. 只读参考：`app/ops/lg_rag/sse_stream.py` · `router.py` · `thread_store.py`  
5. 思想参考（禁止依赖）：`app/ops/session/sse_replay.py` · `tests/test_session_continuity.py`  
6. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
7. `docs/_tech_graph/l1/01_modules.md` · `10_flow_lg_rag.*`

### 自检结论

> **10-task** · 2026-08-31 · 分支 `task/lg-rag-sse-resume` · 思考轮由 SPEC（`05` + session ROADMAP **仅 L-c**）承载；本文件 **不**预置 R0–R5（lint W4 合法）。

- [x] slug=`lg-rag-sse-resume`；范围 **仅 L-c**；非范围钉死 L-a/L-b/L-d 勿重开 · T5/T6/C0–C4 · 无 `lg_rag`→chat/session 新依赖边
- [x] 00 定夺保留：新表 `ops_lg_rag_run_events` · `POST /lg-rag/replay` · 断连仍「尽量跑完」· 跨用户/未知 404 · freeze 扩展 `lg-rag-sse-v1`（顶层 `cursor`，非 silent 扩 event_type）
- [x] 验收含旧测 grep 影响面（`test_lg_rag_sse_stream` · `test_session_continuity` · `test_lg_rag_session_continuity` · `chat/graph.py` 零 diff）
- [x] 验收 / failure_paths / 非范围 / 必读 / wiki_delta / invoke 留档字段齐全
- [x] `npx dsh-coding-kit@1.10.0 task lint --file docs/tasks/active/task_lg_rag_sse_resume.md` → **PASS**（exit 0 · W4）
- [x] `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` → **PASS**
- [x] HG-AUDIT-R1 **仍 pending**（本帽不签发）· 可交 **20-task-audit**

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | **00**：阶段 A 卫生通过后起草 T4；钉 slug=`lg-rag-sse-resume`；存储=新表；API=`/replay`；断连仍跑完；404；freeze 扩展 lg-rag-sse-v1 |
| 2026-08-31 | **10-task**：lint PASS（W4）；补 `### 自检结论`；收紧非范围（L-a/b/d 勿重开 · 禁 event_type=cursor 强制 · 禁 chat 表/依赖）；旧测路径钉死 `test_lg_rag_session_continuity.py` |
| 2026-08-31 | **20** R1 pass · **00** 代签 `HG-AUDIT-R1` → approved；可派 30 |
| 2026-08-31 | **30+40**：实现 L-c（表/cursor/replay）；验收勾选；见 invoke `invoke_20260831_30_40_*` |

### 自检结论（执行者）

> **30+40** · 2026-08-31 · 分支 `task/lg-rag-sse-resume`

| 命令 | 退出码 |
|---|---|
| `npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_sse_resume.md` | 0 · VERIFY PASS |
| `ruff check app/ops/lg_rag app/db/models.py tests/test_lg_rag_sse_resume.py tests/test_lg_rag_sse_stream.py` | 0 |
| `.venv/bin/pytest tests/test_lg_rag_sse_resume.py tests/test_lg_rag_sse_stream.py tests/test_lg_rag_session_continuity.py tests/test_session_continuity.py -q` | 0 · **34 passed** |
| `./scripts/graph-compile.sh` | 0 |
| `npx --yes dsh-coding-kit@1.10.0 task lint-wiki-delta --target .` | 0 · PASS |

- 验收表：上节全部勾选  
- `chat/graph.py` 零 diff；`lg_rag` 无 chat/session import  
- 已知未测：真 LLM 流；图仍在写时的竞态完整一致（failure_paths 已声明仅已落盘帧）  
- 不 CLOSE（留给 00）
