# GUIDE：线上抽样 score + Annotation 回流（E4）

> **热路径**：规则分 only（如 `stab.fallback`）；**禁止** LLM-as-judge / `acc.answer_judge`。  
> **Score 名**：ROADMAP §3.2，不得改名。  
> **本页不调** Langfuse Annotation Queue API；队列在 UI 配置与筛选。

## 抽样策略

| 项 | 约定 |
|---|---|
| 开关 | `OPS_EVAL_SCORE_SAMPLE_RATE` ∈ `[0.0, 1.0]`；**默认 `0`**（CI/本地不打网） |
| 非法值 | 按 `0` 关闭并打 warning |
| 封装 | `app/ops/tracing.py` · `score_current_trace(name, value, …)` |
| 失败语义 | tracing 关 / 采样 miss / SDK 异常 → **静默 no-op**，不挡请求 |
| 本波调用点 | `supervisor_fallback=True` → `stab.fallback=1`（`lg_rag/multi/nodes.py`） |

生产建议：先小比例（如 `0.01`–`0.05`）观察 Dashboard fallback 率，再调高。  
未开 `OPS_CHAT_TRACER=langfuse` + key 时，采样率无效（整条 score 路径 no-op）。

## Annotation Queue 回流（人审 → git Dataset）

目标：难例 / 误判进金标，**git 仍为 SoT**（与 E3 GUIDE 一致）。

1. **筛 trace**：Langfuse UI 按 `module`（如 `supervisor`）或 metadata（`supervisor_fallback=true`）过滤。  
2. **入队**：在 Annotation Queue 中新建/选用队列（可按 module 分队列）；UI 里把抽样 trace 加入队列。  
3. **人审**：标注期望 route / plan / allowlist / 备注；**不**在业务仓调 Queue SDK。  
4. **回流 git**：维护者把确认用例写入 `evals/agent/golden/<module>/cases_v1.yaml`，跑 pytest / E3 dry-run。  
5. **云副本**：需要时 `run_experiment.py --push` 同步 Dataset（见 [`GUIDE_langfuse_dataset_experiment_v0.md`](./GUIDE_langfuse_dataset_experiment_v0.md)）。

难例来源示例：`stab.fallback=1` 的抽样、用户投诉会话、Experiment 失败 case。

## 非范围

- E5 价表 / usage 账本  
- 热路径 judge  
- 新增 GHA Langfuse secret workflow  
- Queue CRUD API
