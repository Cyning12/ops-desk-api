# Task Audit R1：lg-rag-session-continuity

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_lg_rag_session_continuity.md`  
> **上游 SPEC**：`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4 · §9 · §10.2 · `session/ROADMAP_lg_rag_session_continuity_v0.md`（本波仅 L-a / L-b / L-d）  
> **先例**：`docs/harness/reviews/task_lg_rag_sse_stream_updates_audit_R1_20260830.md`（T2 · 同 freeze / 同非 chat 兼容）  
> **日期**：2026-08-31 · 审查人：20-task-audit  
> **10 lint**：PASS（W4 无思考轮节 · SPEC 承载合法）

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **pass** · 零阻塞 · 不退回 10 |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（正确 · 20 不代签）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 已 approved |
| **30 授权** | **未签发** · pending 时禁止附 30 Prompt；真值仍在 task 人工闸表 |

---

## 审查核对（对照 SPEC / ROADMAP / 先例）

| 审查点 | 结论 |
|--------|------|
| 范围是否越到 T4 replay / T5 / T6 / C0–C4 | **未越界**。范围钉 L-a/L-b/L-d；非范围逐条排除 L-c/T4（seq/cursor/replay/resume/`cursor` 事件）、T5 token delta、T6 删 `/chat/stream`、C0–C4 Host 沟通轨。`test_strategy_note` 写明不测 replay；验收禁止 replay/cursor/resume 断言 |
| 是否要求兼容 chat 事件或强合并 chat 表 | **否**。非范围：双写兼容 `/chat/stream`、chat `thinking` 1:1、强合并 `ops_sessions_chat`、以 `ops_runs.session_id` / `GET /chat/sessions/latest` 为 SoT。对齐 `05` §4.1 / §5 / §10.2 与 session ROADMAP「非 chat 兼容」 |
| 是否 lg_rag→chat 依赖 | **禁止且可测**。压缩可参考 H3 `compress_window` 但允许重写；验收：`app/ops/lg_rag/**` 不 import `app.ops.chat` / `app.ops.session`。对齐 `01_modules.md` 现网出边（无 chat） |
| freeze 是否沿用 `lg-rag-sse-v1` | **是**。`freeze_id` + 00 定夺：不新开 freeze、不新增 `event_type`；请求已有可选 `thread_id`，`run.start` 已回写。对齐 T2 冻结与 `05` §4.2 / §10.0 |
| 行为变更 · 旧测 grep 影响面 | **已列**（不退回）。`tests/test_lg_rag_sse_stream.py` 帧序仍绿；`tests/test_session_continuity.py`（chat H3）零破坏；`chat/graph.py` 零 diff |
| 思考轮无 R0–R5 节（W4 · SPEC 承载） | **不退回**。task 自检结论写明思考轮由 `05` + session ROADMAP 承载；本文件不预置 R0–R5。20 不把缺节当内容阻塞 |
| 跨用户 thread → 404 | **已钉**（10 补钉 · 00 定夺接受）。验收 + failure_paths：404；不注入他用户历史；不静默当本用户新会话。不泄露他用户 thread 是否存在。落在 `05` §4.3「非法 thread_id → 4xx」内 |

其余可执行性：验收含同 thread 续写注入、异 thread 隔离、窗口压缩（过短 noop / 失败截断尾部）、缺 `thread_id` 仍 200 且响应头带回 id、401/422/404、G-L2 indexes 条件同步、`05` §10.2 回写。failure_paths 覆盖历史加载失败（不 500 打断 SSE）、压缩失败、落盘失败、图异常维持 T2。合入策略：api-only 可先合、勿 auto-merge、web 另 task——与 `05` §10.2 / §11 一致。

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 30 知情即可）

1. **DDL 未钉死**：独立 thread 面写「建议 `ops_lg_rag_threads` + turns，或等价轻表」。30 须自选并迁；只要不合并 chat 表、不以 chat `session_id` 为 SoT 即可。  
2. **落盘是「尽量」**：`done` 后写 turns 失败只打日志、不阻断已发出 SSE；下次可能缺本轮（已在 failure_paths）。  
3. **api-only 窗口**：web 未带稳定 `thread_id` 时每问仍可能新 uuid，行为不低于 T2；产品多轮依赖另开 web task。  
4. **压缩默认 N**：对齐「H3 思路」未钉具体 `max_full_turns` 数字；30 应对齐 H3 默认或在实现/文档写明本波默认。  
5. **invoke HTTP**：图输入钉 `_ainvoke/_astream`，验收主路径写 `/lg-rag/stream`（或装配函数）；invoke 走同一装配即可，不必单开 HTTP 条。

---

## 回填清单

无（内容零阻塞 · 不改 task 实质 · 不改人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-AUDIT-R1` 仍 pending，**不**指示 30 开工。

---

## 维护者签闸（20 后 · 30 前）

- [x] 已读 R1 审查结论
- [x] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（**00 代签 · 维护者 Prompt 授权** · 2026-08-31）
- [ ] commit task 文档或确认已签（T3 分支待 00 提交过程档）
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
