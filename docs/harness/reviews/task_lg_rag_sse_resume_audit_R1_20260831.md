# Task Audit R1：lg-rag-sse-resume

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_lg_rag_sse_resume.md`  
> **上游 SPEC**：`docs/spec/agent-infra/05_lg_rag_transport_and_session_plan_v0.md` §4.2 · §4.3 · §9 · §10.3 · `session/ROADMAP_lg_rag_session_continuity_v0.md`（本波 **仅 L-c**）  
> **先例**：`docs/harness/reviews/task_lg_rag_session_continuity_audit_R1_20260831.md`（T3 · 同 freeze / 同非 chat 依赖禁区）  
> **日期**：2026-08-31 · 审查人：20-task-audit  
> **10 lint**：PASS（W4 无思考轮节 · SPEC 承载合法）· `dsh-coding-kit@1.10.0 task lint`

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
| 范围是否仅 L-c；未重开 T3 / T5 / T6 / C0–C4 | **未越界**。范围钉 L-c（seq/cursor · 事件存储 · `POST /replay` · 相对 T2 续看）。非范围逐条排除：T3 重做（thread/压缩/历史）、重开 L-a/L-b/L-d、T5 token delta、T6 删 `/chat/stream`、C0–C4 Host 轨、改 `chat/graph.py` 拓扑。对齐 ROADMAP L-c ↔ L0 T4；`05` §10.3 |
| 是否 lg_rag→chat/session 新依赖 | **禁止且可测**。非范围 + 验收：`app/ops/lg_rag/**` 不 import `app.ops.session` / `app.ops.chat`；禁复用 chat SSE 事件表；思想可参考 `sse_replay.py` 但禁止依赖。对齐 `05` Session「非 chat 兼容」与 ROADMAP「允许重写」 |
| freeze 是否扩展 `lg-rag-sse-v1`（顶层 cursor，非强制 `event_type=cursor`） | **是 · 不退回 00**。`freeze_id` + 00 定夺：沿用 `lg-rag-sse-v1`；规范化可选顶层 `cursor`（`run_id:seq`）+ 新增 replay HTTP；**禁止** silently 扩 `event_type`；非范围钉死「不强制每帧另发 `event_type=cursor`」。§4.2 表内 `cursor` 行仍为可选；本波 SoT=顶层字段，验收要求回写 `05` §4.2 / §10.3——与「不 silent 扩」一致，**不**坚持拆新 freeze id |
| 存储新表 + POST /replay + 断连仍跑完 + 404 | **已钉**。新表 `ops_lg_rag_run_events`（建议列已列）；live path 不变 + **新** `POST /api/ops/lg-rag/replay`（与 live 语义分离）；断连相对 T2 **不**引入 cancel、仍尽量跑完；未知/跨用户 `run_id` → **404**（对齐 T3 不泄露）。failure_paths 覆盖落盘失败不阻断 SSE、replay 只返回已提交帧 |
| 行为变更 · 旧测 grep 影响面 | **已列**（不退回）。`tests/test_lg_rag_sse_stream.py` 帧序仍绿（可扩 cursor 断言）；`tests/test_session_continuity.py`（chat H3）零破坏；`tests/test_lg_rag_session_continuity.py`（T3）零破坏；`app/ops/chat/graph.py` **零 diff** |
| 思考轮无 R0–R5 节（W4 · SPEC 承载） | **不退回**。task 自检结论写明思考轮由 `05` + session ROADMAP **仅 L-c** 承载；本文件不预置 R0–R5。20 不把缺节当内容阻塞（同 T3 先例） |
| G-L2 / graph 钩子 | **已钩**。`graph_change_layer=G-L1`；备注改 `lg_rag` 行/flow；若增 `implementedBy` → 同步 G-L2 indexes（`05` §9 / §9.3 T4 钩）。不新增一级模块 · `HG-GRAPH-MODULES` 已 approved |

其余可执行性：验收含 live 帧 `run_id`/`seq`/可选 `cursor`、落盘可查、`after_seq` 仅 `>` 重放、重复 after_seq 不重发已收区间、401/404/422、wiki_delta n/a + lint-wiki-delta、ruff/pytest/graph-compile。合入：api-only 可先合、勿 auto-merge、web 断网 UI 另 task——与 `05` §10.3 / §11 一致。

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 30 知情即可）

1. **DDL 建议列**：`ops_lg_rag_run_events` 写「建议列」；30 须自选列类型（payload JSON vs 全文）并迁；只要独立表、不复用 chat 事件表即可。  
2. **落盘是「尽量」**：落盘失败不阻断已发 SSE；replay 可能缺帧（已在 failure_paths）。图仍在写时只返回已提交帧；客户端可再次 replay。  
3. **replay body 双形态**：`{run_id, after_seq}` 或等价 `{cursor}`；30 须在实现/OpenAPI 钉死解析与非法格式 → 422。  
4. **§4.2 回写口径**：表内仍有可选 `event_type=cursor`；本波 SoT=顶层字段。回写时须写清「可选顶层 `cursor`；不强制每帧 `event_type=cursor`」，避免与 freeze 扩展叙事冲突。  
5. **api-only 窗口**：本 PR 不改 Vue；产品「断网续看」依赖另开 web task（`05` §10.3 web 交付）。

---

## 回填清单

无（内容零阻塞 · 不改 task 实质 · **不改**人工闸表 status）。

---

## 签收

**内容签收 · pass**（终轮 R1）。流程闸 `HG-AUDIT-R1` 已由 **00 代签 approved**（维护者 Prompt 授权 · 2026-08-31）；可下发 30。

---

## 维护者签闸（20 后 · 30 前）

- [x] 已读 R1 审查结论
- [x] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（**00 代签 · 维护者 Prompt 授权** · 2026-08-31）
- [ ] commit task 文档或确认已签（T4 分支由 00/30 过程提交）
- [x] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
