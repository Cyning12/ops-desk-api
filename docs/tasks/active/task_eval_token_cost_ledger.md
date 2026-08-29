# Task：Eval E5 · Token / 费用账本（价表 + 导出）

> **状态**：in_progress（2026-08-29 · 00 起草 · 维护者令开 E5）  
> **类型**：测评 / Cost harness  
> **上游**：`docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` §2.5 · `eval/ROADMAP` E5-a/b/c  
> **前置**：E4 [#95](https://github.com/Cyning12/ops-desk-api/pull/95) MERGED  
> **分支**：`task/eval-token-cost-ledger`  
> **帽子**：**00 不实现**；30 写 usage 审计清单 + 价表 + 聚合脚本 + GUIDE。  
> **无关**：热路径 LLM 估费；E4 抽样大改；扩金标；Langfuse SDK v4；DEF-003/004；`chat/graph.py`；完整计费中台 / 租户账单。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `eval-token-cost-ledger` |
| **git_branch** | `task/eval-token-cost-ledger` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 价表加载 + usage×单价聚合单测；fixture CSV；不连真 Langfuse / 真 LLM |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | Cost 薄层在 evals/agent/cost 或 scripts；默认不改图谱 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 仅 E5；Eval 轨收官本波；00 不实现 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-29 · **00 代签 · 维护者令「开 E5」** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-29 · **00 代签** · 见 `docs/harness/reviews/task_eval_token_cost_ledger_audit_R1_20260829.md` |
| HG-GRAPH-MODULES | approved | — | 不新增一级模块 · **00 代签** |

---

## 背景与目标

Langfuse 可展示 token；商务价与聚合须在 Host。E5 落：**usage 路径审计**、**价表（模型×单价×生效日）**、**可跑导出**、**与 Langfuse 单价配置对齐的 GUIDE**。费用 = usage × 价表，禁止 LLM 估价。

---

## 范围 / 非范围

### 00 定夺

| 项 | 定夺 |
|---|---|
| 价表路径 | `evals/agent/cost/price_table_v1.yaml`（或等价）；键 = `provider` + `model`；字段含 input/output 单价、币种、`effective_from` |
| 聚合脚本 | `evals/agent/cost/export_cost.py`（或 `scripts/`）：读 usage 记录（fixture JSON/CSV）→ 算 `cost.usd_est`（或价表币种）→ stdout/CSV |
| E5-a | **清单文档**：哪些路径已 `update_current_generation_usage`、哪些缺帧标 `usage_missing`；本波 **不强制** 全路径补码（缺口列进 GUIDE；可选 1 处最小 metadata 钉死若触达成本低） |
| E5-c | GUIDE：Host 价表 vs Langfuse model 单价如何对齐；Dashboard 费用列说明 |
| Score | 可不写热路径 `cost.*` score；账本以导出为准 |
| 热路径 | 禁止用 LLM 估费；默认不改 `chat/graph.py` |

**范围（E5-a/b/c）**：

- usage 审计清单（文档）  
- 价表 + 聚合导出脚本 + pytest  
- GUIDE 一页并链到 `eval/README.md`  

**非范围**：

- 自建完整计费中台 / 租户账单 API  
- 新 GHA 拉 Langfuse 云 usage（可文档写「人工导出后再跑脚本」）  
- SDK v4；改 RAG golden；扩 E2 fixture  

---

## 验收标准

- [x] usage 审计清单落盘（GUIDE 或同夹 AUDIT 节）
- [x] `price_table_v1.yaml`（或等价）含 ≥1 个已知模型价行 + 生效日
- [x] 导出脚本：fixture usage → CSV/stdout；缺价表键 → 明确错误或 `price_missing` 行（语义钉死在 GUIDE）
- [x] pytest：`-k eval_cost`（或等价）绿；不连外网
- [x] GUIDE 链到 `eval/README.md`
- [x] `chat/graph.py` 零 diff；无新 GHA Langfuse secret job
- [x] 回归：`-k 'eval_agent or eval_experiment or eval_sample'` 不红
- [x] `npx --yes dsh-coding-kit task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| 价表缺 model/provider | 该行 `price_missing` 或非 0（30 选一并写 GUIDE） | 是 | stderr/CSV |
| usage 缺 tokens | 标 `usage_missing`；不算假价 | 是 | CSV |
| 非法生效日 / 单价 | 加载失败非 0 | 是 | stderr |
| LLM 估费 | **禁止** | — | 评审拒收 |

---

## 给执行帽必读

1. `04` §2.5 · `eval/ROADMAP` E5 / §3.2 `cost.*`  
2. `app/ops/tracing.py` · `update_current_generation_usage`；`app/config.py` LLM model 字段  
3. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
4. 本 task · `PROMPT_30_execute.md`

---

## test_strategy

```text
required · offline
pytest tests -q --tb=short -k eval_cost
回归：-k 'eval_agent or eval_experiment or eval_sample'
不连真 Langfuse / 真 LLM
ruff 触及路径
chat/graph.py git diff 空
```

---

## 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R4 |
| **early_stop** | yes |
| **early_stop_reason** | 价表+脚本+审计清单足够闭环；全路径补码 defer |
| **residual_risks** | 30 可能大改所有 LLM 节点；验收限清单为主 |

### R0
计费 = usage 遥测 + Host 价表，非 Langfuse 替代商务价。

### R1
价表进 git；键对齐 provider/model。

### R2
导出用 fixture；不强制本波拉云 API。

### R3
缺帧只审计/标记，不全仓补码。

### R4
禁止 LLM 估费；不改 chat/graph。

### R5
（提前停 · 未开）

---

### 自检结论（执行者）

30 PASS · 2026-08-29：GUIDE 审计清单 + `price_table_v1.yaml` + `export_cost.py` + fixture；pytest `-k eval_cost` 8 passed；回归 eval_agent/eval_experiment/eval_sample 32 passed；未改 `app/` / `chat/graph.py`；无 LLM 估费、无新 GHA secret。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-29 | 00 起草 E5；维护者令开 E5；闸代签；00 不实现 |
