# Eval · Observability · 域夹（L1）

> **track**：`agent-infra` / eval  
> **规划轨**：[`../04_eval_and_observability_plan_v0.md`](../04_eval_and_observability_plan_v0.md)  
> **实现落点（建议）**：`app/ops/tracing.py`（沿用）· `app/ops/eval/` 或 `tests/eval/`（00 定夺）  
> **控制面**：Langfuse（默认）；LangSmith 非默认

---

## 本夹文件

| 文件 | 说明 |
|---|---|
| [`ROADMAP_eval_observability_v0.md`](./ROADMAP_eval_observability_v0.md) | SLI 字典（E1 真值）· Dataset/Experiment · CI 门禁 · E1–E5 |

上级：[`../04_eval_and_observability_plan_v0.md`](../04_eval_and_observability_plan_v0.md) · [`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md)

---

## 一句话

**Langfuse** 承载 traces/scores/experiments/**annotation**；**仓内 Eval/Cost harness** 承载模块金标、确定性评估器、CI 门禁与价表；不完整自建观测平台，不默认双开 LangSmith，**不默认 Fork 二开 Langfuse**。
