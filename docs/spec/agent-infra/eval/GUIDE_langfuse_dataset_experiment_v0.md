# GUIDE：Langfuse Dataset / Experiment（E3）

> **SoT**：git `evals/agent/golden/<module>/cases_v1.yaml`。云端 Dataset 是副本，禁止当主源。  
> **Score 名**（ROADMAP §3.2，不得改名）：`acc.route_match` · `acc.strategy.allowlist_match` · `acc.plan_match`（0/1）。  
> **Runner**：`evals/agent/run_experiment.py`（复用 `tests/eval/eval_agent_graders.py`）。e2e **不**建 Dataset。

## Dataset 名

| module | git | Langfuse Dataset |
|---|---|---|
| `router` | `evals/agent/golden/router/cases_v1.yaml` | `golden-router-v1` |
| `strategy_builder` | `evals/agent/golden/strategy_builder/cases_v1.yaml` | `golden-strategy_builder-v1` |
| `supervisor` | `evals/agent/golden/supervisor/cases_v1.yaml` | `golden-supervisor-v1` |

方向：**git → 云**。改金标先改 yaml + pytest；`--push` 再同步副本。

## dry-run vs `--push`

默认 **dry-run**：读 git、跑评估器、stdout JSON，**不联网**。无 `LANGFUSE_*` key 仍绿。

`--push`：须已有 `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY`；否则 **非 0** 且不打网。有 key 时才写 Dataset item / score。

失败语义：缺 `expect` 或 grader ≠ 金标 → 进程非 0。dry-run 下 Langfuse HTTP 失败不得导致失败。

    python evals/agent/run_experiment.py --module router
    python evals/agent/run_experiment.py --push

## CI

门禁 = 现有 `pytest tests`（`-k eval_experiment` 为 mock / dry-run）。**不**新增 GHA workflow，**不**给 `pytest.yml` 加 Langfuse secret。CI 不连云。
