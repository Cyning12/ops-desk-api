# Task：Capability Gateway · P1（schemas_for_llm + 可选 ToolNode adapter）

> **状态**：completed（P1 50 PASS · 同分支待合入；2026-08-26）  
> **上游 SPEC**：`docs/spec/agent-infra/SPEC-capability-gateway_v0.md` §4 P1  
> **前置**：capability-gateway-p0 CLOSE PASS  
> **分支**：`task/capability-gateway`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `capability-gateway-p1` |
| **git_branch** | `task/capability-gateway` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | schemas_for_llm 形状单测；ToolNode adapter smoke（mock）；不强制挂主路径；不连真外网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` 或 `none` |
| **graph_delta_note** | 可选备注；不增一级模块 |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签；`task_capability_gateway_p1_audit_R1_20260826.md` |
| HG-GRAPH-MODULES | approved | 30 | 不增一级 |

---

## 背景与目标

P0 已有 Registry/invoke。P1 补 `schemas_for_llm`（供 bind_tools / ToolNode 可选），并提供可选 ToolNode adapter smoke（**不**强制挂 lg_rag 主路径）。

---

## 范围 / 非范围

**范围**：`schemas_for_llm(*, filter)`；可选 thin ToolNode/LangChain tool 适配（单独可测）；文档注释说明不挂主路径；单测。

**非范围**：MCP/sandbox/cli（P2）；skill（P3）；改 chat/graph.py；强制改 supervisor/tool_exec 主路径为 FC；Agently。

---

## 验收标准

- [x] `schemas_for_llm` 对已注册带 args_schema 的能力返回可序列化 list[dict]
- [x] Filter 生效（kinds/tags 等最小）
- [x] ToolNode adapter 或等价 smoke 单测（可 mock）；**不**改 multi/graph 拓扑为必挂
- [x] P0 multi 单测不回归
- [x] ruff / pytest 绿；chat/graph.py 零 diff；无 Agently

---

## failure_paths

| 触发 | 行为 | 可重试 |
|---|---|---|
| 无 args_schema | 跳过或空 schema 条目（注释钉死） | N |
| 误挂主路径破坏 fallback | 打回 | N |

---

## 思考轮

### 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R5 |
| **early_stop** | no |
| **residual_risks** | ToolNode 与 plan 直调双路径并存易混淆——文档写清可选 |

### R0
schemas 优先于强制 FC 挂载。

### R1
不改 multi 图拓扑。

### R2
Filter 复用 P0。

### R3
smoke 即可。

### R4
与 Structured Output 正交。

### R5
multi 不回归。

---

### 自检结论

> 2026-08-26 · 00 **PASS**（30 [Review](6926fcb9-789e-489d-b38f-75cbcc0b7c22)）· 20 passed

**50 结论**：PASS · 下一棒 P2

---

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | schemas_for_llm + 可选 ToolNode adapter |
| 归档 | 暂留 active |
| PR | 待全波次 |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 00 起草 P1 |
| 2026-08-26 | 20 R1 pass；00 代签闸 |
| 2026-08-26 | 30/40 PASS；00 50 CLOSE |
