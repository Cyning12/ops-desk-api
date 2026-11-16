# invoke_10 · draft（p3-t3-schedule-worker）

## 内容

- task 档落盘：`docs/tasks/active/task_p3_t3_schedule_worker.md` v1
  （背景/范围 7 条/非范围/失败路径/验收 15 条/必读/思考轮 R0-R5/
  实现备忘含偏差 D1-D5 与限制 L1-L2/测试策略）。
- registry entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=17337d35 · allowed_app_files 三件
  （worker.py/main.py/models.py）· allowed_tree_files 八件 ·
  allowed_tree_prefixes=invokes 目录 · banned_prefixes=[] ——本波碰
  alembic/ 承 T2 先例），`yaml.safe_load` 验证通过。
- R1 审查文落盘：`docs/harness/reviews/task_p3_t3_schedule_worker_audit_R1_20261116.md`（结论 GO）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03283 夜间授权）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（见 invoke_30 摘录） |
| registry yaml safe_load | PASS（末 entry=p3-t3-schedule-worker） |

## 偏差

- D1：抢占单语句 UPDATE 拆为锁定 SELECT+同事务逐行推进（task R3）。
- D2：CLAIM_STALE_SECONDS=120（设计未钉值）。
- D3：max_fires 达限插 skipped+推进。
- D4：once_at 不推进 next_fire_at。
- D5：fires 加 created_at 列（新迁移 · R10 判据载体）。

## 结果

10 draft 完成，进 30。
