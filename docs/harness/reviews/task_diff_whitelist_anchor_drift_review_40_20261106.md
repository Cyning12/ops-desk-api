# task_diff_whitelist_anchor_drift 40 核验（独立复跑 · 不采信 30 自报）

> **核验对象**：PR #359 squash merge → master HEAD `18756ba`（30 交付：两闸固定波次窗语义 + F1 补登记 + N2 规格）
> **核验帽**：40-verify（独立复跑 · 全程零仓内码改动 · 不采信 30 自报）
> **核验日期**：2026-11-06 · **核验时仓态**：`agent/337-diff-whitelist-task-5e3e38c2abdd` @ `18756ba`（= origin/master · 干净树）
> **授权**：issue #337 维护者（lead 代发）comment `6685019068`（2026-11-06 20:39 · 40 棒授权 · 19:04 大授权窗口链）
> **结论**：**机制面 PASS**——30 自报全部独立复验成立（两闸 2 passed / 全量零新增红 / 浅克隆 N2 实证 / 固定窗逐行审查 / F1 限定语逐字核对 / 红线对拍零命中）；**建议 50 CLOSE**（active→done 归档 · 四字段）

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| 两闸命令级独立复跑（非转录） | ✅ **2 passed**（`test_tc8_diff_whitelist` + `test_diff_whitelist_scenario_stage_rewire` · `-v` 亲跑 · 不采信 30 输出） |
| 全量套件独立复跑 | ✅ **2104 passed · 2 failed** = 既有 env 依赖红（`test_embedder_failure_degrades_with_marker` / `test_hitl_cross_instance_resume` · 与 30 档及既往各波次基线逐枚同形）· **diff-whitelist ×2 转绿 · 零新增红** |
| **浅克隆 N2 实证（本棒重点）** | ✅ **深度 1 全新浅克隆**（`/tmp/shallow337` @ `18756ba`）：两闸 committed 面**带审计输出跳过**（`[TC8] committed 面跳过：_WAVE_TIP c17e63b/63bad3d 不可解析（浅克隆? · N2 规格：不退化为 vs HEAD 增长窗）`）→ **2 passed**；banned 在途探针（`scripts/.tc8_banned_probe`）→ **fail**（O2 原样咬 · 探针已删）——输出全文见 40 invoke |
| 固定窗语义逐行审查 | ✅ diff `0870fb4..18756ba` 全量 118 行逐行亲读：`_changed_faces` 两闸同构（committed 闭窗 + 未提交面 vs HEAD + untracked + N2 分支）· 四锚值未动（`d337486`/`c17e63b`/`a1591e9`/`63bad3d` · 独立 grep 实证）· banned 前置/O2/四态/`_touched_in_wave` 回归牙**零改动** |
| F1 两件登记核对 | ✅ 限定语逐字在册（「仅 CLOSE 落盘面，禁承载其他改动」+「前波次 query-coref…仅审查文入库面」· 引据 `920c8e5` [00]）· 闭窗独立复数 wave1=15 文件 / wave2=13 文件与 20-R1 审查实录一致 |
| 红线对拍（40 棒自身） | ✅ 40 全程零仓内码改动 · `git diff origin/master...HEAD --name-only` 非 docs 面空集（待本 PR 文档落盘后仍仅 docs 面） |
| 质量门 | ✅ `ruff check` 两触及文件 All checks passed · `task lint` PASS（零 warn）· `lint-wiki-delta` PASS（213/0）· `verify` PASS（四闸 approved）· CI 待本 PR 跑 |
| 闸语义对拍（GATE_VERIFY 表比对） | ✅ 30 invoke GATE_VERIFY 表（HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES/HG-DIFF-WHITELIST-DIAGNOSIS 全 approved · status 修复记录引据 GO 评论 `6684073257`）与本授权「闸签回执：四闸全 approved」**逐条一致** |

## 逐项核验

### 1. 两闸独立复跑（40 内容①）

```
$ .venv/bin/python -m pytest \
    tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist \
    tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire -v
tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist PASSED  [ 50%]
tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire PASSED [100%]
========================= 2 passed, 1 warning in 0.16s =========================
```

全量：`2104 passed · 2 failed · 2 skipped`——2 failed 逐枚核对为 env 依赖既有红（embedder / dualproc · CI skip 面 · 与 30 出货前基线同形），零新增红。

### 2. 浅克隆 N2 实证（40 内容② · 重点）

