# invoke_10 · draft（p3-t2-schedule-ddl-rest）

## 内容

- task 档落盘：`docs/tasks/active/task_p3_t2_schedule_ddl_rest.md` v1
  （背景/范围 6 条/非范围/失败路径/验收 10 条/必读/思考轮 R0-R5/
  实现备忘含限制 L1-L2/测试策略）。
- registry entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=f1d0dd28 · allowed_app_files 五件 ·
  allowed_tree_files 九件 · allowed_tree_prefixes=invokes 目录 ·
  banned_prefixes=[] ——本波碰 alembic/ 承 p0prime-t4/t5 先例），
  `yaml.safe_load` 验证通过（24 entries · 末 entry=p3-t2-schedule-ddl-rest）。
- R1 审查文落盘：`docs/harness/reviews/task_p3_t2_schedule_ddl_rest_audit_R1_20261116.md`（结论 GO）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03283 夜间授权）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（见下方摘录） |
| registry yaml safe_load | PASS（24 entries · 末 entry=p3-t2-schedule-ddl-rest） |

## 偏差

- uq 索引形态：15 §4.1「部分唯一索引」无 WHERE 语义 → 取普通
  UNIQUE INDEX(schedule_id, planned_fire_at)（ON CONFLICT 直接可用 ·
  task 档 R3 决策记录）。
- resume（paused→active）不重算 next_fire_at（§1.6「任一排期字段变更」
  字面 · task 档 R3/限制 L1）。

## 结果

10 draft 完成，进 30。
