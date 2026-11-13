# Task：P0' T2a 旧 chat 计算栈清除——图/服务/节点/状态/流式 + 死测试 + 死冒烟脚本

> **状态**：in_progress  
> **类型**：遗留清除  
> **关联图谱**：`docs/_tech_graph/l1/01_modules.md`（chat 行备注追加 T2a 清除记录 + 概念表 ChatState/SseEvent 行标注）  
> **落盘**：`docs/tasks/active/task_p0prime_t2_chat_legacy_cleanup.md`；验收后 `git mv` → `docs/tasks/done/`  
> **来源**：ops-desk-workspace `docs/01-scope/03-general-agent/06-kickoff-readiness.md` 任务卡 T2（issue #23 Round 4 裁定 A3②）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `p0prime-t2-chat-legacy-cleanup` |
| **test_strategy** | `required` |
| **test_strategy_note** | 删除整份死测试 3 件；部分手术 4 件（chat 耦合用例删除/改写）；改写 1 件用 lg-rag `complete_answer_streaming` 承接「流式中途失败零重试」纪律 |
| **code_quality_bar** | `recommended` |
| **orchestration** | P0' 任务卡 T2（紧随 T1；范围裁定拆 T2a/T2b，见下） |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/p0prime-t2-chat-legacy-cleanup` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `note-only` |
| **graph_delta_note** | 不新增模块/节点/边；`01_modules.md` chat 行备注追加 T2a 清除记录，概念表 ChatState/SseEvent 行标注，10_flow_chat.md / 11_flow_sync_to_chat.md 头部加退役注记；HG-GRAPH-MODULES 追加签收行 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack |
| **review_hat** | `20` |
| **close_pr_policy** | `required` |
| **experience_capture** | `recommended` |
| **kpi_rubric** | `KPI_RUBRIC_v1_2` |
| **kpi_aggregator** | `CLOSE` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| **HG-TASK-DRAFT** | approved | 22-R1, 30 | 维护者授权（issue #23 R4 评论 + 会话 m00177「签收，开始」） |
| **HG-AUDIT-R1** | approved | 30 | 维护者会话签收（m00177「签收，开始」，覆盖 P0' T1–T7 全部任务卡） |
| **HG-GRAPH-MODULES** | approved | 30 | 仅备注追加/退役注记，不新增一级模块；签收行见 `01_modules.md` |

---

## 背景与目标

旧 chat 主线（StateGraph + SSE）自 2026-08-31 T6 起 410 收口，传输主线由 lg-rag SSE 承继；P0' T1 已摘 WS。残留 `app/ops/chat/` 计算栈（graph/service/nodes/rag_nodes/state/streaming/sse 共 7 件）为**零运行时消费者**的死码：`app/ops/router.py` 仅挂 `chat/router.py`（410 墓碑 + models + sessions/latest），不触计算栈。

**范围裁定（组织人 · 2026-11-13 · 对任务卡 T2 原文的拆分）**：卡 T2 原文含「归档导出后 alembic drop ops_runs/ops_run_events/ops_sessions_chat」。30 前勘察发现 **web 仓活依赖** `GET /ops/chat/sessions/latest`：`ops-desk-web/src/api/chat.ts:22` 封装 + `src/stores/chat.ts:552` 调用，且 :872/:903 以 `session.value` 为发送/续答硬门——直接 410/drop 会打断 web 聊天发送链路（跨仓前置，单仓纪律禁同波次跨仓改码）。故拆：

- **T2a（本卡）**：纯代码面清除——删 7 件死码 + 死测试 + 死冒烟脚本，卡验收「全仓零旧 ChatState 引用」在本卡达成。
- **T2b（后续卡，另落）**：`/chat/models` + `/chat/sessions/latest` 410 化 + 归档导出 + alembic drop 三表；前置 = web 仓摘除 session 硬门（另起 web task）+ prod 归档导出 runbook。卡验收「迁移 up/down 通过」随之移交 T2b。

**完成态**：

- [ ] 删除 `app/ops/chat/{graph,service,nodes,rag_nodes,state,streaming,sse}.py` 七件。
- [ ] 保留 `chat/__init__.py`（docstring 改墓碑注记）、`chat/router.py`（三端点全留：stream 410 墓碑 + models + sessions/latest live）、`chat/schema.py`。
- [ ] 删除死测试整件：`tests/test_chat_nodes.py`、`tests/test_chat_service.py`、`tests/test_rag_nodes.py`。
- [ ] 测试手术：`test_llm_retry.py`（改写 stream 纪律用例至 lg-rag `answer_stream` 承接）、`test_llm_routing.py`（删 `TestAnswerNodeRouting`/`TestGradeNodeRouting` 两类 chat 接线用例）、`test_llm_usage.py`（删 `test_answer_node_wires_run_context`）、`test_rag_embedder.py`（删 `test_rag_nodes_wiring_uses_factory`）、`test_rag_reranker.py`（删 `test_retrieve_node_disabled/enabled` 两件）。
- [ ] 删除死冒烟脚本：`scripts/rag_smoke.py`、`scripts/trace_smoke.py`（CI/工作流零引用已核实）。
- [ ] docstring 同步：`app/ops/lg_rag/__init__.py`（去「默认不挂 chat/graph」旧表述）、`app/llm/usage.py`（writer 面枚举去 chat）。
- [ ] 图谱：`01_modules.md` chat 行备注 + 概念表两行标注 + 签收行；`10_flow_chat.md` / `11_flow_sync_to_chat.md` 头部退役注记。
- [ ] N3 自注册：`registry.yaml` 追加本波次 entry（status=active · base=`77a1102`）。

