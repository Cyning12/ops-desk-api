# invoke · #3 scenario-stage-rewire · 30 收尾（40=approve 审查文入库 + 00 裁定 O1/O2/O4）

- 日期：2026-10-20 · 帽：30 · 分支：task/scenario-stage-rewire
- 裁定来源：父 Agent（00）收尾指令（40=approve · 审查文入库 + O1/O2 预防性处置 + O4 nit）
- 性质：测试基建语义修正 + 注释行级去重 · 行为面零动（freeze lg-rag-sse-v1 / lg-rag-http-v1 无涉）

## 1. 裁定链落实清单

| 项 | 裁定 | 落实 |
|---|---|---|
| A | review40 审查文入库（40 落盘 125 行未 commit · 沿用 #2 裁定路径） | docs/harness/reviews/task_scenario_stage_rewire_review40_20261020.md 入库 + 补登记 _TREE_ALLOWED_FILES（注释注明 40 落签面同类） |
| O1 | #3 闸补第四态：CLOSE 移动面登记 + 未来波次越界可审计 skip（语义照抄 #2 四态） | done/task_scenario_stage_rewire.md 补登记（00 落签面同类）；_WAVE_TIP=None 占位（CLOSE 时由 00 钉死为 #3 合并 commit）+ _touched_in_wave 等价判定 |
| O2 | 态3 skip 判定前先做 banned 前缀断言 | banned（scripts//alembic/ 及其余 app/ · 含 untracked）断言提至 skip 分支之前 |
| O4 | builder.py:122-125 docstring 两个「allowlist = …」重复句去重 | 合并为单句（保留 S1 求交/未知 key → []/摘除等价三要素 · 注释行级） |
| O3 | dormant audit 性质无覆盖 | 仅记录 · 移交 #5/后续：scenario.py dormant 期 audit_scenario_stripped 无生产调用方故无行为覆盖需求；若未来复用须另立 SPEC 时补测 |
| O5 | /tmp 残留仓外 | 不管（仓外） |

## 2. 四态语义（#3 闸 · tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire）

| 态 | 条件 | 结果 |
|---|---|---|
| 1 | 钉锚 a1591e9 命中 ∧ diff ⊆ 白名单 | pass |
| 2 | 越出面含波次窗内文件（_touched_in_wave=True） | **fail（回归牙保留）** |
| 3 | 越出面全为后续波次产物（foreign） | **skip（reason 带越界清单）** |
| 0 | 任何形态含 banned 前缀路径 | **fail（O2 · 先于态 3 判定）** |

_WAVE_TIP 未定期间的等价逻辑（00 裁定口径「钉锚后仅本波次文件」）：本闸在波次内
即钉死改动面 ⊆ 声明面（_allowed），故越界路径只可能来自后续波次 → 态 3 skip；
钉死后恢复 git log a1591e9.._WAVE_TIP 全量历史判定，态 2 牙全量生效（波次窗内
未登记面被触碰 → fail，防绕过闸的强合并）。

## 3. 验证矩阵（全实测）

| 形态 | 结果 |
|---|---|
| 本分支 #3 闸 | **1 passed** |
| 本分支 #2 闸 | **1 skipped**（态 3 · reason 列 #3 十件全 foreign） |
| 本分支全量（park .env） | **1743 passed, 183 skipped, 0 failed**（24s · 较上一程 182 skipped +1 = #2 闸转 skip · 零失败） |
| SIM1 模拟 CLOSE（worktree git mv active/→done/ · staged） | #3 闸 **1 passed**（done/ 已登记） |
| SIM2 模拟 #4 假想合入（staged docs/tasks/active/task_fake_wave4.md + docs/guides/FAKE_wave4.md） | #3 闸 **1 skipped**（态 3 · reason 列两件 foreign · 不红） |
| SIM3 banned 越界（staged scripts/fake_wave4.py） | #3 闸 **1 failed**（AssertionError 禁改面 :550 · 先于 skip :558 · O2 生效） |
| ruff app tests | All checks passed |

注：SIM2 首跑误带 untracked app/ops/strategy/builder.py.tmp → banned 断言正确截停
（含 untracked 防新文件绕过口径实测有效 · 非缺陷）。

## 4. 禁区自查

- 改动面：tests/test_strategy_scenario.py · app/ops/strategy/builder.py（docstring 行级）·
  docs/harness/reviews/task_scenario_stage_rewire_review40_20261020.md（入库）· 本 invoke。
- scripts//alembic/ 零触达；零新 event_type/路由/表；SSE 帧/HTTP 契约零变化。
- 模拟 worktree /tmp/ops-desk-sim-close 已清理；.env 主仓在场；工作区仅他务预存
  untracked（backups/ · task_query_coref_rewrite_review40_20261019.md）维持挂账未纳管。
