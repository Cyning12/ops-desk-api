# invoke · 50 CLOSE · ops-write-catalog-reconcile（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `50`（关账收口棒 · 承 issue #336 comment [`6681442245`](https://github.com/Cyning12/ops-desk-api/issues/336#issuecomment-6681442245)「40 复跑销项 · 全绿则关账」令 · 依据 13:40 多选授权） |
| task_slug | `ops-write-catalog-reconcile` |
| task 文件 | `docs/tasks/done/task_ops_write_catalog_reconcile.md`（本棒归档） |
| 分支 | `close/ops-write-catalog-reconcile`（base `origin/master` @ `039f802`） |

## 关账动作

1. **档迁**：`git mv docs/tasks/active/task_ops_write_catalog_reconcile.md → docs/tasks/done/`（active 仅余 README.md · 活跃 0 件）。
2. **task 档头部回填**：状态 done（全棒链同日闭环摘要）· orchestration 行补 40/50 · 修订表补 40/50 行。
3. **CLOSE 档**：`docs/tasks/close/close_ops_write_catalog_reconcile_20261106.md`（任务信息 / 交付清单 / 验收核验七项全 PASS / 偏差与裁定留痕 / 关账动作 · 体例承 cosign CLOSE）。
4. **双 README**：active/README 顶部增「单档关账」行（活跃 0 件）· done/README 增 2026-11-06 归档行。
5. **invoke 全齐**：10 / 20 / 30 / 40 / 50 五棒 invoke 全落盘 `docs/harness/invokes/by-task/ops-write-catalog-reconcile/`（20 为 30 期遗漏 · 本棒随审查文补档 · 非自签转录）。

## 验收锚（40 invoke 矩阵摘要）

- 独立复跑（worktree `/tmp/verify40-recon` @ `039f802`）：新测 19 / 关联 114 / 全量 2102 passed · 4 failed = 既有基线同形 · **零新增红** · 漂移反向实证 10/10。
- ruff / graph-compile / task lint / lint-wiki-delta / **verify 四闸 approved PASS**（20-R1 审查文 + 20 invoke 补档后闸据完整）。
- 红线对拍：app/ / alembic 零 diff · SSE 事件面零触碰 · 既有断言零放宽。
- 对账实扫发现声明↔行为漂移 2 枚（receipt / duplicate_of · 测试钉死 · 声明面对齐建议另案）。

## 留痕与移交

- issue #336 关 issue 由维护者执行（bot 不 close issue）。
- 分支 `agent/catalog-reconcile-task-e848e9dbbf56` / `fix/ops-write-catalog-reconcile` / `close/ops-write-catalog-reconcile` 移交 00 统一清理（本 CLOSE 不删任何东西）。
- residual_risk 承档：「三能力」字面与实扫一枚之差随 A1 扩展锚消解 · 偏差②另案裁决。

## 自检（关账分支）

| 命令 | 结果 |
|------|------|
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/done/task_ops_write_catalog_reconcile.md` | PASS |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | PASS（scope all · missing 0 · issues 0） |
| `pytest tests/test_ops_write_catalog_reconcile.py -q`（关账分支） | 19 passed |
| `npx --yes spec-wave@3.5.0 verify --target . --task docs/tasks/done/task_ops_write_catalog_reconcile.md` | VERIFY: PASS（四闸 approved） |