**不做**（非范围）：

- `chat/router.py` / `chat/schema.py` 零 diff（三端点行为不变，`test_chat_router.py` 不动）。
- `app/db/models.py` 三表类与 alembic 零 diff（T2b）。
- `tests/test_chat_history_api.py`（lg-rag 历史 API 测试，与旧 chat 无关）零 diff。
- `scripts/graph_coverage_check.py` R4 规则零 diff（10_flow_chat.graph.yaml 保留，warn-only 不炸）。
- web / ios / workspace 仓零改动。

---

## 范围

- [ ] `app/ops/chat/graph.py`（删）、`service.py`（删）、`nodes.py`（删）、`rag_nodes.py`（删）、`state.py`（删）、`streaming.py`（删）、`sse.py`（删）、`__init__.py`（docstring 改）
- [ ] `app/ops/lg_rag/__init__.py`（docstring 一行）、`app/llm/usage.py`（docstring 一行）
- [ ] `tests/test_chat_nodes.py`（删）、`tests/test_chat_service.py`（删）、`tests/test_rag_nodes.py`（删）
- [ ] `tests/test_llm_retry.py`（1 用例改写）、`tests/test_llm_routing.py`（删 2 类）、`tests/test_llm_usage.py`（删 1 用例）、`tests/test_rag_embedder.py`（删 1 用例）、`tests/test_rag_reranker.py`（删 2 用例）
- [ ] `scripts/rag_smoke.py`（删）、`scripts/trace_smoke.py`（删）
- [ ] `evals/golden/run_eval.py`（30 实施新增：`GRADER_MODEL`/`GRADER_PROVIDER` 两常量内联承接——原 import 自已删 chat/rag_nodes；语义逐字保持）
- [ ] `docs/_tech_graph/l1/01_modules.md`、`10_flow_chat.md`（注记）、`11_flow_sync_to_chat.md`（注记）
- [ ] `docs/harness/audit_gates/registry.yaml`（N3 自注册）

## 非范围

- `app/ops/chat/router.py`、`app/ops/chat/schema.py`、`app/db/models.py`、`alembic/**`。
- `docs/_tech_graph/l1/10_flow_chat.graph.yaml`、`11_flow_sync_to_chat.graph.yaml`（yaml 不动，仅 .md 加注记）。
- `tests/test_chat_router.py`、`tests/test_chat_history_api.py`、`tests/test_prompt_packs.py`。
- web / ios / workspace 仓。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 残留 import 引用已删 chat 模块 | 启动/导入 ImportError | 修复引用 | CI 红 / 服务启动失败日志 |
| 测试手术误伤 lg-rag 覆盖 | pytest 红 | 修正用例 | CI 红 |
| 改写后 stream 纪律用例断言错语义 | 测试红或假绿 | 对照 `answer_stream.py` 实际语义修正 | CI 红 |
| router 三端点被误删/行为漂移 | `test_chat_router.py` 红 | 恢复 | CI 红；web 发送链断 |
| 在途面触碰 scripts/ 触发波次闸 | `test_wave_gate_registry` 红（O2 语义） | 提交后自清 | 本地红（CI 干净树绿） |

---

## 验收标准

- [ ] 全仓零旧 `ChatState` 引用（`grep -rn "ChatState" app/ scripts/ tests/` 为零；docs/tasks 历史文档除外）。
- [ ] 全仓零 `app.ops.chat.{graph,service,nodes,rag_nodes,state,streaming,sse}` 引用。
- [ ] `chat/router.py` 三端点行为不变：`tests/test_chat_router.py` 全绿（410 墓碑 + models + sessions/latest）。
- [ ] 干净环境（无 .env 残留污染、无在途面）全量 `pytest` 零新增红。
- [ ] `ruff check app tests` 通过。
- [ ] `./scripts/graph-compile.sh` 通过。
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_p0prime_t2_chat_legacy_cleanup.md` 通过。
- [ ] 提交到 `task/p0prime-t2-chat-legacy-cleanup` 并创建 PR。

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/tasks/done/task_p0prime_t1_ws_shutdown.md`（T1 先例：仪式/闸/在途面提交先行工作流）
3. `app/ops/router.py`、`app/ops/chat/router.py`（保留面）
4. `app/ops/lg_rag/answer_stream.py`（stream 纪律承接面）
5. `tests/test_llm_retry.py`、`tests/test_llm_routing.py`、`tests/test_llm_usage.py`、`tests/test_rag_embedder.py`、`tests/test_rag_reranker.py`
6. `docs/harness/audit_gates/README.md`（N3 自注册程序）

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题框定：7 件死码零运行时消费者（router 仅挂 chat/router.py）；卡 T2 的 drop 三表部分被 web 活依赖阻塞 | no | — | T2b 拆分偏差需 issue #23 记录 |
| R1 | 开工闸：三闸 approved（m00177 覆盖 T1–T7） | no | — | 无 |
| R2 | 竖切：单 PR——删 7 件 + 测试删/改写 + 脚本删 + docstring/图谱同步 + N3 登记 | no | — | 在途面闸咬（scripts/）以提交先行消解（T1 已实证） |
| R3 | 失败语义：最锋利边界 = 残留 import 与测试手术误伤；grep 零残留 + 干净环境全量 pytest 兜底 | no | — | `__pycache__` 陈旧 .pyc 不属 git 面 |
| R4 | 可测性：stream 纪律改写件钉 lg-rag `complete_answer_streaming` 真实语义（中途异常→降级整段 complete，complete_stream 仅调一次）；`test_chat_router.py` 全绿钉保留面零漂移 | no | — | 无 |
| R5 | 交付判定：范围 23 文件钉死、非范围六条、验收 8 条可机断，可交 30 | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：T2b 拆分偏差需 issue #23 记录

