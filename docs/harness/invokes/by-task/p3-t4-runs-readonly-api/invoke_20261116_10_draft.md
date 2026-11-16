# invoke_10 · draft（p3-t4-runs-readonly-api）

## 内容

- task 档落盘：`docs/tasks/active/task_p3_t4_runs_readonly_api.md` v1
  （背景/范围 6 条/非范围/失败路径 8 条/验收 10 条/必读/思考轮 R0-R5/
  限制登记 R-P3-T4-1/测试策略）。
- R1 审查文落盘：`docs/harness/reviews/task_p3_t4_runs_readonly_api_audit_R1_20261116.md`（结论 GO · 零阻塞项）。
- registry N3 entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=f1d0dd28 · allowed_app_files 四件 run_store/event_store/
  runs_router/app/ops/router · allowed_tree_files 六件 ·
  allowed_tree_prefixes=invokes 目录 · banned_prefixes=[alembic/, scripts/]），
  `yaml.safe_load` 验证通过（末 entry=p3-t4-runs-readonly-api）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03283 夜间授权）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（W3 自检结论占位 draft 期合法 · W6 思考轮控制表过渡 warn-only） |
| registry yaml safe_load | PASS（末 entry=p3-t4-runs-readonly-api） |

## 偏差

- 无。契约真源 15-p3-contracts.md v1 终稿（commit 62af6ea）§3/§4 与委派书
  m00002 逐条对账一致；五项裁定（白名单 SQL 层/thread 归属 SoT/归因容错反查/
  query 截断风格/零 import-linter 改动）已落 task 档 R3 与审查文第 3-6 项。

## 结果

10 draft 完成，进 30。
