# invoke_10 · draft（p2b-t3-mcp-translator）

## 内容

- task 档落盘：`docs/tasks/active/task_p2b_t3_mcp_translator.md` v1
  （背景/范围 10 条/非范围/失败路径/验收 13 条/必读/思考轮 R0-R5/实现备忘含偏差 D1-D4+限制 L1/测试策略）。
- registry N3 entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=b3bc3d6f · allowed_app_files 七件 · allowed_tree_files 八件 ·
  allowed_tree_prefixes=invokes 目录 · banned_prefixes=[alembic/, scripts/, app/ops/skill_registry/]），
  `yaml.safe_load` 验证通过（末 entry=p2b-t3-mcp-translator）。
- R1 审查文落盘：`docs/harness/reviews/task_p2b_t3_mcp_translator_audit_R1_20261116.md`（结论 GO）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03216 夜间授权）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（见本目录 lint 输出摘录） |
| registry yaml safe_load | PASS（末 entry=p2b-t3-mcp-translator） |

## 偏差

- D1-D4 + L1 已在 task 档「实现备忘」落笔：委派书节号 §4-A/B/D/F · §5-⑦ · §9.2
  在终稿不存在（以委派书内联细节为准）；命名双下划线从委派；outputSchema 只取
  output_fields；destructiveHint 两稿并集；strategy 候选集不碰（真实流需运维
  allowlist）。

## 结果

10 draft 完成，进 30。
