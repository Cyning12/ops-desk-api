# Eval · Observability · 域夹（L1）

> **track**：`agent-infra` / eval  
> **规划轨**：[`../04_eval_and_observability_plan_v0.md`](../04_eval_and_observability_plan_v0.md)  
> **实现落点（建议）**：E2 金标 `evals/agent/golden/` + `tests/eval/`；E3 Dataset/Experiment 见 GUIDE；`app/ops/tracing.py` 沿用（本波默认不改）  
> **控制面**：Langfuse（默认）；LangSmith 非默认

---

## 本夹文件

| 文件 | 说明 |
|---|---|
| [`ROADMAP_eval_observability_v0.md`](./ROADMAP_eval_observability_v0.md) | SLI 字典（E1 真值）· Dataset/Experiment · CI 门禁 · E1–E5 |
| [`GUIDE_langfuse_dataset_experiment_v0.md`](./GUIDE_langfuse_dataset_experiment_v0.md) | E3：git SoT · Dataset 名 · dry-run / `--push` · CI 不连云 |
| [`GUIDE_online_sample_annotation_v0.md`](./GUIDE_online_sample_annotation_v0.md) | E4：`OPS_EVAL_SCORE_SAMPLE_RATE` · `stab.fallback` · Annotation Queue 回流（无 Queue API） |
| [`GUIDE_token_cost_ledger_v0.md`](./GUIDE_token_cost_ledger_v0.md) | E5：usage 审计 · Host 价表 · `export_cost.py` · `price_missing` / `usage_missing` |
| [`SLI_host_v1_four_metrics_v1.md`](./SLI_host_v1_four_metrics_v1.md) | Host v1.0 出口四项 SLI 定义（P99 / 完成率 / 命中率 / Cost） |
| [`sli_host_v1_four_metrics_v1.yaml`](./sli_host_v1_four_metrics_v1.yaml) | 同上 · 机读键名 |
| [`GUIDE_host_v1_sli_dashboard_v1.md`](./GUIDE_host_v1_sli_dashboard_v1.md) | 四项看板：Langfuse 三步打开 + 字段清单 |

上级：[`../04_eval_and_observability_plan_v0.md`](../04_eval_and_observability_plan_v0.md) · [`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md)

---

## 一句话

**Langfuse** 承载 traces/scores/experiments/**annotation**；**仓内 Eval/Cost harness** 承载模块金标、确定性评估器、CI 门禁与价表；不完整自建观测平台，不默认双开 LangSmith，**不默认 Fork 二开 Langfuse**。
