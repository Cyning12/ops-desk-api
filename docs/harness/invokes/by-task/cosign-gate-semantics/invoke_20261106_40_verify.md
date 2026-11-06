# invoke · 40 复跑 · cosign-gate-semantics（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `40`（复跑销项棒 · 承 issue #333 comment `6678465675` · 依据 2026-11-06 08:48 授权） |
| task_slug | `cosign-gate-semantics` |
| task 文件 | `docs/tasks/done/task_cosign_gate_semantics.md`（关账时 active→done 归档） |
| 复跑基点 | **独立复跑不采信 30 自报**：干净 worktree `/tmp/verify40-cosign` @ `3cc3e71`（origin/master · PR #352 squash merge） |
| 基线对拍 | `/tmp/verify40-cosign-base` @ `f78a721`（本 task 前置 base）定点复跑 4 枚红 |

## 复跑矩阵（本地 CI 同款 · GitHub Actions 自 04:20Z 零投递——维护者偏差告知①，机检以本地为准）

| 命令（worktree @ 3cc3e71） | 退出码 | 摘要 |
|------|--------|------|
| `pytest tests/test_cosign_gate_semantics.py` | 0 | 8 passed（新测机断断言全绿） |
| `pytest tests/test_prompt_packs.py` | 0 | 55 passed（关联回归 · 零适配确认） |
| `pytest tests`（全量） | 0 | 2083 passed · 4 failed = 既有红基线同形（diff-whitelist ×2 / embedder env ×1 / dualproc env ×1）· **零新增红** |
| `pytest <4 枚红>` @ base `f78a721`（定点基线对拍） | 1（预期） | 同 4 枚 failed（同 node id 同签名 · 7.21s 实锤）→ **零新增红对拍成立** |
| `ruff check app tests` | 0 | All checks passed! |
| `./scripts/graph-compile.sh` | 0 | EXIT=0 |
| `npx spec-wave@3.5.0 task lint --file <task>` | 0 | LINT: PASS |
| `npx spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS（scope all · missing 0 · issues 0） |
| `npx spec-wave@3.5.0 verify --target . --task <task>` | 0 | VERIFY: PASS（四闸 approved · GATE_VERIFY 唯一闸据不破） |
| spec 锚 grep（15 关键词） | 0 | 幂等锚 ×3 / 同锚重送达 / 同效力 / 不重复记录 / replay ×2 / 覆盖不设默认 ×2 / append-only / 显式声明替换意图 / 追加新行 ×2 / 旧行保留引注 ×2 / 拒重复不设 ×2 / 合法通路 / gate 记录层 ×3 / 消费门内 ×2 / residual_risk ×2 —— **15/15 全命中** |
| 红线对拍 `git diff f78a721..3cc3e71 --stat` | 0 | 8 文件全落签认承载面（docs/harness ×5 · docs/tasks · tests ×1）· `app/` / `alembic/` 零 diff · SSE 事件面零命中 |

## 结论

**40 复跑机制面 PASS** · 全绿 · 零新增红（基线同 4 枚逐字复证）· 红线对拍零命中 · spec 锚 15/15。偏差登记：①GitHub Actions 04:20Z 零投递（账户额度疑似耗尽 · 维护者告知在查 · 本地 CI 同款替代并注明）②worktree 无 `.env` 全量墙钟 ~90s（环境性 · 承先例）。

## 下一棒

50 CLOSE：active→done 归档 + CLOSE 档 `docs/tasks/close/close_cosign_gate_semantics_20261106.md` + 双 README + 50 invoke → 关账 PR 待 lead 验收。
