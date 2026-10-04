# Task：B1 会话历史只读 API（事件表真源 · threads + thread 完整历史）（chat-history-api）

> **状态**：`ready`（裁定 A/B 已定夺；20 R2 **通过**（0 阻塞 · R1 退回项 5/5 闭合）；`HG-TASK-DRAFT`/`HG-AUDIT-R1` 维护者已签 approved 2026-09-30 → **30 可开工**；`HG-GRAPH-MODULES` 随交付签录）
> **类型**：**码面**（新增只读 REST 端点 · 零表结构 · 默认零 SSE 帧改动）
> **依据 SPEC**：`docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed 2026-09-30 · §2 B1 · §4 Q1/Q6 · §5 FP-1/2/4 · §6 B1）
> **审查承接**：`docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md`（PASS-WITH-NITS · N3 阈值本 task 钉；N4 亡端点不计入可用面） · task R1：`docs/harness/reviews/task_chat_history_api_audit_R1_20260930.md`（**退回 10-task** · 唯一阻塞=缺「旧测 grep 影响面」；nit N1-N4 已回填，见修订记录）
> **分支**：`task/chat-history-hitl-ux`（SPEC §Harness 元信息 默认后端分支 · B1/B2 串行 · 各自 PR）
> **10 帽**：2026-09-30 · 10-task 拆解（不实现代码 · 不签 HG-AUDIT-R1）

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `chat-history-api` |
| **git_branch** | `task/chat-history-hitl-ux` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 集成/单测（造 `ops_lg_rag_run_events` 行 → threads/history 断言）；纯函数优先（聚合 / 分页 cursor / 标题降级）；不连真 LLM；SSE 帧对拍（仅 `run.start` +可选 `query` 键 · 零新 event_type）；**旧测 grep 影响面**：清点 `run.start` 既有断言面（`tests/test_lg_rag_sse_stream.py:101-102` · `tests/test_lg_rag_session_continuity.py:166-167` · `tests/test_multi_replica_dualproc.py:420-424` · `tests/test_lg_rag_sse_token_stream.py:183/254` · `tests/test_chat_ws.py:226/275`）并列入回归；新增可选 `query` 键 **subset-安全**（既有断言取子集字段 / 排序对拍双端一致） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` · `docs/_tech_graph/l1/10_flow_lg_rag.md` |
| **graph_delta_note** | `lg_rag`/`api` 行备注：新只读历史端点（`GET /api/ops/chat/threads` · `.../{thread_id}/history`）+ `run.start` payload 增可选 `query` 键（裁定 A1 · 非新 event_type）；不新增一级模块/表/SSE 事件类型；若增 `implementedBy` → 同步 G-L2 `by_path_lg_rag.yaml` · `HG-GRAPH-MODULES` 随交付签录 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无 `docs/coding_wiki/` 页面承载 lg_rag/hitl 路由真值（索引无对应条目）；路由真值以 G-L1 图谱备注为准 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | `lg-rag-sse-v1`（裁定 A1 已批：仅 `run.start` payload 增可选 `query` 键 · 非新 event_type · errata 见 `docs/spec/chat-history-hitl-ux/ERRATA-chat-history-hitl-ux_v0_20260930.md`） |
| **close_pr_policy** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 拆解 → 裁定 A/B 定夺 → 20 R1（退回）→ 10 回填 → 20 R2 → `HG-AUDIT-R1` 人签 → 30/40 → PR + CI 四绿 → merge → CLOSE |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 10 初稿经 20 R1/R2 复审闭合 · 维护者签 2026-09-30 |
| HG-AUDIT-R1 | approved | 30 | 20-task-audit R2 通过（0 阻塞）· 维护者签 2026-09-30 |
| HG-GRAPH-MODULES | pending | 30 | 新增 REST 路由 → G-L1 备注 + 签录（真值 `docs/_tech_graph/l1/01_modules.md`） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | 复用既有 G-L1 模块，不涉物理分层试点新增 |

---

## 背景与目标

