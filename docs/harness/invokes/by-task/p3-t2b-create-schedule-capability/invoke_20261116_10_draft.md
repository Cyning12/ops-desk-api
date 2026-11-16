# invoke_10 · draft（p3-t2b-create-schedule-capability）

## 内容

- task 档落盘：`docs/tasks/active/task_p3_t2b_create_schedule_capability.md` v1
  （背景/范围 7 条/非范围/失败路径/验收 11 条/必读/思考轮 R0-R5/
  实现备忘含偏差 D1-D4 + 限制 L1-L3/测试策略）。
- registry entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=17337d35 · allowed_app_files 四件 ·
  allowed_tree_files 六件 · allowed_tree_prefixes=invokes 目录 ·
  banned_prefixes=[] ——承 T2 先例），`yaml.safe_load` 验证通过
  （26 waves · 末 entry=p3-t2b-create-schedule-capability）。
- R1 审查文落盘：`docs/harness/reviews/task_p3_t2b_create_schedule_capability_audit_R1_20261116.md`（结论 GO）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03283/m03498 夜间授权）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（见下方摘录） |
| registry yaml safe_load | PASS（26 waves · 末 entry=p3-t2b-create-schedule-capability） |

## 偏差

- D1 adapter 形态：契约 §2.1 嵌套 map → 冒号串白名单
  `local_fn:app.ops.schedule.service:create_schedule_from_capability`
  + _PREFIX_TO_MODULE 第三前缀（loader 约束 · task 档 R3-D1）。
- D2 output_schema：契约 JSON-schema 风 → JSONPath required 词表
  ["$.schedule_id","$.next_fire_at","$.status"]（V10 约束 · task 档 R3-D2）。
- D3 request_id：契约 required 四键逐字不动；args_schema 增 request_id
  可选 property + adapter 回退键 f"{run_id}:{subtask_id}"（task 档 R3-D3）。
- D4 schedule→capability 新边：service.py 函数内延迟 import
  capability.idempotency（T2 自注豁免 · 01_modules 登记）。

## 结果

10 draft 完成，进 30。
