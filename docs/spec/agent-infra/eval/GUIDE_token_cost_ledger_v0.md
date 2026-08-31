# GUIDE：Token / 费用账本（E5）

> **计费公式**：`cost = usage × Host 价表`（禁止 LLM 估费）。  
> **价表**：[`evals/agent/cost/price_table_v1.yaml`](../../../../evals/agent/cost/price_table_v1.yaml)  
> **导出**：[`evals/agent/cost/export_cost.py`](../../../../evals/agent/cost/export_cost.py)  
> **规划**：[`../04_eval_and_observability_plan_v0.md`](../04_eval_and_observability_plan_v0.md) §2.5 · [`ROADMAP_eval_observability_v0.md`](./ROADMAP_eval_observability_v0.md) E5

---

## 1. Host 价表 vs Langfuse model 单价

| 层 | 职责 | 真值 |
|---|---|---|
| **Langfuse** | generation usage 展示；可在 UI 配 model 单价做 **粗估** | 观测 / Dashboard；**非**商务账单 |
| **Host 价表** | `provider` + `model` + input/output/cache 单价 + 币种 + `effective_from` | git 本仓 `price_table_v1.yaml` |
| **对齐方式** | 键一致：`provider` / `model` 与 `OPS_LLM_PROVIDER`、`OPS_LLM_MODEL`（及 catalog 默认）同名；Langfuse UI 单价应抄 Host 价表同一行，避免双源漂移 | 改价先改 git 价表，再手工同步 Langfuse Model prices（若启用） |

Host 单价字段：`input_per_1m`（必填）；`output_per_1m` / `cached-input-tokens_per_1m` **缺省按 0**（rerank 等无 completion 价、无 cache 价时补 0）。  
导出 usage：`input_tokens` / `output_tokens` 必填；`cached_input_tokens` 可选（缺则 0）。  
`cost = input×input价 + cached×cache价 + output×output价`（每 1M）。

Dashboard「费用列」：优先看 Langfuse 在已配单价后的 generation cost；**对账 / 导出 / 折扣**一律以本 GUIDE 脚本 × Host 价表为准。  
人工：从 Langfuse 导出 usage CSV/JSON → 映射为 fixture 字段 → `python evals/agent/cost/export_cost.py --usage …`。本波 **不** 新增 GHA 拉云 usage。

---

## 2. 状态语义（导出 CSV `status`）

| status | 含义 | `cost_est` | CLI 退出码 |
|---|---|---|---|
| `ok` | 有 tokens 且价表命中 | usage × 单价（价表币种） | 0（全 ok / 仅含 usage_missing） |
| `usage_missing` | 缺 `input_tokens` / `output_tokens`（或非法负值） | **空**（不算假价） | 0 |
| `price_missing` | provider+model 无生效价行 | **空** | **1** |
| （加载失败） | 价表/JSON 结构或生效日非法 | — | **2**（stderr） |

单价单位：每 **1M** tokens（`input_per_1m` / `output_per_1m` / `cached-input-tokens_per_1m`）。  
生效：取 `effective_from ≤ usage.date`（无 date 则用运行日）的最新一行。

---

## 3. Usage 审计清单（`update_current_generation_usage`）

入口：`app/ops/tracing.py` · `update_current_generation_usage` → Langfuse `update_current_generation(usage_details)`。  
上报键：`input`（prompt−cache，exclusive）· `output` · `cached-input-tokens`（SiliconFlow：`prompt_cache_hit_tokens` / `prompt_tokens_details.cached_tokens`）。  
tracing 关 / SDK 失败 → 静默 no-op。

### 3.1 已上报

| 路径 | 机制 | 备注 |
|---|---|---|
| `app/ops/chat/nodes.py` · `answer_llm` | stream 末帧 `chunk.meta["usage"]` → 显式调用 | `run_type=llm` + `model=` |
| `app/llm/providers/base.py` · `_report_complete_usage` | `complete()` 聚合 stream 时副作用上报 | 凡走 `BaseProviderImpl.complete()` 且 tracing 开 |

依赖 `complete()` 上报的典型调用（tracing 开时）：`lc_evidence_chain` 的 `grade_llm` / `answer_llm`；`structured_output.complete`；`lg_rag` / `lg_rag/multi` 内 `provider.complete(...)` 等。

### 3.2 缺帧 / 标 `usage_missing`（本波不强制补码）

| 缺口 | 说明 |
|---|---|
| API 未回 usage 末帧 | Provider `stream_options.include_usage` 失效或兼容层丢帧 → Langfuse 无 usage；导出侧标 `usage_missing` |
| `run_type=chain` 内 `complete()` | 如 supervisor / router / rewrite 等：上报目标是 **current generation**；若无 generation 包裹，SDK 失败静默 → 观测上等同缺帧 |
| embed / rerank | `lc_evidence_chain/retrieve.py` · `query_embed` / `rerank`：`run_type=llm` 但无 `update_current_generation_usage`（无标准 chat usage 字段时可缺） |
| `model` / `provider` metadata 不统一 | 价表键难对齐；可选后续在 generation 路径钉死（本波默认不改 `chat/graph.py`） |

Score 热路径 `cost.*`：**可不写**；账本以导出 CSV 为准（ROADMAP §3.2）。

---

## 4. 快速跑通

    # 默认 fixture → stdout CSV（样例含 price_missing → exit 1）
    python evals/agent/cost/export_cost.py

    # 仅 ok 行可自备 fixture；pytest 不连网
    pytest tests -q --tb=short -k eval_cost

---

## 5. 非范围

- 完整计费中台 / 租户账单 HTTP  
- 新 GHA Langfuse secret job；Langfuse SDK v4  
- LLM 估 `cost_est`  
- 扩 E2 金标；改 RAG `evals/golden`  
- 强制全路径补 usage（缺口仅列本清单）
