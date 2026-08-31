# Task：SiliconFlow 默认 Catalog / Grader + Host 价表 cache

> **状态**：completed（2026-08-31 · 本地交付已 commit · PR 待开）  
> **类型**：config / cost harness  
> **分支**：`task/siliconflow-default-catalog-cost`  
> **帽子**：10 / 20 R1 / 30 已交付。  
> **无关**：删 BailianProvider；Langfuse SDK v4；热路径补 cache usage 上报（移交 `langfuse-cached-input-tokens`）；改 chat/graph 拓扑。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `siliconflow-default-catalog-cost` |
| **git_branch** | `task/siliconflow-default-catalog-cost` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | catalog env 解析 + 默认兜底；grader 默认 SF；export cache/缺省 output；不连真 LLM / 真 SiliconFlow |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `n/a` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30` |
| **invoke_retention_profile** | `minimal` |
| **close_pr_policy** | `required` |
| **orchestration** | 默认模型/价表对齐生产 SiliconFlow；与 T3 session 并行、互不夹带 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | — | 2026-08-31 · 维护者确认：方案 B · 保留 bailian 价行 · cache 进 export · 价表只补 0 |
| HG-AUDIT-R1 | approved | 30 | 2026-08-31 · 维护者 Prompt 授权 · 见 `docs/harness/reviews/task_siliconflow_default_catalog_cost_audit_R1_20260831.md` |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 |

---

## 范围

1. **`SILICONFLOW_MODELS` 环境变量**（逗号分隔 model id）+ 代码内默认列表兜底；默认模型 = 列表首项（默认 Flash）。
2. Grader / lg_rag router 回退默认：`siliconflow` + `Qwen/Qwen3.6-27B`；`.env.example` 对齐。
3. Host 价表：保留维护者核对的数值与 bailian 行；**仅**对未写字段补 `0`。
4. `export_cost.py`：认 `cached-input-tokens_per_1m`；`output_per_1m` 缺省 0；usage 可选 `cached_input_tokens`。
5. 相关单测与 GUIDE 一句对齐。

### failure_paths

| 路径 | 预期 |
|---|---|
| `SILICONFLOW_MODELS` 空/非法 | 回退代码默认列表 |
| 价表缺 `output_per_1m` / cache 键 | 按 0 计，不炸加载 |
| usage 无 cache 字段 | cache 用量按 0 |
| 仍显式 `OPS_LLM_PROVIDER=bailian` | BailianProvider 可用（不删） |

---

## 验收

- [x] `get_models_for_provider("siliconflow")` 可读 env 列表；未设时含 Flash / Pro / Qwen3.6-27B
- [x] `get_default_model("siliconflow")` → `deepseek-ai/DeepSeek-V4-Flash`（默认列表首项）
- [x] grader 默认 provider/model 为 SF + Qwen3.6-27B
- [x] `load_price_table` 成功加载含 rerank（无 output）与 cache 价行
- [x] `compute_cost_rows` 计入 `cached_input_tokens × cached-input-tokens_per_1m`
- [x] `pytest` 相关绿；`ruff check` 触及文件绿

---

## CLOSE

| 项 | 值 |
|---|---|
| 分支 | `task/siliconflow-default-catalog-cost` |
| 交付 | catalog env B · grader 默认 SF · Host 价表 cache 字段 · export_cost |
| 归档 | 2026-08-31 → `docs/tasks/done/`（维护者令：commit 即归档；PR 另开） |
| 下一棒 | `langfuse-cached-input-tokens`（热路径上报 `cached-input-tokens`） |

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-31 | 维护者确认方案；开分支落地 |
| 2026-08-31 | 30 交付 · 归档 · 热路径 cache 上报另开 task |
