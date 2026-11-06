# invoke · 50 CLOSE · cosign-gate-semantics（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `50`（关账收口棒 · 承 issue #333 comment `6678465675`「全绿则关账」令） |
| task_slug | `cosign-gate-semantics` |
| task 文件 | `docs/tasks/done/task_cosign_gate_semantics.md`（本棒归档） |
| 分支 | `close/cosign-gate-semantics`（base `origin/master` @ `3cc3e71`） |

## 关账动作

1. **档迁**：`git mv docs/tasks/active/task_cosign_gate_semantics.md → docs/tasks/done/`（active 仅余 README.md · 活跃 0 件）。
2. **task 档头部回填**：状态 active→done（全棒链同日闭环摘要）· 40 注（40 复跑机制面 PASS + 基线对拍 + 偏差①②）· 分支行刷新 · orchestration 行补 40/50 · 修订表补 40/50 行。
3. **CLOSE 档**：`docs/tasks/close/close_cosign_gate_semantics_20261106.md`（任务信息 / 交付清单 / 验收核验七项全 PASS / 偏差与裁定留痕 / 关账动作 / 棒链留痕 · 体例承 seen-surface CLOSE）。
4. **双 README**：active/README 顶部增「单档关账」行（活跃 0 件）· done/README engineering 表增 2026-11-06 行。
5. **invoke 全齐**：10 / 20 / 30 / 40 / 50 五棒 invoke 全落盘 `docs/harness/invokes/by-task/cosign-gate-semantics/`。

## 验收锚（40 invoke 矩阵摘要）

- 独立复跑（worktree `/tmp/verify40-cosign` @ `3cc3e71`）：新测 8 / 关联 55 / 全量 2083 passed · 4 failed = base `f78a721` 同 4 枚逐字复证 · **零新增红**。
- ruff / graph-compile / task lint / lint-wiki-delta / verify 四闸 approved 全绿。
- spec 锚 grep 15/15 命中 · 红线对拍（app//alembic/SSE/闸表契约）零命中。
- 偏差①GitHub Actions 04:20Z 零投递（本地 CI 同款替代 · 维护者告知在查）②worktree 无 .env（环境性）。

## 留痕与移交

- issue #333 关 issue 由维护者执行（bot 不 close issue）。
- 分支 `agent/cosign-semantics-task-022a61b26cba` / `fix/cosign-gate-semantics` / `close/cosign-gate-semantics` 移交 00 统一清理（本 CLOSE 不删任何东西）。
- residual_risk 承档：0c88ac32 承载面在仓外运行时——消费门内判定不属本 task 语义，后续仓外转译以 FRAGMENT 落文为唯一真源。

## 自检（关账分支）

| 命令 | 结果 |
|------|------|
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | PASS（scope all · scanned 211 · missing 0 · issues 0） |
| `pytest tests/test_cosign_gate_semantics.py`（关账分支） | 8 passed |