D2 观察期实战：用户刷新后历史会话消失、无列表可回；挂起 run 无处可查。SPEC Q1 裁定历史真源=事件表 `ops_lg_rag_run_events`（每帧独立 commit · 回放真值），Q6 裁定服务端聚合为消息视图返回。

一句话目标：新增**当前用户**只读历史 API——thread 列表（标题 / 末活动 / run 数 / 最新状态含 `waiting_approval`）+ 单 thread 完整历史（每 run = query + answer + 子任务摘要 + 终态 + HITL 等待），跨用户 404，SSE **零新事件类型**（仅 `run.start` payload 增可选 `query` 键 · 裁定 A1）。

---

## 已定夺（维护者令「冲突部分安全推荐方案进行」· 2026-09-30）

> **落定**：下列裁定采纳「安全推荐」项，原「30 拒开工」阻塞解除；冻结口径以本节为准（SPEC §1 纪律 #1 对 `run.start` payload 增键的豁免已落独立 errata：`docs/spec/chat-history-hitl-ux/ERRATA-chat-history-hitl-ux_v0_20260930.md`，SPEC 升版时并轨）。

### 裁定 A · query / 标题真源（已采纳 A1 · 维护者 2026-09-30）

- **现状真读**：`app/ops/lg_rag/sse_stream.py:343-347` 的 `run.start` payload = `{run_id, thread_id, mode}`，**不含 query**；`ops_lg_rag_turns`（`thread_store.persist_thread_turns`）只在 `done` 后落 user turn，**`waiting_approval` 挂起路径不落**（`sse_stream.py:458-473`）。
- **SPEC 冲突**：§2 B1 称 query 来自 `run.start` 帧、§5 FP-4 预言「缺 `run.start` query 帧」降级 → SPEC 隐含 `run.start` 应携 query；但 §1 纪律 #1「SSE 契约零改动」、§3 非范围「freeze 契约任何改动」——两者不可同时成立。
- **备选**：
  - **A1（采纳）**：`run.start` payload **增可选 `query` 键**（非新 event_type · 承 T4 顶层 `cursor` 增键先例 · 旧 run 无键按 FP-4 降级）→ 完整满足 SPEC §6 B1「完整重建 query」；维护者已批该 freeze 语义（2026-09-30）。
  - **A2（零 SSE）**：query / 标题从 `ops_lg_rag_turns` user 轮取；`waiting_approval` run 无 turn → 标题降级 run_id 前缀（FP-4 允许），但 pending run 历史缺 query。
  - A3（禁）：从 checkpoint 取（违 SPEC Q1「不从 checkpoint 重建」）。
- **落定**：采纳 A1（维护者令 2026-09-30）→ 30 不再因此阻塞；实现须同步 `10_flow_lg_rag.md` 备注 `run.start` 携可选 `query`。

### 裁定 B · 端点归属模块（已采纳 B1 · 维护者 2026-09-30）

- **现状真读**：`.importlinter` `chat-outbound` 明列 `app.ops.chat` 禁 → `app.ops.lg_rag`；`lg-rag-outbound` 明列 `app.ops.lg_rag` 禁 → `app.ops.chat`。历史数据真源在 `lg_rag.event_store`。
- **备选**：
  - **B1（采纳）**：路由实现落 `app/ops/lg_rag/history_router.py`（`APIRouter(prefix="/chat")`，在 `app/ops/router.py` 注册），聚合纯函数落 `app/ops/lg_rag/history.py` → 路径保持 SPEC `/api/ops/chat/threads`，**零 import-linter 契约改动**，`app/ops/chat/**` 零 diff（维护者令 2026-09-30 采纳）。
  - B2：写进 `app/ops/chat/router.py` + 加 `app.ops.chat.router -> app.ops.lg_rag` 白名单（违 chat legacy 非主线纪律 · 需改契约 · 弃选）。
  - B3：改路径为 `/api/ops/lg-rag/threads`（偏离已签 SPEC 路径 · 弃选除非 00 改钉）。
