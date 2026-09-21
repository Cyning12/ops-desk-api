# Invoke：30 · supervisor-parallel-join

| 字段 | 值 |
|------|-----|
| **时间** | 2026-09-19 |
| **帽** | 30 |
| **task_slug** | `supervisor-parallel-join` |
| **git_branch** | `task/supervisor-parallel-join` |
| **task** | `docs/tasks/active/task_supervisor_parallel_join.md` |

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved | Y | Y | 是 |
| HG-AUDIT-R1 | approved | approved | Y | Y | 是 |
| HG-GRAPH-MODULES | approved | approved | Y | Y | 是 |

reviews：`task_supervisor_parallel_join_audit_R1_20260919.md` 与 `…_R2_…` 均存在。闸真值以 task 表 `HG-AUDIT-R1=approved` 为准。

pre-30 invoke：`invoke_20260919_00_start.md`、`invoke_20260919_10_task.md` 齐全。

`npx spec-wave verify --target . --task docs/tasks/active/task_supervisor_parallel_join.md` → `VERIFY: PASS`。

结论：可进入改码。

## 实现

- 无依赖子任务：`route_next_subtask` 返回多个 `Send`，载荷带 `assigned_subtask`（`subtask_id` / `type` / `input`，有则 `tool` / `args`）。
- Host 签发 `subtask_id="{run_id}:{seq}"`，`seq` 从 1，Critic 不重置。模型 id 只进 `alias`。
- `subtask_join` 按计划 id 终态收齐；未知 id 与重复终态在 `merge_subtask_results` 丢弃；`None` 仍清空。
- `depends_on` 解析为已签发 id；成环 / 计划外写错误终态，不与前驱同批。
- RAG `thread_id` 等于该 `subtask_id`。`invoke_lg_rag` 与 `iter_lg_rag_sse` 把已有 `run_id` 传入图。
- 图谱：`01_modules.md` lg_rag 备注；`10_flow_lg_rag` dispatch / 回边改为同批 Send + 按 id 归并。未扩 G-L2 indexes。未改闸 status。

## 验证

- `./scripts/graph-compile.sh` exit 0
- `npx spec-wave task lint-wiki-delta --target .` → `LINT-WIKI-DELTA: PASS`
- `.venv/bin/ruff check` 触及的 `app/ops/lg_rag` 与本次 tests：通过
- `.venv/bin/pytest tests -q --tb=line`：695 passed，1 skipped，2 failed（`tests/test_chat_ws.py` 两条，SQLAlchemy `run already active`；文件不引用 lg_rag）
- 主题文件已绿：`tests/test_supervisor_parallel_join.py` 及 task 点名的 multi / critic / catalog / structured / budget / sse stream / sse resume

## 禁区确认

- 未改 `app/ops/capability/**`
- 未改 `docs/tasks/active/task_tenant_readonly_predicate.md`
- 未 commit、未 push、未 `task close`
- 分支保持 `task/supervisor-parallel-join`
