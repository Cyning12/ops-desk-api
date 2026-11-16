# invoke_10 · draft（p2b-t2-mcp-transport-session）

## 内容

- task 档落盘：`docs/tasks/active/task_p2b_t2_mcp_transport_session.md` v1
  （背景/范围 9 条/非范围/失败路径/验收 12 条/必读/思考轮 R0-R5/实现备忘含偏差 D1-D5/测试策略）。
- registry N3 entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=575ab69b · allowed_app_files 七件 · allowed_tree_files 十一件 ·
  allowed_tree_prefixes=invokes 目录 · banned_prefixes=[alembic/, scripts/, app/ops/lg_rag/, app/ops/skill_registry/]），
  `yaml.safe_load` 验证通过（waves=21 · 末 entry=p2b-t2-mcp-transport-session）。
- R1 审查文落盘：`docs/harness/reviews/task_p2b_t2_mcp_transport_session_audit_R1_20261116.md`（结论 GO）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03216 夜间授权）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | PASS（W3 自检结论占位符 draft 期合法 · W6 思考轮表头 warn-only 过渡） |
| registry yaml safe_load | PASS（21 waves · 末 entry=p2b-t2-mcp-transport-session） |

## 偏差

- D1-D5 已在 task 档「实现备忘 · 偏差登记」落笔：委派书节号 §5-①~⑥/§5-④/§7-①/§9.2
  在终稿不存在（以委派书内联细节为准）；握手降级链与终稿 §11 钉版调和；模块清单自裁定建包；
  e2e 采零依赖手工 stdio 脚本（委派书明示备选）；unregister 仅接口面注释 T3 挂点。

## 结果

10 draft 完成，进 30。
