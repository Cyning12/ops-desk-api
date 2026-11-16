# invoke_10 · draft（p2b-t5b-mcp-smoke-wrapup）

## 内容

- task 档落盘：`docs/tasks/active/task_p2b_t5b_mcp_smoke_wrapup.md` v1
  （背景/范围 6 条/非范围/失败路径/验收 · 纯文档波 · 人工闸三枚 approved）。
- registry N3 entry 追加：`docs/harness/audit_gates/registry.yaml`
  （status=active · base=bfbb855c · allowed_app_files=[] · allowed_tree_files 五件 ·
  allowed_tree_prefixes=invokes 目录 · banned_prefixes=[app/, tests/, alembic/, scripts/]）。
- R1 审查文落盘：`docs/harness/reviews/task_p2b_t5b_mcp_smoke_wrapup_audit_R1_20261116.md`（结论 GO · 窄面纯文档）。
- 人工闸：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved
  （issue Cyning12/ops-desk-workspace#23 m03064/m03216 夜间授权 + 11 设计终稿 §8 T5b 行）。

## 验证台账

| 项 | 结果 |
|---|---|
| task lint（`npx --yes spec-wave@3.5.0 task lint --file`） | 见 30_impl 台账 |
| registry yaml safe_load | PASS（末 entry=p2b-t5b-mcp-smoke-wrapup） |

## 偏差

- 冒烟配置驻仓外 /tmp（mcp_servers.yaml 仓内化属非范围 · 总闸 env 驱动）。
- 端口 8000 被 T5a 冒烟进程（PID 18921）占用 → 本波用 8001，不杀他波进程。

## 结果

GO → 30（冒烟已在总闸 env 开启的本地服务上执行 · 证据 /tmp/opsdesk-rfc/p2b-t5b/ + /tmp/opsdesk-rfc/p2b-t5b-exec.md）。