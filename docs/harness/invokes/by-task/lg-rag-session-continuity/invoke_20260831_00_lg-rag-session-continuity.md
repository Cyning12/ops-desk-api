# Invoke：00 · lg-rag-session-continuity（T3）

| 字段 | 值 |
|---|---|
| hat_id | 00 |
| task_slug | `lg-rag-session-continuity` |
| task_paths | `docs/tasks/active/task_lg_rag_session_continuity.md` |
| git_branch | `task/lg-rag-session-continuity` |
| created_utc_or_local | 2026-08-31 |
| notes | 维护者 Prompt 授权开工 T3；**00 不实现**；阶段 A 已 CLOSE T2/kit |

---

## GATE_VERIFY（00 扫描 · 非 30 改码）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 维护者 Prompt 代签 | Y | N | 待 20 |
| HG-AUDIT-R1 | pending | 尚未 20 | Y | Y | **否** |
| HG-GRAPH-MODULES | approved | 不新增一级模块 | Y | N | 待 R1 |

reviews：尚无 R1 → 30 不可开工。

pre-30 invoke：本文件（00）+ 下一棒 10。

结论：**派 10 → 20；00 不改 `app/`**。

## 签收栏

00 代签 · 维护者 Prompt 授权 · 2026-08-31
