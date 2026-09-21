# Invoke：40 · supervisor-parallel-join

| 字段 | 值 |
|------|-----|
| **时间** | 2026-09-19 |
| **帽** | 40 |
| **task_slug** | `supervisor-parallel-join` |
| **git_branch** | `task/supervisor-parallel-join` |
| **task** | `docs/tasks/active/task_supervisor_parallel_join.md` |

独立自检。未改 `app/`。未改 00/10/30 invoke。未改 reviews。未改人工闸 status。未 commit / 未 push。

## 命令（仓根真跑）

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `.venv/bin/pytest` 点名 8 个测试文件 `-q --tb=line` | **0** | 84 passed |
| `npx --yes spec-wave@3.0.0 task lint-wiki-delta --target .` | **0** | LINT-WIKI-DELTA: PASS |
| `./scripts/graph-compile.sh` | **0** | check OK |
| `.venv/bin/ruff check` 触及 `app/ops/lg_rag` 与本次 tests | **0** | All checks passed |

## 验收

主题 1–11、13–16：**pass**。全量 pytest：**不勾 pass**。

`tests/test_chat_ws.py` 与 `app/ops/chat/**` 不在本次 diff；源码无 `lg_rag` / `subtask_id`。记为「仓内既有失败，非本 task 验收」。

非范围：`MAX_SUBTASKS` 仍为 4；`make_cursor` 未写入 `subtask_id`；`app/ops/capability/**` 与 `docs/tasks/active/task_tenant_readonly_predicate.md` diff 0 字节。

## 结论

**不打回 30**。交 00 / 50。未 CLOSE。
