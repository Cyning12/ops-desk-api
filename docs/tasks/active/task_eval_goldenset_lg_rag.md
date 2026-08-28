# Task：Eval E2 · lg_rag 模块金标最小集

> **状态**：in_progress（2026-08-28 · 00 起草 · 维护者令开始 E2）  
> **类型**：测评 / 金标 harness  
> **上游**：`docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` · `eval/ROADMAP_eval_observability_v0.md`（E0+E1 **DONE** · PR #92）  
> **分支**：`task/eval-goldenset-lg-rag`  
> **帽子**：**00 不实现**；30 写金标与确定性评估器。  
> **无关**：勿拉 DEF-003/004 RAG；勿开 Langfuse SDK v4（DEF-001）；禁止改 `chat/graph.py`；禁止 E3 Dataset/CI、E4 线上 score、E5 价表；禁止把 RAG `evals/golden/queries_v1.yaml` 当本波金标。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `eval-goldenset-lg-rag` |
| **git_branch** | `task/eval-goldenset-lg-rag` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock LLM；`evals/agent/golden/` + pytest 确定性评估器；不连真 LLM / 真库 / Langfuse Dataset |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 本波默认不改 `app/` 与图谱；金标/评估器落 `evals/agent/` + `tests/eval/` |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 仅 E2；E3–E5 另开 task；00 不实现 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-28 · **00 代签 · 维护者令「继续开始E2」** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-28 · **00 代签** · 见 `docs/harness/reviews/task_eval_goldenset_lg_rag_audit_R1_20260828.md` |
| HG-GRAPH-MODULES | approved | — | 不改图谱 · **00 代签** |

---

## 背景与目标

E0/E1 已签字典。E2 把「改哪测哪」落成 **可本地 pytest 的最小金标**：router / strategy_builder / supervisor plan + **1** 条 E2E。评估器只做确定性比对（枚举、集合、schema），不打分上云。

---

## 范围 / 非范围

### 00 定夺（颗粒度）

| 项 | 定夺 |
|---|---|
| 金标根 | `evals/agent/golden/<module>/`（**隔离** RAG `evals/golden/`） |
| router | ≥3 条：`query` + `expect.route`（枚举对照现 router 出口，30 读 `lg_rag/nodes.py`） |
| strategy_builder | ≥2 条：`expect.allowed_capability_ids` **集合相等** |
| supervisor | ≥2 条：plan 结构（如 `subtask_types` / `supervisor_fallback`） |
| e2e | **恰好 1** 条：mock 全链到 END |
| 评估器 | 纯函数：枚举相等、tool id ∈ allowlist、plan JSON schema |
| `module=` 热路径 | **本波非阻塞、默认不做**（避免扩成 tracing 单）；可另 task |
| 既有标注集 | 可 **抽样引用** `evals/router/labeled_router_v1.yaml` 的 query；**禁止改其语义/当本波验收全集** |

**范围（E2-a / E2-b）**：

- 目录 + YAML（或等价 fixture）如上四切片  
- `tests/eval/`（或 `tests/test_eval_agent_*.py`）跑评估器；CI 已有 `pytest tests` 能吃到  
- mock LLM / 直接调节点函数喂 fixture；不连外网  

**非范围**：

- E3：Langfuse Dataset 同步、Experiment runner、新 CI workflow  
- E4：热路径 `score_current_trace`、线上抽样、Annotation Queue  
- E5：usage/价表  
- 改 `chat/graph.py`；改 RAG `evals/golden/run_eval.py` / `queries_v1.yaml`  
- LLM-as-judge；真 LLM 准确率脚本作为本波必绿项  

---

## 验收标准

- [ ] `evals/agent/golden/router/` · `strategy_builder/` · `supervisor/` · `e2e/` 均有最小 fixture（条数见上表）
- [ ] 确定性评估器：route 枚举相等；allowlist 集合相等；非法 tool id 判定失败；plan 过 schema
- [ ] `pytest tests -q --tb=short -k eval_agent`（或 `pytest tests/eval -q --tb=short`）绿；**不**打真 LLM
- [ ] `evals/golden/queries_v1.yaml` 与 `evals/golden/run_eval.py` **零业务 diff**
- [ ] `app/ops/chat/graph.py` 零 diff；默认 `app/` 零 diff（若 30 必须动节点，须先停并问 00）
- [ ] `npx --yes dsh-coding-kit task lint-wiki-delta --target .` 通过
- [ ] 未新增 GitHub Actions workflow（E3）

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| fixture 缺 `expect` 键 | pytest **fail**（禁止 silent skip） | 是 | 测报 |
| actual route / allowlist 与 expect 不等 | fail | 是 | 测报 |
| tool id ∉ allowlist | 评估器判 0/fail | 是 | 测报 |
| 未 mock 却调 LLM | 禁止；测试须失败或不可达 | 是 | 测报 |
| 误跑 RAG `run_eval.py` 当 E2 验收 | 非本波；00 拒收 | 否 | 评审 |

---

## 给执行帽必读

1. `docs/spec/agent-infra/eval/ROADMAP_eval_observability_v0.md` §3 字典 + §4 颗粒度  
2. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
3. `tests/test_strategy_builder.py` · `tests/test_lg_rag_supervisor_capability_catalog.py`（复用 mock 手法，勿复制 RAG golden runner）  
4. 本 task · `PROMPT_30_execute.md`

---

## test_strategy

```text
required · mock only
pytest tests -q --tb=short -k eval_agent
（或 pytest tests/eval -q --tb=short）
不连真 LLM / 真库 / Langfuse
ruff check 触及路径
chat/graph.py git diff 空
```

---

## 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R4 |
| **early_stop** | yes |
| **early_stop_reason** | 目录隔离与评估器类型已钉死；E3–E5 明确排除 |
| **residual_risks** | 30 可能把 RAG golden runner 复用进来；验收已禁 |

### R0
E2 是 Agent 模块金标，不是检索 `queries_v1`。

### R1
根目录 `evals/agent/golden/<module>/`，与 `evals/golden/` 隔离。

### R2
评估器只做确定性比对；score 名可在注释对齐字典，本波不写 Langfuse。

### R3
四切片最小条数钉死；e2e 恰好 1 条，避免做成全链回归套件。

### R4
`module=` 与 Dataset/CI 不进本单。

### R5
（提前停 · 未开）

---

### 自检结论（执行者）

30 E2 完成：四切片金标 + 确定性评估器；`pytest tests -q --tb=short -k eval_agent` → 17 passed / exit 0；`app/` 零 diff；`module=` 未做。

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 00 起草 E2；维护者令开始；闸代签；00 不实现 |
