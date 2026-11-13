# Task：P0' T1 安全收口——下线未鉴权 demo WebSocket 端点

> **状态**：closed（2026-11-13 · PR [#367](https://github.com/Cyning12/ops-desk-api/pull/367) merge `c557095` · 全量 1900 passed 零红 · registry entry 已转 closed 钉 wave_tip）  
> **类型**：安全收口/遗留清除  
> **关联图谱**：`docs/_tech_graph/l1/01_modules.md`（chat 行备注追加 ws 下线）  
> **落盘**：`docs/tasks/done/task_p0prime_t1_ws_shutdown.md`（CLOSE 已迁档）  
> **来源**：ops-desk-workspace `docs/01-scope/03-general-agent/06-kickoff-readiness.md` 任务卡 T1（issue #23 Round 4 裁定 A3① / P5）

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `p0prime-t1-ws-shutdown` |
| **test_strategy** | `required` |
| **test_strategy_note** | 负向回归：断言 /api/ops/chat/ws 路由不存在（连接被拒/404）；删除针对已删端点的整份旧测试文件 |
| **code_quality_bar** | `recommended` |
| **orchestration** | P0' 任务卡 T1（关键链 T1→T3→T4 之首，安全口子最先行） |
| **semi_auto** | `false` |
| **audit_profile** | `human_only` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **git_branch** | `task/p0prime-t1-ws-shutdown` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `note-only` |
| **graph_delta_note** | 不新增模块/节点/边；`01_modules.md` chat 行备注追加「ws.py 已下线（P0' T1）」，HG-GRAPH-MODULES 追加签收行 |
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
| **HG-GRAPH-MODULES** | approved | 30 | 仅 chat 行备注追加，不新增一级模块；签收行见 `01_modules.md` |

---

## 背景与目标

`app/ops/chat/ws.py` 是旧 chat 时代的 demo WebSocket 端点：**无鉴权**、代码自述「do not expose publicly」、功能已被 lg-rag SSE 完全覆盖。issue #23 Round 3 实地调研将其列为现存安全风险；Round 4 裁定 P5「直接下线，不带闸保留」、A3①「摘路由安全优先独立先行」。本任务为 P0' 关键链第一张卡。

**完成态**：

- [ ] `app/ops/router.py` 摘除 `chat_ws_router` 导入与注册（:11、:33）。
- [ ] 删除 `app/ops/chat/ws.py`。
- [ ] 删除 `app/config.py` `ops_chat_ws_enabled` 开关（P5 裁定不带闸保留，开关随之移除）。
- [ ] 删除 `tests/test_chat_ws.py`（被测端点已不存在）；新增负向回归断言路由缺席。
- [ ] 图谱 `01_modules.md` chat 行备注 + HG-GRAPH-MODULES 签收行。

**不做**：

- 不删 `chat/graph.py`、`chat/service.py`（属 T2）。
- 不动 ops_runs/ops_run_events/ops_sessions_chat 三表（属 T2 归档 drop）。
- 不动 chat/router.py 410 墓碑。

---

## 范围

- [ ] `app/ops/router.py`（摘 chat_ws 导入与注册）
- [ ] `app/ops/chat/ws.py`（删除）
- [ ] `app/config.py`（删 `ops_chat_ws_enabled`）
- [ ] `tests/test_chat_ws.py`（删除）
- [ ] `tests/test_chat_ws_removed.py`（新增负向回归）
- [ ] `docs/_tech_graph/l1/01_modules.md`（chat 行备注 + 闸签收行）

## 非范围

- `app/ops/chat/graph.py`、`app/ops/chat/service.py`、`app/ops/chat/router.py`。
- 数据库迁移（本任务无 DDL）。
- iOS `IMWebSocketClient.swift`（R4-D2 裁定保留冻结，不落本仓）。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| 摘除路由后仍有模块 import ws.py | 启动 ImportError | 修复引用 | 服务启动失败日志 |
| 旧测试文件残留引用已删模块 | pytest 收集失败 | 删除/修正测试 | CI 红 |
| 负向回归误伤其他路由 | 测试失败 | 修正断言路径 | CI 红 |

---

## 验收标准

- [ ] `/api/ops/chat/ws` WebSocket 连接被拒（路由不存在，负向回归测试通过）。
- [ ] 全仓无 `chat_ws_router` / `ops_chat_ws_enabled` / `app.ops.chat.ws` 残留引用（grep 为零，排除 tasks/done 历史文档）。
- [ ] `pytest tests` 全绿。
- [ ] `ruff check app tests` 通过。
- [ ] `./scripts/graph-compile.sh` 通过。
- [ ] `npx spec-wave task lint --file docs/tasks/active/task_p0prime_t1_ws_shutdown.md` 通过。
- [ ] 提交到 `task/p0prime-t1-ws-shutdown` 并创建 PR。

---

## 给执行帽的必读列表

1. `AGENTS.md`
2. `docs/01-scope/03-general-agent/06-kickoff-readiness.md`（workspace 仓，T1 任务卡与 R4 裁定 A3/P5）
3. `app/ops/router.py`
4. `app/ops/chat/ws.py`
5. `app/config.py`
6. `tests/test_chat_ws.py`

---

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|----|------|------------|----------------------|----------------|
| R0 | 问题框定：未鉴权 demo WS 端点挂生产路由（ws.py 自述 do not expose publicly）；R3 调研证据 + R4 裁定 P5/A3① 为真源 | no | — | 无 |
| R1 | 开工闸：HG-TASK-DRAFT / HG-AUDIT-R1 维护者 m00177「签收，开始」批准；HG-GRAPH-MODULES 仅备注追加已回写 | no | — | 无 |
| R2 | 竖切：摘导入/注册 → 删 ws.py → 删配置开关 → 删旧测试 + 负向回归 → 图谱备注；单 PR 一次完成 | no | — | 无 |
| R3 | 失败语义：残留 import 导致启动失败、旧测试收集失败、负向断言误伤——均以 grep+pytest 全绿兜底 | no | — | 无 |
| R4 | 可测性：负向回归 pytest 机断（路由缺席断言）；无 DB 依赖 | no | — | 无 |
| R5 | 交付判定：范围仅删遗留零新增面，可交 30；iOS WS 资产不落本仓（R4-D2） | no | — | 无 |

**actual_last_round**：R5 · **early_stop**：no · **residual_risks**：无

### R0 · 问题框定

`app/ops/chat/ws.py` 为旧 chat 时代 demo WebSocket：无鉴权、自述「do not expose publicly」，功能被 lg-rag SSE 全覆盖。issue #23 R3 实地调研列为现存安全风险；R4 裁定 P5「直接下线，不带闸保留」、A3①「摘路由安全优先独立先行」。

### R1 · 开工闸

三闸 approved：HG-TASK-DRAFT / HG-AUDIT-R1（维护者 m00177 会话签收，覆盖 P0' T1–T7）· HG-GRAPH-MODULES（仅 chat 行备注追加，签收行已回写 `01_modules.md`）。

### R2 · 竖切

单 PR 完成：摘 `app/ops/router.py` 导入与注册 → 删 `ws.py` → 删 `ops_chat_ws_enabled` → 删 `test_chat_ws.py` 新增负向回归 → 图谱备注。

### R3 · 失败语义

见 failure_paths：最锋利边界 = 残留 import（启动 ImportError）与旧测试收集失败——均以全仓 grep 零残留 + pytest 全绿兜底。

### R4 · 可测性

负向回归 `tests/test_chat_ws_removed.py` 断言 `/api/ops/chat/ws` 路由缺席（TestClient 机断，无 DB 依赖）。

### R5 · 交付判定

纯删遗留、零新增面，可直接交 30。iOS `IMWebSocketClient.swift` 属 ops-desk-ios 仓且 R4-D2 裁定保留冻结，不落本任务。

### 自检结论

（10-task · 2026-11-13）范围 6 文件钉死 · 非范围三条（graph/service/三表归 T2 · 410 墓碑不动）· 验收 7 条可机断 · failure_paths 3 条 · 思考轮 R0–R5 齐全 · 闸表三签（m00177）。

---

## 实现备忘（子 Agent 回填）

| 项 | 状态 | 备注 |
|----|------|------|
| （待回填） | | |

---

## 测试策略（Harness）

**test_strategy**: `required`

- 负向回归：`tests/test_chat_ws_removed.py` 断言 `/api/ops/chat/ws` 连接被拒。
- 全量 `pytest tests` 与 `ruff check`。
- grep 残留引用为零。

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
| 2026-11-13 | 创建 task（issue #23 R4 任务卡 T1；维护者 m00177「签收，开始」） |
