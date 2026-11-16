# invoke_10 · draft（p2b-t1-mcp-legacy-config）

## 内容

- task 档落盘：`docs/tasks/active/task_p2b_t1_mcp_legacy_config.md` v1
  （背景/范围 10 条/非范围/失败路径 F1-F5/验收 9 条/必读/思考轮 R0-R5/实现备忘/测试策略）。
- registry N3 entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=bf1c23f2 · allowed_app_files 八件 · allowed_tree_files 十一件 ·
  allowed_tree_prefixes=invokes 目录 · banned_prefixes=[alembic/, scripts/, app/ops/lg_rag/]），
  `yaml.safe_load` 验证通过（waves=19）。
- R1 审查文落盘：`docs/harness/reviews/task_p2b_t1_mcp_legacy_config_audit_R1_20261116.md`（结论 GO）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03216 夜间授权）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（见本 invoke 命令行记录） |
| registry yaml safe_load | PASS（19 waves · 末 entry=p2b-t1-mcp-legacy-config） |

## 偏差

无。

## 结果

10 draft 完成，进 30。