### R0 · 问题框定

`app/ops/chat/` 计算栈 7 件零运行时消费者（全仓 import 闭包自查：仅 chat 包内部互引 + 死测试 + 2 冒烟脚本）。卡 T2 原文 bundle 的 alembic drop 三表被 web 活依赖 `/chat/sessions/latest`（`stores/chat.ts:552` 调用 + :872/:903 发送硬门）阻塞——单仓纪律下拆 T2a/T2b。

### R1 · 开工闸

三闸 approved：HG-TASK-DRAFT / HG-AUDIT-R1（维护者 m00177 会话签收，覆盖 P0' T1–T7）· HG-GRAPH-MODULES（备注/注记级，签收行回写 `01_modules.md`）。

### R2 · 竖切

单 PR 一次完成：删 7 件死码 → 测试删 3 整件 + 手术 5 件 → 删 2 冒烟脚本 → docstring 两处 → 图谱注记三处 + 签收行 → N3 登记。

### R3 · 失败语义

见 failure_paths：残留 import（ImportError）与测试手术误伤（覆盖丢失）为最锋利边界——全仓 grep 零残留 + 干净环境（无 .env / 无在途面）全量 pytest 兜底，承 T1 实证工作流。

### R4 · 可测性

改写作 `test_no_retry_after_first_content_chunk` 承接至 lg-rag `complete_answer_streaming`：fake provider `complete_stream` 首 chunk 后抛错 → 断言 `complete_stream` 仅调一次（零流式重试）+ 降级 `complete` 返回整段（与 `answer_stream.py:82-89` 语义逐字对齐）。`test_chat_router.py` 全绿钉三端点零漂移。删除件判定：接线用例随被测模块死亡，单元逻辑由在文件内其余用例与 lg-rag 面既有用例承继（`TestResolveTaskModel` / `test_lg_rag_surface_distinguishable` 等）。

### R5 · 交付判定

纯清除 + 承接改写，零新增运行面，可交 30。T2b（端点 410 化 + drop 三表）另落卡，前置 = web 摘除 session 硬门 + prod 归档导出 runbook；拆分偏差将记 issue #23。

### 自检结论

（10-task · 2026-11-13）范围 23 文件钉死 · 非范围六条（router/schema/models/alembic/yaml/三测试件不动 · 跨仓零改动）· 验收 8 条可机断 · failure_paths 5 条 · 思考轮 R0–R5 齐全 · 闸表三签（m00177）· 范围拆分裁定含 web 活依赖证据链（`chat.ts:22` / `stores/chat.ts:552,872,903`）。

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| （待回填） | | |

---

## 测试策略（Harness）

**test_strategy**: `required`

- 删除整件 3：`test_chat_nodes.py` / `test_chat_service.py` / `test_rag_nodes.py`（被测模块已删）。
- 手术 5：`test_llm_retry.py` 改写 1 用例（lg-rag 承接）；`test_llm_routing.py` 删 `TestAnswerNodeRouting` + `TestGradeNodeRouting`；`test_llm_usage.py` 删 `test_answer_node_wires_run_context`；`test_rag_embedder.py` 删 `test_rag_nodes_wiring_uses_factory`；`test_rag_reranker.py` 删 `test_retrieve_node_disabled_does_not_call_rerank` + `test_retrieve_node_enabled_reranks`。
- 保留钉：`test_chat_router.py` 全绿（三端点零漂移）。
- 全量 `pytest`（干净环境）+ `ruff check` + grep 零残留。

---

### 自检结论（执行者）

（回填）

---

### KPI（00）

（关账回溯填写）

---

### 经验总结

（关账必填）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-11-13 | 创建 task（issue #23 R4 任务卡 T2 · 组织人范围裁定拆 T2a/T2b；维护者 m00177「签收，开始」） |