```
$ git clone --depth 1 file:///…/ops-desk-api /tmp/shallow337   # @ 18756ba
$ cd /tmp/shallow337 && pytest <两闸> -s -q
[TC8] 基线退化：d337486 不可用，取 merge-base HEAD origin/master = 18756ba5dafb
[TC8] committed 面跳过：_WAVE_TIP c17e63b 不可解析（浅克隆? · N2 规格：不退化为 vs HEAD 增长窗）
[TC8] 基线退化：a1591e9 不可用，取 merge-base HEAD origin/master = 18756ba5dafb
[TC8] committed 面跳过：_WAVE_TIP 63bad3d 不可解析（浅克隆? · N2 规格：不退化为 vs HEAD 增长窗）
2 passed, 1 warning in 0.50s

$ touch scripts/.tc8_banned_probe && pytest ::test_tc8_diff_whitelist -q
E  AssertionError: 禁改面（scripts/ alembic/ 及其余 app/）出现改动: ['scripts/.tc8_banned_probe']
1 failed   （探针已删 · O2 在浅克隆环境原样咬）
```

**行为链核验**：浅克隆下 base 缺失 → `_resolve_base` 态②退化（merge-base HEAD origin/master）→ `_changed_faces` N2 分支命中（tip 不可解析 → 审计输出跳过 committed 面 · **绝不退化为 vs HEAD 增长窗**）→ 干净树 2 passed；在途触碰禁改面仍即时 fail——与签认规格逐字吻合。另注：真实 GitHub CI（fetch-depth=1）行为与本实证同链（态②+N2），CI 绿与此不冲突。

### 3. 固定窗语义逐行审查（40 内容③）

`git diff 0870fb4 18756ba -- tests/`（118 行）逐行亲读：

| 审查点 | 裁定 |
|--------|------|
| `_changed_faces`（test_lg_rag_write_replay_guard.py :427-461） | ✅ committed 面 = `("diff","--name-only",base,_WAVE_TIP)` 闭窗 · 未提交面 = 工作区/暂存 vs HEAD · untracked 并集 · N2 两分支（未钉/不可解析）皆带审计输出且不引入 vs HEAD 增长面 |
| `_changed_faces`（test_strategy_scenario.py :537-561） | ✅ 与上同构照抄（该文件无 `_changed_and_untracked` 助手故内联展开 · 语义逐字等价） |
| `test_tc8_diff_whitelist` 主流程 | ✅ 唯一定改变量 = `_changed_faces(root, base)` 替换三行 diff 面 · banned 前置/O2/四态③④/`_touched_in_wave` 全零改动 |
| `test_diff_whitelist_scenario_stage_rewire` 主流程 | ✅ 同上 · `_resolve_base` 三级探测零改动 |
| 四锚值 | ✅ `_BASE`/`_WAVE_TIP` 四值未动（git diff 无该行变更 + 独立 grep 实证）——修窗不修史（FP-7） |

### 4. F1 登记核对（40 内容④）

- 限定语逐字：「仅 CLOSE 落盘面，禁承载其他改动」（backups snapshot）/「前波次 query-coref 审查文随 CLOSE commit `920c8e5` 入库面 · 仅审查文入库面，禁承载其他改动」（review40）——**与 20-R1 N1 口径一致**；
- 闭窗白名单覆盖独立复数：wave1 闭窗 15 文件经登记全白名单（banned 面空）· wave2 闭窗 13 文件全白名单（20-R1 实录 15/13 复数一致）；
- 溯源独立复核：`git log d337486..c17e63b -- <两文件>` 均命中 `920c8e5` [00]（与 20-R1/30 档链一致）。

### 5. 偏差登记

**无实质偏差。** 观察一条（非偏差）：浅克隆下 base 走态② merge-base 退化（非态④ skip）——两闸在干净浅克隆树均 pass（committed 面 N2 跳过），与 GitHub CI 绿现状自洽；该行为链 30 invoke 未逐字预告但属签认语义内（态②为 00 裁定原义），不构成偏差。

## 给维护者的裁定建议

1. **40 机制面 PASS · 建议 50 CLOSE**：active→done 归档 + CLOSE 档（`docs/tasks/close/` 四字段）+ README 登记 · 关账 PR 待 lead 验收；
2. 下一波如需 committed 面审计须自注册新闸（20-R1 N3 口径 · 本闸已转「闭窗档案 + 在途守卫」）——建议写入 invoke/README 视野，非本 task 阻塞项。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-11-06 | 40 核验落盘（`18756ba`）：两闸 2 passed 独立复跑 + 全量 2104 passed 零新增红 + **浅克隆 N2 实证**（审计输出跳过 committed 面 · banned 探针原样咬）+ 固定窗逐行审查（锚值未动 · 闸语义零改动）+ F1 限定语逐字核对 + 红线对拍零命中 + GATE_VERIFY 表与授权逐条一致——**机制面 PASS · 建议 50 CLOSE**（偏差：无实质偏差） |
