# invoke · 40-verify · diff-whitelist-anchor-drift（核验 30 交付 · 独立复跑 · 不采信自报）

| 项 | 值 |
|----|----|
| 帽 | `40-verify` · **日期** 2026-11-06 |
| task | `docs/tasks/active/task_diff_whitelist_anchor_drift.md` |
| 分支 | `agent/337-diff-whitelist-task-5e3e38c2abdd`（自 origin/master `18756ba` = PR #359 squash merge · 40 全程零仓内码改动 · 末段含票号 337 与工单名） |
| 核验对象 | PR #359 全量 diff（`0870fb4..18756ba` · tests 面 118 行）+ master 活链实测 |
| 依据 | issue #337 维护者（lead 代发）comment [`6685019068`](https://github.com/Cyning12/ops-desk-api/issues/337#issuecomment-6685019068)（40 棒授权 · 六条 40 内容逐项执行） |
| 结论 | **机制面 PASS**——30 自报全部独立复验成立（含浅克隆 N2 实证 · 本棒重点）；建议 50 CLOSE |

## 40 内容逐项执行记录

### 1. 两闸命令级独立复跑 + 全量零新增红 ✅

```
$ .venv/bin/python -m pytest \
    tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist \
    tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire -v
tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist PASSED  [ 50%]
tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire PASSED [100%]
========================= 2 passed, 1 warning in 0.16s =========================
```

```
$ .venv/bin/python -m pytest tests -q
2 failed, 2104 passed, 2 skipped, 1 warning in 38.57s
FAILED tests/test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker   ← 既有 env 红（CI skip 面）
FAILED tests/test_multi_replica_dualproc.py::test_hitl_cross_instance_resume         ← 既有 env 红（CI skip 面）
```

（逐枚核对：2 failed 与 30 出货前基线及各波次登记同形 · diff-whitelist ×2 转绿 · **零新增红**）

### 2. 浅克隆环境实证（N2 规格独立复验 · 本棒重点）✅

环境：`git clone --depth 1 file:///Users/cyning/src/ops-desk-api /tmp/shallow337` → HEAD `18756ba` · `git rev-parse d337486^{commit}` = **fatal: Needed a single revision**（base 对象缺失 · 浅克隆真实形态）。

**两闸全输出（`-s` 捕获审计行）**：

```
[TC8] 基线退化：d337486 不可用，取 merge-base HEAD origin/master = 18756ba5dafb
[TC8] committed 面跳过：_WAVE_TIP c17e63b 不可解析（浅克隆? · N2 规格：不退化为 vs HEAD 增长窗）
.[TC8] 基线退化：a1591e9 不可用，取 merge-base HEAD origin/master = 18756ba5dafb
[TC8] committed 面跳过：_WAVE_TIP 63bad3d 不可解析（浅克隆? · N2 规格：不退化为 vs HEAD 增长窗）
2 passed, 1 warning in 0.50s
```

**banned 在途探针（O2 原样咬）**：

```
$ touch scripts/.tc8_banned_probe
E  AssertionError: 禁改面（scripts/ alembic/ 及其余 app/）出现改动: ['scripts/.tc8_banned_probe']
tests/test_lg_rag_write_replay_guard.py:490: AssertionError
1 failed   → 探针已删（零残留）
```

**行为链判定**：base 缺失 → 态② merge-base 退化 → `_changed_faces` N2 分支（tip 不可解析 → 审计输出跳过 committed 面 · 代码中无 vs HEAD 增长面回退路径）→ 干净树 2 passed；在途触碰禁改面仍即时 fail——**与签认规格逐字吻合**；与 GitHub CI（fetch-depth=1）绿现状自洽。

### 3. 固定窗语义逐行审查 ✅

`git diff 0870fb4 18756ba -- tests/` 118 行逐行亲读（审查文 §3 对照表）：`_changed_faces` 两闸同构 · committed 闭窗 `_BASE.._WAVE_TIP` · 未提交面 vs HEAD · untracked · N2 双分支带审计输出 · banned 前置/O2/四态/`_touched_in_wave` **零改动** · 态④兜底原样。四锚值未动（git diff 无变更行 + grep 实证：`d337486`/`c17e63b`/`a1591e9`/`63bad3d` 全在册）。

### 4. F1 两件登记核对 ✅

限定语逐字在册（「仅 CLOSE 落盘面，禁承载其他改动」/「前波次 query-coref…仅审查文入库面 · 禁承载其他改动」· 引据 `920c8e5` [00]）；闭窗独立复数 **wave1=15 文件 / wave2=13 文件**（与 20-R1 审查实录一致）；溯源 `git log d337486..c17e63b -- <两文件>` 均命中 `920c8e5`。

### 5. 红线对拍 ✅

40 棒全程**零仓内码改动**（仅本 invoke + 审查文 + task 档回填三文档面）；`git diff origin/master...HEAD --name-only | grep -v '^docs/'` 空集。

### 6. 质量门 ✅

| 命令 | 结果 |
|------|------|
| `.venv/bin/ruff check tests/test_lg_rag_write_replay_guard.py tests/test_strategy_scenario.py` | All checks passed! |
| `npx spec-wave@3.5.0 task lint --file <本档>` | LINT: PASS（零 warn） |
| `npx spec-wave@3.5.0 task lint-wiki-delta --target .` | LINT-WIKI-DELTA: PASS（213/0） |
| `npx spec-wave@3.5.0 verify --target . --task <本档>` | VERIFY: PASS（四闸 approved） |
| CI | 待本 PR 跑（出货后补登） |

## 闸语义对拍（30 invoke GATE_VERIFY 表 × 本授权）

| 闸 | 30 invoke 表 | 本授权 `6685019068` 闸签回执 | 一致？ |
|----|--------------|------------------------------|--------|
| HG-TASK-DRAFT | approved（comment `6683541162`） | 随档签（`6683541162`） | ✅ |
| HG-AUDIT-R1 | approved（签录 `0870fb4` · review `5799605736`） | 随 PR #358 签（review `5799605736` · 签录 `0870fb4`） | ✅ |
| HG-GRAPH-MODULES | approved（`none` 口径） | `none` 口径随档签 | ✅ |
| HG-DIFF-WHITELIST-DIAGNOSIS | approved（status 单元格修复 · 引据 GO 评论 `6684073257`） | 随 PR #358 签（裁决 = whitelist 过期→刷新基线 · 子形态=改固定波次窗语义） | ✅ |

另比对 30 invoke 落地三件套/三实证/红线对拍各项与本授权 40 内容①-⑥：全部可复验项已亲跑复验成立。

## 偏差登记

**无实质偏差。** 观察（非偏差）：浅克隆下 base 走态② merge-base 退化而非态④ skip——属 00 裁定态②原义（干净浅克隆树两闸均 pass），30 invoke 未逐字预告但在签认语义内。

## FAIL 判定扫描

30 无造假：红侧基线逐字一致（10/20/30/40 四棒同形）· 两闸 2 passed 独立复跑成立 · N2 浅克隆行为链逐字吻合签认规格 · F1 溯源三方一致（`920c8e5`）· 全量零新增红 · 红线对拍零命中。

## 出货

- 40 review 文：`docs/harness/reviews/task_diff_whitelist_anchor_drift_review_40_20261106.md`（机制面 PASS · 建议 50 CLOSE）
- 下一棒：50 CLOSE（active→done 归档 + CLOSE 档 + README · 关账 PR 待 lead 验收）· issue #337 关 issue 由维护者执行
