# invoke_10 · draft（fix-434-worker-thread-upsert）

## 内容

- task 档落盘：`docs/tasks/active/task_fix_434_worker_thread_upsert.md` v1
  （背景/范围 4 条/非范围/失败路径 6 条/验收 7 条/必读/思考轮 R0-R5/
  实现备忘含偏差 D1/测试策略）。
- registry entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=396f7fed · allowed_app_files 一件
  （app/ops/schedule/worker.py）· allowed_tree_files 六件 ·
  allowed_tree_prefixes=invokes 目录 · banned_prefixes=[alembic/, scripts/]
  ——零新迁移），`yaml.safe_load` 验证通过（31 entries · 末=本 entry）。
- R1 审查文落盘：`docs/harness/reviews/task_fix_434_worker_thread_upsert_audit_R1_20261117.md`（结论 GO）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03694 夜间授权）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（W3 自检结论占位符 draft 期合法） |
| registry yaml safe_load | PASS（末 entry=fix-434-worker-thread-upsert） |

## 勘察记录（30 前置）

- `app/ops/schedule/worker.py:229-240`：`_execute_fire` R6 复核处——`thread = await db.get(OpsLgRagThread, schedule.thread_id)`，None 时直落 create_run，**未建行**（缺口实锤）。
- 404 链：`runs_router.py:68-74 _load_runs_page` → `thread_store.thread_owner`（:63-79）返回 None → 404「Thread not found」（承 history_router FP-1 不泄露存在性）。
- persist 兜底不齐窗口：`sse_stream.py:504-506` 仅正常 done 且 user_id 非空调 `persist_thread_turns`（其内部 :93-95 会建行）；waiting_approval/error/disconnected 不走 persist → thread 行可能始终不存在。
- 建行先例：`thread_store.py:35` / `:95` 均为 `db.add(OpsLgRagThread(id=thread_id, user_id=user_id))` 最小字段形态。
- 模型实际：`app/db/models.py:226-238` OpsLgRagThread 仅 id/user_id/created_at/updated_at（无 tenant_id 列）→ 偏差 D1。
- 契约真源：15-p3-contracts.md §1「thread_id 无 FK（fire 时不存在则 worker 自建）」· models.py:704-705 同述。

## 偏差

- D1：最小字段按模型裁剪（无 tenant_id 列 · 实落 id+user_id）。

## 结果

10 draft 完成，进 30。