- **import 纪律（20 R1 N1 实测）**：`history_router.py` 取鉴权/ORM 须经同族 `app.ops.lg_rag.router` 间接取 `CurrentUser`/`OpsUser`（直连 `app.ops.deps`/`app.db.models` 会破 `lg-rag-outbound`）；若改为直连，须显式给 `lg-rag-outbound` 增 `ignore_imports` 并同步更正「零 import-linter 契约改动」措辞（维护者仅禁改 chat-outbound；二者以 `lint-imports` 绿为准）。

### 裁定 C · B2 的鉴权/归属口径

本 task 不涉；登记给 `task_hitl_browser_decide.md` 裁定 D/E。

---

## 范围（钉死）

| # | 件 | 落点（按裁定 B） | 动作 |
|---|---|---|---|
| H1 | threads 列表 | `GET /api/ops/chat/threads` | `user_id=当前用户` 聚合事件表：`thread_id` · `title` · `last_activity_at` · `run_count` · `latest_run_status`（`running`/`waiting_approval`/`completed`/`error`） · `cursor`/`limit` 分页（默认 20 · 上限 100 · 超限 422） |
| H2 | thread 完整历史 | `GET /api/ops/chat/threads/{thread_id}/history` | 按 run 升序（run 首帧 `created_at`）重建消息视图：每 run = `query` + `answer`(聚合) + `subtasks`(subtask.progress 摘要) + `terminal_status`(done.status) + `hitl`(hitl.waiting requests)；run 内 seq 升序；`cursor`/`limit` 分页 |
| H3 | 聚合纯函数 | `app/ops/lg_rag/history.py` | 事件行 → 消息视图（可单测 · 不碰 DB）：answer 终帧优先 → 回退 delta 拼接；标题/降级；run 序 |
| H4 | 归属校验 | 查询层 | thread 归属对拍当前用户 · 跨用户/未知 → 404（不 403 · 不泄露存在性）；复用 `event_store.run_owner` 语义 |
| H5 | 事件查询 | `event_store.py`（优先复用/最小扩展） | 按 user 列 thread、按 thread 列 run 事件；分页键；不新增表/迁移 |
| H6 | 图谱/文档 | G-L1 | `01_modules.md` + `10_flow_lg_rag.md` 备注新端点；`graph-compile.sh` 绿 |

## 非范围（钉死 · 越任一条即停）

- ❌ SSE 新事件类型 / 改 `hitl.waiting`/`done` 帧语义（仅 `run.start` payload 增可选 `query` 键已批 · 其余帧零改动）
- ❌ 从 checkpoint（`checkpoints`/LangGraph state）重建历史（SPEC Q1 禁）
- ❌ 新表 / 迁移 / 写路径（只读面）
- ❌ 历史删除/编辑/重命名 · 标题持久化
- ❌ 前端实现（F1/F2 专项 SPEC 另立 · Q4）
- ❌ 改 `app/ops/chat/**`（legacy 面 · 除裁定 B 明确落点外零 diff）
- ❌ OA 签名面 / HITL 决策面（B2 另 task）
- ❌ 改 `app/ops/lg_rag/multi/**` 图拓扑 / `chat/graph.py`

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 读他人 thread / 未知 thread | **404** · 不泄露存在性（FP-1） | 否 | 校验错误 |
| 未登录 | 401 | 是 | 登录 |
| 大 thread（多 run / 长 answer） | 聚合层 `limit` 分页 + 单 run answer 截断 `32000` 字符（标 `answer_truncated`）· 聚合超时 `10s` → **504**（FP-2/N3） | 是（缩小 limit/重试） | 分页/截断标记/504 |
| 老 run 缺 query（裁定 A 未覆盖的存量帧） | 标题降级 run_id 前缀+时间 · 列表不阻塞（FP-4） | n/a | 降级标题 |
| 事件落盘有缺口（persist 失败历史） | 按现有帧如实重建 · 不伪造 · 不报 500 | 是 | 历史可能缺帧 |
| `thread_id` 非法/超长 | 422（Query 校验） | 是 | 校验错误 |
| SSE 面被误改 | **拒收**（验收钉 `sse_stream.py` 对拍） | 是 | — |
| 30 未签 `HG-AUDIT-R1` 即改码 | **拒开工** | 是 | 须先 20 + 人签 |

