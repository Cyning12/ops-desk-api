# Task：Capability Gateway · P0（Registry + local_fn + tool_exec 接入）

> **状态**：completed（PR #59 MERGED · 已归档；2026-08-26）  
> **类型**：feature / agent-infra（Capability Gateway 首波）  
> **上游 SPEC**：`docs/spec/agent-infra/SPEC-capability-gateway_v0.md`（active · `HG-SPEC-SIGNOFF=approved`）  
> **前置**：structured-output-gateway P0–P3 已合入（PR #58）  
> **总轨**：`capability-gateway`（00 切分：P0 / P1 / P2 / P3）  
> **分支**：`task/capability-gateway`  
> **无关**：勿与 `task_ops_sync_sender_migration` 等混改；禁止改 `chat/graph.py`；禁止引入 Agently。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `capability-gateway-p0` |
| **git_branch** | `task/capability-gateway` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | Registry 注册/重复/未知 id；local_fn 成功与抛错；tool_exec 接入后 `tests/test_lg_rag_multi.py` 不回归；不连真外网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` |
| **graph_delta_note** | `lg_rag` 备注：tool_exec 经 Capability Gateway；**不**新增一级模块（新增一级须维护者明示） |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 总轨四子 task：本 task = P0 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签（20 R1 pass） |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`task_capability_gateway_p0_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 仅备注；不增一级模块 |

---

## 背景与目标

`tool_exec_node` 直调 `MOCK_TOOLS` 字典。P0 建立 Capability Gateway 最小面：Registry + `local_fn` adapter，迁移 mock 工具，节点改调 Gateway；行为与现 mock **等价**。

---

## 范围 / 非范围

**范围**：

- 新建包草案：`app/ops/capability/`（register / list / invoke · `CapabilityResult`）
- `local_fn` adapter；将 `MOCK_TOOLS` 迁入注册表（或启动时 register）
- `tool_exec_node` 改调 Gateway；未知 id → `ok=False`，不中断后续子任务
- 观测：invoke 写 span metadata（`capability_id` · `kind` · `ok` · error 截断），兼容现 `trace_span("tool_exec")`
- 单测 + G-L1 `lg_rag` 备注

**非范围**：

- `schemas_for_llm` / ToolNode adapter（→ P1）
- MCP / sandbox / cli 探针（→ P2）；`app/tools/run_code.py` 可保留草稿，**本 task 不强制接入**
- `kind=skill`（→ P3）
- 改 `chat/graph.py` 拓扑；Agently 依赖；升 freeze

---

## 验收标准

- [x] 可 import Gateway：至少 `register` / `list` / `invoke`
- [x] `MOCK_TOOLS` 两枚 mock 经 Gateway 可调用；行为等价（output 形状不劣于改前）
- [x] `tool_exec_node` 不再直读裸字典为主路径（可保留薄兼容 shim，须委托 Gateway）
- [x] 未知 capability_id → 错误结果，图不垮；既有 multi 单测绿
- [x] Registry：重复 id 有明确行为（拒绝或覆盖，注释钉死）+ 单测
- [x] ruff / pytest 触及路径绿；`chat/graph.py` 零 diff
- [x] G-L1 备注 + graph-compile；无 Agently

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 未注册 id | `ok=False`，记入 subtask_results | N |
| adapter 异常 | `ok=False` + error，不中断后续 | Y（上层） |
| 误改 chat graph / 实现 MCP/P1+ | 打回 | N |

---

## 依赖

SPEC §3–§4 P0 · `app/ops/lg_rag/multi/nodes.py` · `CODING_BACKEND_L2` · `FRAGMENT_30`

---

## 给执行帽（30）必读

本 task · SPEC · tool_exec / MOCK_TOOLS · FRAGMENT_30 · CODING_BACKEND_L2

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | 迁移时 tool 名与 plan 字段对齐；观测双写 span 风险——复用现 tool_exec span metadata |

### R0
P0 只 Registry + local_fn + tool_exec。

### R1
不新增一级模块。

### R2
未知 id 容错对齐现行为。

### R3
run_code 草稿不强制接入。

### R4
与 Structured Output Gateway 正交，可组合但不混实现。

### R5
multi 单测不回归。

---

### 自检结论

> 2026-08-26 · 00 机械复检 · **PASS**（30 [Review](109766b3-5b32-4e21-9db2-66aff3466b0e)）

- [x] 验收勾选
- [x] pytest / ruff（17 passed）
- [x] graph.py 零 diff

**50 结论**：PASS · 下一棒 P1

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | Registry + local_fn + tool_exec 迁 MOCK_TOOLS |
| 归档 | `docs/tasks/done/task_capability_gateway_p0.md` |
| PR | [#59](https://github.com/Cyning12/ops-desk-api/pull/59) MERGED |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 00 起草 P0；闸 pending |
| 2026-08-26 | 20 R1 pass；00 代签闸 |
| 2026-08-26 | 30/40 PASS；00 50 PASS；CLOSE |

| 2026-08-26 | 归档：PR #59 MERGED · git mv → docs/tasks/done/ |
