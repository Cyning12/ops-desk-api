# Invoke：30（含 40）· lg-rag-session-continuity（T3）

| 字段 | 值 |
|---|---|
| hat_id | 30（含 40） |
| task_slug | `lg-rag-session-continuity` |
| task_paths | `docs/tasks/active/task_lg_rag_session_continuity.md` |
| related_review_or_none | `docs/harness/reviews/task_lg_rag_session_continuity_audit_R1_20260831.md` |
| git_branch | `task/lg-rag-session-continuity` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 代签 HG-AUDIT-R1 后派发；**禁止** T4 replay / 改 chat 拓扑 |

---

## 人工闸扫描（GATE_VERIFY · 首输出须由 30 重填）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 不新增一级模块 | Y | N | Y |

reviews：`task_lg_rag_session_continuity_audit_R1_20260831.md` 存在且内容 pass？ **是**

pre-30 invoke：00 + 10 已落盘。

机械：`npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_session_continuity.md`

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-08-31