---

## 验收标准

- [ ] H1：造 2 run 同 thread + 1 run 异 thread（同用户）→ 列表 2 thread；字段族齐（`thread_id`/`title`/`last_activity_at`/`run_count`/`latest_run_status`）；`waiting_approval` 最新态可识别；按 `last_activity_at` 倒序
- [ ] H1 分页：默认 `limit=20`；`limit>100` → **422**；`limit`+`cursor` 不重不漏（造 >limit 条 thread 断言）
- [ ] H2：完整重建 query + answer 聚合 + subtask 摘要 + `done.status` + `hitl.waiting` requests；run 升序 · 帧序（seq）正确
- [ ] answer 聚合：终帧 `{"content","final":true}` 优先；无终帧回退 delta 按 seq 拼接；超 `32000` 字符截断并标 `answer_truncated=true`（N3 阈值钉）
- [ ] 跨用户访问 → **404**（不 403 · 不泄露存在性）
- [ ] 缺 query 老 run / `waiting_approval` run：标题降级不阻塞（FP-4）
- [ ] 聚合超时阈值 `10s` → 504（FP-2 · 常量可注入）
- [ ] SSE 面按 A1：仅 `run.start` payload +可选 `query` 键且**零新 event_type**；`app/ops/lg_rag/sse_stream.py` 其余 diff 为空（`hitl.waiting`/`done`/`answer`/`subtask.progress` 帧语义零改动）
- [ ] `app/ops/chat/**` 零 diff（裁定 B1）
- [ ] `.venv/bin/pytest tests -q --tb=short` 绿（新增 `tests/test_chat_history_api.py`）
- [ ] **旧测 grep 影响面**：清点 `run.start` 既有断言面（`tests/test_lg_rag_sse_stream.py:101-102` · `tests/test_lg_rag_session_continuity.py:166-167` · `tests/test_multi_replica_dualproc.py:420-424` · `tests/test_lg_rag_sse_token_stream.py:183/254` · `tests/test_chat_ws.py:226/275`）并列入回归；新增可选 `query` 键 **subset-安全**（既有断言取子集字段、排序对拍双端一致，不断言 payload 恰等三键）
- [ ] `app/ops/lg_rag/history_router.py` 鉴权 import 走同族间接取（或显式 `ignore_imports` 授权）；`.venv/bin/lint-imports --config .importlinter` 绿
- [ ] `./scripts/graph-compile.sh` exit 0；G-L1 备注落盘 + `HG-GRAPH-MODULES` 签录
- [ ] `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` 通过

---

## 依赖

- SPEC：`docs/spec/chat-history-hitl-ux/SPEC-chat-history-hitl-ux_v0.md`（signed · §2 B1 · §4 Q1/Q6 · §5 · §6）
- SPEC 审查：`docs/harness/reviews/spec_chat_history_hitl_ux_audit_R1_20260930.md`
- 码面真值：`app/ops/lg_rag/event_store.py` · `app/ops/lg_rag/sse_stream.py:343-347/458-473` · `app/ops/lg_rag/thread_store.py` · `app/db/models.py:290-344` · `.importlinter`（chat-outbound / lg-rag-outbound）
- 先例：`docs/tasks/done/task_lg_rag_sse_resume.md`（T4 事件表/cursor 归属语义）
- A1 errata：`docs/spec/chat-history-hitl-ux/ERRATA-chat-history-hitl-ux_v0_20260930.md`
- 标准：`docs/standards/CODING_BACKEND_L2_v1_zh.md`

---

## 给执行帽的必读列表

