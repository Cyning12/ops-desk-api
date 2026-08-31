# Task：Langfuse 上报 `cached-input-tokens`

> **状态**：completed（2026-08-31 · PR [#101](https://github.com/Cyning12/ops-desk-api/pull/101) **MERGED**）  
> **类型**：observability / tracing  
> **上游**：[`task_siliconflow_default_catalog_cost`](./task_siliconflow_default_catalog_cost.md)（已归档）· SiliconFlow usage `prompt_cache_hit_tokens` / `prompt_tokens_details.cached_tokens`  
> **分支**：`task/langfuse-cached-input-tokens`  
> **帽子**：10 / 20 R1 / 30 已交付。  
> **无关**：改 Host 价表数值；删 Bailian；Langfuse SDK v4；改 chat/graph 拓扑；Batch 推理通道。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `langfuse-cached-input-tokens` |
| **git_branch** | `task/langfuse-cached-input-tokens` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock usage 含 `prompt_cache_hit_tokens` / `prompt_tokens_details.cached_tokens`；断言 Langfuse `usage_details` 含 `cached-input-tokens` 且 `input` 为 exclusive（prompt−cache）；不连真网 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `minimal` |
| **close_pr_policy** | `required` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | — | 2026-08-31 · 维护者令开本波 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-31 · 维护者 Prompt 授权 · 见 reviews |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 |

---

## 范围

1. `LlmUsage` 增加 `cached_input_tokens`；从 Provider usage 解析（优先 `prompt_cache_hit_tokens`，否则 `prompt_tokens_details.cached_tokens`）。
2. `update_current_generation_usage` 上报 Langfuse：`input`（不含 cache）· `output` · **`cached-input-tokens`**（对齐 SiliconFlow 账单后缀）。
3. `complete()` 聚合路径与 Chat `nodes.py` 流式路径共用解析。
4. 单测 + GUIDE 一句。

### failure_paths

| 路径 | 预期 |
|---|---|
| usage 无 cache 字段 | `cached_input_tokens=0`；`input=prompt_tokens` |
| cache > prompt | `input=0`；cache 按解析值（不负） |
| tracing 关 | 不上报、不抛 |

---

## 验收

- [x] mock 带 `prompt_cache_hit_tokens` → Langfuse `usage_details["cached-input-tokens"]` 正确
- [x] `input` = `prompt_tokens − cached`（exclusive-bucket）
- [x] 无 cache 字段时行为与改前一致（仅 input/output 语义）
- [x] pytest / ruff 绿

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-31 | 维护者令开；自 SF catalog CLOSE 后开分支 |
| 2026-08-31 | 30 交付 · PR #101 MERGED · 归档 |

---

## CLOSE

| 项 | 值 |
|---|---|
| PR | [#101](https://github.com/Cyning12/ops-desk-api/pull/101) **MERGED** · 2026-08-31 |
| 交付 | `LlmUsage.from_provider_usage` · Langfuse `cached-input-tokens` exclusive-bucket |
| 归档 | 2026-08-31 → `docs/tasks/done/` |

