# invoke_50 · close（p2b-t1-mcp-legacy-config）

## 内容

50 CLOSE 关账：feat PR #408 squash merge 完成（wave_tip=64791fc5），registry
status active→closed 钉 wave_tip，task 档 active→done。

## 验证台账

| 项 | 结果 |
|---|---|
| feat PR | #408 · squash merge · 分支已删（远程） |
| CI 四绿 | pytest pass (2m26s) · check pass · import-linter pass · lint-wiki-delta pass |
| wave_tip | `64791fc5`（feat(capability): P2b-T1 … (#408)） |
| registry | status=closed · base=bf1c23f2 · wave_tip=64791fc5 |
| task 档 | docs/tasks/active/ → docs/tasks/done/task_p2b_t1_mcp_legacy_config.md |
| `spec-wave verify`（done 档） | PASS |
| 全量 pytest（五键 blank） | 2205 passed, 1 skipped |
| 验收 grep | 五符号 + env 键在 app/ tests/ .env.example docs/spec/ docs/_tech_graph/ 零命中 |

## 偏差终录

1. **D1**：`adapters/mcp.py`:5 docstring 一行改写——原含 `McpClientAdapter`
   字样，验收 grep 零命中要求必清；整文件删除属 T4，本单 docstring-only
   无行为变化（registry allowed_app_files 已预含该文件）。
2. **D2**：`probes.py`:13-14 与 `http_generic.py`:246 两处 stale docstring
   指针顺手清（各一行 · 指向已删模块的死指针 · 无行为变化）。
3. **D3**：ROADMAP:95 历史表行（2026-08-26 U3 落地记录，含 FakeTransport
   字样）属档案行不动；`docs/tasks/done/task_cap_mcp_real.md`、
   `docs/audits/task-review/20261011_*`、`docs/harness/reviews/task_cap_mcp_real_*`、
   `docs/harness/invokes/by-task/cap-mcp-real/*` 档案豁免（grep 命中但属冻结档案）。

## 结果

CLOSE GO · P2b-T1 关账完成。T2（传输与 runtime 接线）可基于
`mcp_config.py` 配置面开工。
