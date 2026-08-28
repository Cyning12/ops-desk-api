# Task：Eval E3 · Langfuse Dataset / Experiment（mock 可 CI）

> **状态**：in_progress（2026-08-28 · 00 起草 · 维护者令开 E3）  
> **类型**：测评 / 控制面接入  
> **上游**：`docs/spec/agent-infra/04_eval_and_observability_plan_v0.md` · `eval/ROADMAP` §4.1  
> **前置**：E2 [#93](https://github.com/Cyning12/ops-desk-api/pull/93) MERGED · 金标在 `evals/agent/golden/`  
> **分支**：`task/eval-langfuse-experiment-ci`  
> **帽子**：**00 不实现**；30 写 GUIDE + runner + mock 测。  
> **无关**：E4 热路径 score、E5 价表、扩金标条数、Langfuse SDK v4、DEF-003/004、`chat/graph.py`。

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `eval-langfuse-experiment-ci` |
| **git_branch** | `task/eval-langfuse-experiment-ci` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | mock Langfuse SDK；dry-run 实验 runner；CI 不注入 Langfuse secret |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 脚本/文档/测试；默认不改图谱与 `app/` |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 不改 coding_wiki 正文 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,00,30` |
| **invoke_retention_profile** | `default` |
| **freeze_id** | 无 |
| **orchestration** | 仅 E3；E4/E5 不进 active；00 不实现 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 22-R1 | 2026-08-28 · **00 代签 · 维护者令「开 E3」** |
| HG-AUDIT-R1 | approved | 30 | 2026-08-28 · **00 代签** · 见 `docs/harness/reviews/task_eval_langfuse_experiment_ci_audit_R1_20260828.md` |
| HG-GRAPH-MODULES | approved | — | 不改图谱 · **00 代签** |

---

## 背景与目标

E2 金标只在 git。E3 把「git → Langfuse Dataset 名」钉死，并提供 **可 mock 的 Experiment runner**（跑既有评估器 → score 名对齐 E1 字典）。CI 只证明 dry-run/mock，不打真云。

---

## 范围 / 非范围

### 00 定夺

| 项 | 定夺 |
|---|---|
| SoT | **git** `evals/agent/golden/<module>/cases_v1.yaml`；云端 Dataset 是副本 |
| Dataset 名 | `golden-<module>-v1`（module=`router`/`strategy_builder`/`supervisor`；e2e 可不建 Dataset） |
| Score 名 | 只用字典已有：`acc.route_match` · `acc.strategy.allowlist_match` · `acc.plan_match`（0/1） |
| Runner | `evals/agent/run_experiment.py`（或 `scripts/` 等价）：默认 **dry-run**（stdout JSON）；`--push` 仅当环境已有 Langfuse key |
| CI | **不**新增带 secret 的 workflow；**不**改 `pytest.yml` 除非 30 证明现有 job 吃不到新测。门禁 = 现有 `pytest tests` 收集 mock 测 |
| 失败语义 | grader 不等 → 进程非 0；Langfuse HTTP 失败 **不得**在无 `--push` 时失败 |
| `tracing.py` / `score_current_trace` | **本波不做**（E4） |
| 金标条数 | **不扩** |

**范围（E3-a/b/c）**：

- GUIDE 一页：同步方向、Dataset 命名、何时 `--push`、CI 不连云  
- Experiment runner + 复用 `tests/eval/eval_agent_graders.py`  
- pytest：mock client；dry-run 阈值对比（如全 1 通过 / 故意错 1 条失败）  

**非范围**：

- E4 线上抽样、Annotation Queue、热路径打分  
- E5 价表  
- 新 GHA job 调 Langfuse API  
- 改 `app/`（默认）；改 RAG `evals/golden/`  

---

## 验收标准

- [ ] GUIDE 落盘（eval 域夹或 `docs/guides/`，README 有链）
- [ ] runner dry-run：对至少 `router` 金标算出 `acc.route_match`，无网络
- [ ] `--push` 路径有 mock 单测；无 key 时 dry-run 仍绿
- [ ] pytest 绿：`pytest tests -q --tb=short -k eval_experiment`（或 30 写明等价 `-k`）
- [ ] 未新增依赖真 Langfuse secret 的 workflow
- [ ] `app/` 与 `chat/graph.py` 零 diff（默认）
- [ ] `npx --yes dsh-coding-kit task lint-wiki-delta --target .` 通过

---

## failure_paths

| 触发 | 行为 | 可重试 | 用户可见 |
|---|---|---|---|
| git fixture 缺 expect | dry-run **非 0** | 是 | stderr |
| grader 与 expect 不等 | 非 0；CI 红 | 是 | pytest |
| 无 Langfuse key 却 `--push` | 明确错误退出；不默认打网 | 是 | stderr |
| CI 无 secret | dry-run/mock 仍绿 | — | Actions |

---

## 给执行帽必读

1. `eval/ROADMAP` §3 score 名 + §4.1  
2. `evals/agent/golden/` · `tests/eval/eval_agent_graders.py`  
3. `docs/standards/CODING_BACKEND_L2_v1_zh.md`  
4. 本 task · `PROMPT_30_execute.md`

---

## test_strategy

```text
required · mock Langfuse
pytest tests -q --tb=short -k eval_experiment
不连真 Langfuse / 真 LLM
ruff 触及路径
无新 GHA secret job
```

---

## 思考轮控制

| 字段 | 值 |
|---|---|
| **actual_last_round** | R4 |
| **early_stop** | yes |
| **early_stop_reason** | CI 不连云、score 名与 SoT 已钉 |
| **residual_risks** | 30 可能加带 secret 的 workflow；验收已禁 |

### R0
E3 是控制面副本与 runner，不是新金标。

### R1
git 为 SoT；Dataset 名 `golden-<module>-v1`。

### R2
默认 dry-run；`--push` 可选且须 mock 覆盖。

### R3
CI = 现有 pytest；不加 Langfuse secret job。

### R4
不写 `score_current_trace`；不扩 fixture。

### R5
（提前停 · 未开）

---

### 自检结论（执行者）

（30 回填）

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | 00 起草 E3；维护者令开 E3；闸代签；00 不实现 |
