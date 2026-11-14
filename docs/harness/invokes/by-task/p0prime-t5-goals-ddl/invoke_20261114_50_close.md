# Invoke 50 · CLOSE（p0prime-t5-goals-ddl · 2026-11-14）

## 结论
CLOSE。PR #375 CI 四件全绿 → squash merge df3177b2（master）。

## 验证台账
| 项 | 结果 |
|----|------|
| 目标用例 tests/test_ops_goals_ddl.py | 3 passed（本地真 PG brew postgresql@18） |
| 迁移 up/down/up | scratch 库实证通过（`DATABASE_URL` 覆盖 · 扩展预建体例承 T4） |
| 干净 worktree 全量（ddfd1074 · 无 .env · .venv 符号链接） | 2088 passed / 2 skipped / 1 failed |
| ruff (app tests) | All checks passed |
| lint-imports | 12 kept / 0 broken |
| graph compile | build_basic_agent / build_router_agent OK |
| spec-wave task lint | PASS（W3 占位符于本 close 回填消除） |
| PR #375 CI | check / import-linter / lint-wiki-delta / pytest 全 pass |

## 偏差登记
1. **唯一红 = 既有 `test_ta2_ttl_db_store_expired_not_consumed`**（baseline fee74fa7 同源 · T4 已登记 issue #23 · 建议另立 task · 不阻塞）。
2. **方法纠偏**：迁移实证首跑误用 `ALEMBIC_DATABASE_URL`（env.py 不读），迁移打到 dev 库 opsdesk；dev 终态=head 无数据损失（ops_goals 新建空表），后以 `DATABASE_URL` 覆盖在 scratch 库重做实证。教训已落 task 单经验节。
3. **附带修复**：01_modules.md:41 T4 遗留文本错位（capability_notes 收尾错位至 runs 条目后）随本波同行修复。
4. 01_modules db 行登记 + HG-GRAPH-MODULES 签收行已回写；registry status=closed 钉 wave_tip=df3177b。

## 人工闸
HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 approved（维护者 m00177「签收，开始」覆盖 P0' T1–T7）。
