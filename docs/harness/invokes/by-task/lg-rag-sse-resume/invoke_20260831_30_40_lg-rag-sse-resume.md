# Invoke：30（含 40）· lg-rag-sse-resume（T4）

| 字段 | 值 |
|---|---|
| hat_id | 30（含 40） |
| task_slug | `lg-rag-sse-resume` |
| task_paths | `docs/tasks/active/task_lg_rag_sse_resume.md` |
| related_review_or_none | `docs/harness/reviews/task_lg_rag_sse_resume_audit_R1_20260831.md` |
| git_branch | `task/lg-rag-sse-resume` |
| created_utc_or_local | 2026-08-31 |
| notes | 00 代签 HG-AUDIT-R1 后派发；**仅 L-c**；禁止 T3 重做 / T5 / T6 / C0–C4 / cancel / chat 依赖 |

---

## 人工闸扫描（GATE_VERIFY · 30 重填 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 pass | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 不新增一级模块 · 00 代签 | Y | N | Y |

reviews：`task_lg_rag_sse_resume_audit_R1_20260831.md` 存在且内容 pass？ **是**

pre-30 invoke：00 + 10 已落盘？ **是**

机械：`npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_lg_rag_sse_resume.md` → **VERIFY: PASS**（exit 0 · 00 派发前）

结论：**可进入读码/改码**（30 须首输出重扫本表）

---

## 可复制 Prompt 快照

hat_id：30（含 40 自检）  
task_slug：lg-rag-sse-resume  
本帽禁区：不越 L-c；不 import chat/session；不引入 cancel；不改 Vue；不直推 master

首动作：GATE_VERIFY（FRAGMENT_30_gate_verify）→ 通过再改码。

00 定夺摘要：
- 表 `ops_lg_rag_run_events` + Alembic
- live 帧顶层可选 `cursor=run_id:seq`
- `POST /api/ops/lg-rag/replay` · after_seq / cursor · SSE 重放 seq>
- 断连仍「尽量跑完」；未知/跨用户 run_id → 404
- freeze 扩展 lg-rag-sse-v1；回写 05 §4.2/§10.3；G-L1 备注；条件同步 G-L2
- PR 勿 auto-merge；可 api-only 先合

验证：相关 pytest · ruff · graph-compile · 旧测零破坏 · chat/graph.py 零 diff

完成后：回填本 invoke 交付摘要 + task「自检结论（执行者）」；开 PR（勿 merge）；回报 00。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-08-31 · VERIFY PASS

---

## 交付摘要

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS · 可开工（HG-AUDIT-R1/GRAPH/DRAFT approved · verify exit 0） |
| 实现 | `ops_lg_rag_run_events` + Alembic；live 帧顶层 `cursor`；`POST /lg-rag/replay`；断连仍跑完、无 cancel |
| 测试 | `.venv/bin/pytest` resume+stream+session_continuity×2 → **34 passed**；`ruff check` PASS；`./scripts/graph-compile.sh` exit 0；`lint-wiki-delta` PASS |
| chat 依赖 | `app/ops/chat/graph.py` **零 diff**；`app/ops/lg_rag/**` **无** import chat/session |
| PR | https://github.com/Cyning12/ops-desk-api/pull/103 · **勿 auto-merge** |

关键路径：
- `app/ops/lg_rag/sse_replay.py` · `event_store.py` · `sse_stream.py` · `router.py`
- `app/db/models.py` · `alembic/versions/20260831_lg_rag_run_events.py`
- `tests/test_lg_rag_sse_resume.py`
- `docs/spec/.../05_...§4.2/§10.3` · `docs/_tech_graph/l1/01_modules.md` · `10_flow_lg_rag.graph.yaml` · G-L2 indexes
