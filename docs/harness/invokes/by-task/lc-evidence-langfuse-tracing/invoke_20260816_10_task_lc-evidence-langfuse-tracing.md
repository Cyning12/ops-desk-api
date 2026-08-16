# Invoke：10-task · lc-evidence-langfuse-tracing

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | lc-evidence-langfuse-tracing |
| task_path | docs/tasks/active/task_lc_evidence_langfuse_tracing.md |
| git_branch | task/lc-evidence-langfuse-tracing |
| created | 2026-08-16 |
| notes | 仅 task；不改业务码；依赖旁路链合入 |

## 要点

- 复用 `app/ops/tracing.py` + Chat 的 `CallbackHandler` 模式。  
- freeze：`run_name=lc-evidence-chain` · tags 含 `lc-evidence-chain`。  
- 闸：`HG-TASK-DRAFT` / `HG-AUDIT-R1` = pending。  

## 下一棒

维护者签 `HG-TASK-DRAFT` → 20-task-audit → 签 `HG-AUDIT-R1` → 30。
