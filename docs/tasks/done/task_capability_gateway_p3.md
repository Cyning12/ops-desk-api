# Task：Capability Gateway · P3（kind=skill 边界）

> **状态**：completed（PR #59 MERGED · 已归档；2026-08-26）  
> **SPEC**：§4 P3 · **前置** P2 · **分支** `task/capability-gateway`

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `capability-gateway-p3` |
| **git_branch** | `task/capability-gateway` |
| **test_strategy** | `required` |
| **test_strategy_note** | skill 预留 API/文档单测；不实现完整 Skill 引擎；对齐 docs/skills/ 边界 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` 或 `G-L1` 一句 |
| **graph_delta** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-26 00 代签 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-26 00 代签 |
| HG-GRAPH-MODULES | approved | 30 | 不增一级 |

## 范围

- `kind=skill`：区分 `provide()` 注入上下文 vs `invoke()` 可执行步骤（预留接口 + 文档）
- 与 `docs/skills/`（人/Agent 读的仓内 Skill）边界文档
- SPEC 修订记录「P0–P3 落地状态」
- 最小 stub/单测（未实现引擎则 assert NotImplemented 或明确 stub 行为）

## 非范围

- 完整 Skill 执行引擎；改 chat/graph；真 MCP；Agently

## 验收标准

- [x] skill 边界文档落盘
- [x] kind=skill 注册/预留 API 有单测或明确 stub
- [x] SPEC §8 修订含 P0–P3 落地状态
- [x] pytest/ruff 绿；chat/graph.py 0

### 自检结论

> 2026-08-26 · 00 **PASS**（30 [Review](5f02faa7-faeb-45be-b125-0d2eac62e454)）· 触及 40 passed

**50 结论**：PASS · 全波次收官 · 待 PR

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | skill provide/invoke stub + 边界文档 + SPEC 落地状态 |
| 归档 | `docs/tasks/done/task_capability_gateway_p3.md` |
| PR | [#59](https://github.com/Cyning12/ops-desk-api/pull/59) MERGED |

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 00 起草 P3 |
| 2026-08-26 | 20 R1 pass；00 代签闸 |
| 2026-08-26 | 30/40 PASS；00 50 CLOSE；全波次收官 |

| 2026-08-26 | 归档：PR #59 MERGED · git mv → docs/tasks/done/ |