1. 本 task（含「已定夺」裁定 A/B）
2. SPEC §2 B1 · §4 Q1/Q6 · §5 FP-1/2/4 · §6 B1
3. `app/ops/lg_rag/event_store.py`（`run_owner`/`assert_run_owned`/`load_events_after`）
4. `app/ops/lg_rag/sse_stream.py:287-347`（事件帧真形）· `:427-473`（HITL 挂起/收口帧）
5. `app/db/models.py:290-344`（三表列真值）
6. `.importlinter`（chat-outbound / lg-rag-outbound）
7. `docs/standards/CODING_BACKEND_L2_v1_zh.md` · `docs/_tech_graph/l1/01_modules.md` · `10_flow_lg_rag.*`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | SPEC signed + D2 实战链 + 代码锚点真读（`run.start` 无 query 实测） | no | — | 无 |
| R1 | 范围 H1-H6 钉死；非范围锁 SSE（除 A1 已批）/checkpoint/chat 包；裁定 A/B 已定夺落定 | no | — | 无 |
| R2 | 真源=事件表（Q1）；返回=服务端聚合消息视图（Q6）；模块落 lg_rag 保 import 边界（裁定 B） | no | — | 无 |
| R3 | FP：404 不泄露 / 分页与截断 / 超时 504 / 老 run 降级 / SSE 误改拒收 | no | — | 无 |
| R4 | 验收全可 pytest 机断（造行→断言）+ diff/lint/图谱命令 | no | — | 无 |
| R5 | 可交 20；裁定 A/B 已定夺（A1/B1）· 无未决项 | no | — | 无（A1 已采纳：pending run 历史含 query；存量旧 run 无 `query` 键按 FP-4 降级） |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：见 R5

### R0 · 问题框定

D2 冒烟三缺口之一：无历史 API / 刷新即丢。SPEC Q1/Q6 已裁定真源与返回形态。

### R1 · 开工闸

`HG-TASK-DRAFT`/`HG-AUDIT-R1`/`HG-GRAPH-MODULES` 均 pending（10 不代签）。范围静态：只读、零表、默认零 SSE。

### R2 · 竖切

H1/H2 两端点 + H3 纯函数 + H5 查询复用；模块归属见裁定 B1。

### R3 · 失败语义

见 failure_paths：最锋利边界 = 归属 404 不泄露 + SSE freeze 零动 + 大 thread 有界。

### R4 · 可测性

造事件行（不连 LLM）→ 列表/回放/404/降级/分页全可断言；契约面用 diff。

### R5 · 交付判定

可交 20-task-audit；裁定 A/B 已由维护者令落定（A1/B1），无未决项。

### 自检结论

（10-task · 2026-09-30 · 含 20 R1 回填）范围 H1–H6 钉死 · 非范围八条 · 验收 14 条可机断（含「旧测 grep 影响面」）· failure_paths 8 条 · 裁定 A1/B1 已按维护者令采纳 · import 间接取纪律钉定（N1）· 分页默认/超限 422（N2）· 思考轮 R0–R5 齐全 · 未签任何 human_gate · 未改 `app/`/`tests/`。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-09-30 | 10-task 立稿：拆自 SPEC chat-history-hitl-ux §2 B1；锚点真读发现 `run.start` 无 query（SPEC 内部冲突）→ 裁定 A 上抛；模块归属 import-linter 边界 → 裁定 B 上抛；N3 截断/超时阈值钉定 |
| 2026-09-30 | 维护者令「冲突部分安全推荐方案进行」→ 裁定 A 采纳 A1（`run.start` 增可选 `query` 键）· 裁定 B 采纳 B1（路由落 `lg_rag/history_router.py`）；阻塞解除 |
| 2026-09-30 | **20-task-audit R1 退回 10-task**（唯一阻塞：行为变更类缺「旧测 grep 影响面」）→ 回填：验收+test_strategy 增旧测影响面（`run.start` 断言面清点 · subset-安全）· 钉 import 间接取纪律（N1）· 分页默认 20/超限 422（N2）· 更正 R1/R5 陈旧文字（N3）· A1 errata 落独立便签（N4）；待 R2 复审 |
| 2026-09-30 | **20-task-audit R2 通过**（0 阻塞 · R1 退回项 5/5 闭合 · 审查文 `docs/harness/reviews/task_chat_history_api_audit_R2_20260930.md`）→ 维护者签 `HG-TASK-DRAFT`/`HG-AUDIT-R1` = approved；30 可开工 |
