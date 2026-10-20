# invoke · #3 scenario-stage-rewire · 30 跨波次基线修正（00 裁定落实）

- 日期：2026-10-20 · 帽：30 · 分支：task/scenario-stage-rewire
- 裁定来源：父 Agent（00）指令（遗留挂账 1 → 结构性问题裁定）
- 性质：测试基建语义修正 · 行为面零动（freeze lg-rag-sse-v1 / lg-rag-http-v1 无涉）

## 1. 问题定性（00 裁定链）

- #2 tests/test_memory_injection_consumer.py::test_phase_b_diff_whitelist 钉锚 _BASE="414270d"，
  波次使命于 PR #285（merge commit 51e75c9）时点已完成；固定基线跨波次失效。
- 地面真值核验：干净 worktree @ 51e75c9（= origin/master）跑该闸即 FAILED
  （AssertionError :625 · 越界 = docs/tasks/done/task_memory_injection_consumer.md，
  系 #2 CLOSE commit 55424d4 自 active/ 移入，未登记 _UPSTREAM_SIGN_PATHS）——
  **master 自 PR #285 即红，非待 #3 合并才红**。

## 2. 修法（四态语义）

_resolve_base 链路第四态（_WAVE_TIP="51e75c9" · _touched_in_wave(root, path) =
git log 414270d..51e75c9 -- <path> 非空；锚点不可解析/命令异常 → 保守 internal=True 保牙）：

| 态 | 条件 | 结果 |
|---|---|---|
| 1 | 钉锚 414270d 命中 ∧ diff ⊆ 白名单 | pass（照旧） |
| 2 | 钉锚命中 ∧ 越出面含波次内文件（被改动/未登记） | **fail（回归牙保留）** |
| 3 | 钉锚命中 ∧ 越出面全为后续波次产物（foreign） | **skip（新增 · 可审计）** |
| 4 | 钉锚不可解析 | skip（三级探测既有 · 带 tried 清单） |

skip reason 全文带实测越界文件清单（pytest -rs 可见）。
CLOSE 移动面 docs/tasks/done/task_memory_injection_consumer.md 补登记
_UPSTREAM_SIGN_PATHS（00 落签面同类 · 治 master 即红）。
#3 tests/test_strategy_scenario.py::_TREE_ALLOWED_FILES 同步补入
tests/test_memory_injection_consumer.py（注释注明 00 裁定 · 跨波次基线修正）。

## 3. 验证证据（三态 + 分类器真值）

- **本地分支（钉锚命中 ∧ 越出=#3 全 foreign）**：#2 闸 1 skipped
  （reason 列 9 件 #3 文件全为后续波次产物）；#3 全套 35 passed。
- **master@51e75c9 + 修正文件覆贴**：#2 闸 **1 passed**（done/ 补登记后 violations 空）——master 红治愈。
- **模拟 #3 合并后 master**（worktree /tmp/ops-desk-master-51e75c9 merge task/scenario-stage-rewire · fast-forward 至实现头）：
  #2 闸 1 skipped（不红 · reason 列 #3 九件）；#3 闸 1 passed。
- **分类器真值**（_touched_in_wave @ 主仓）：
  continuity.py（波内 · 已白名单）=True · builder.py（#3 后续波次）=False ·
  done/ task（CLOSE 移动面 · 波次内）=True（故须登记而非 skip）·
  scenario invoke（#3）=False。
- ruff check 两测试文件 All checks passed。

## 4. 禁区自查

- 改动仅两测试文件：tests/test_memory_injection_consumer.py · tests/test_strategy_scenario.py（白名单常量）。
- app/ 零触达；scripts//alembic/ 零触达；零新 event_type/路由/表。
- #2 波次内文件改动的回归牙（态 2 fail）原样保留；skip 仅放行 foreign 波次产物。
