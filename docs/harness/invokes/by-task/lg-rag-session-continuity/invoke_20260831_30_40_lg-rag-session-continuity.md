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

## 人工闸扫描（GATE_VERIFY · 30 重填 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 pass | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 不新增一级模块 · 00 代签 | Y | N | Y |

reviews：`task_lg_rag_session_continuity_audit_R1_20260831.md` 存在且内容 pass？ **是**

pre-30 invoke：00 + 10 已落盘？ **是**

机械：`npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_session_continuity.md` → **VERIFY: PASS**（exit 0）

结论：**可进入读码/改码**

---

## 签收栏

30 重扫通过 · 2026-08-31

---

## 交付摘要

- SoT=`thread_id`；表 `ops_lg_rag_threads` / `ops_lg_rag_turns` + Alembic
- `continuity.assemble_graph_messages` 注入 `_ainvoke/_astream`
- 缺 thread_id → 头 `X-Ops-Lg-Rag-Thread-Id`；跨用户 404；超长 422
- freeze `lg-rag-sse-v1` 未新增 event_type；`chat/graph.py` 零 diff
- **勿 auto-merge** · 可 api-only 先合
