# Task：Capability Gateway · P2（MCP / sandbox / cli 探针）

> **状态**：completed（P2 50 PASS · 同分支待合入；2026-08-26）  
> **SPEC**：§4 P2 · **前置** P1 CLOSE · **分支** `task/capability-gateway`

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `capability-gateway-p2` |
| **git_branch** | `task/capability-gateway` |
| **test_strategy** | `required` |
| **test_strategy_note** | 各 kind 至少 1 个 mock 探针；默认关闭；不连真外网 CI |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `G-L1` |
| **graph_delta** | `docs/_tech_graph/l1/01_modules.md` 或 `none` |
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

- MCP / sandbox / cli adapter **各至少 1 个探针**（mock，默认 enabled=false 或不进 defaults）
- 文档说明如何开启；单测 mock
- 可选：`app/tools/run_code.py` 作 cli/sandbox 探针包装（若接入须默认关闭）

## 非范围

- 真 MCP client / 生产 sandbox；skill（P3）；改 chat/graph；Agently；强制开启探针进 CI 默认路径

## 验收标准

- [x] 三 kind 探针可 register + invoke（mock）
- [x] 默认关闭：默认 Gateway defaults 不暴露真外网
- [x] 文档短文或模块 docstring
- [x] pytest/ruff 绿；chat/graph.py 0；multi 不回归

### 自检结论

> 2026-08-26 · 00 **PASS**（30 [Review](ee799432-1a82-4063-a532-a266f1fadc22)）· 24 passed

**50 结论**：PASS · 下一棒 P3

## CLOSE

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-26 |
| 定稿 | MCP/sandbox/cli mock 探针（默认关闭） |
| 归档 | 暂留 active |
| PR | 待全波次 |

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-26 | 00 起草 P2 |
| 2026-08-26 | 20 R1 pass；00 代签闸 |
| 2026-08-26 | 30/40 PASS；00 50 CLOSE |
