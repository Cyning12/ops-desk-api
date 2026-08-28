# Invoke：20-task-audit · eval-goldenset-lg-rag

| 字段 | 值 |
|---|---|
| hat_id | 20-task-audit |
| task_slug | eval-goldenset-lg-rag |
| 审查文 | `docs/harness/reviews/task_eval_goldenset_lg_rag_audit_R1_20260828.md` |
| 内容结论 | **pass** |
| 维护者签收 | **approved** · 2026-08-28 · 00 代签（维护者令开始 E2） |

## 范围核对

| 项 | 结论 |
|---|---|
| 仅 E2 | 是 · 明示排除 E3–E5 |
| 与 RAG golden 隔离 | 是 · `evals/agent/` |
| 00 实现 | **禁止**；30 Prompt 另文件 |
| 思考轮 | R0–R4 · early_stop 合理 |

## 下一棒

闸已签 → 新窗 30。本 20 **不**改码。

| 2026-08-28 | 20 R1 pass · 与 10 同日 |
