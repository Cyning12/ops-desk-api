# invoke · 30 实现 · diff-whitelist-anchor-drift（2026-11-06）

| 项 | 值 |
|----|----|
| hat | `30`（实扫落码 · 承 issue #337 维护者（lead 代发）comment `6684073257` 30 棒授权 GO） |
| task_slug | `diff-whitelist-anchor-drift` |
| task 文件 | `docs/tasks/active/task_diff_whitelist_anchor_drift.md` |
| 分支 | `fix/diff-whitelist-anchor-drift`（自 origin/master `0870fb4` 切出 · 预登记在册） |
| 授权依据 | issue #337 comment [`6684073257`](https://github.com/Cyning12/ops-desk-api/issues/337#issuecomment-6684073257)（2026-11-06 19:46 · lead 代维护者下发 · 19:04 大授权窗口 + 13:40 多选授权链）· 四闸全 approved（HG-TASK-DRAFT/HG-GRAPH-MODULES=comment `6683541162` 随档签 · HG-AUDIT-R1/HG-DIFF-WHITELIST-DIAGNOSIS=PR #358 review `5799605736` 签 · 签录 `0870fb4`）· **设计闸裁决 = whitelist 过期 → 刷新基线 · 子形态 = 改固定波次窗语义** |
| 交付 | 两枚闸 `_changed_faces` 固定波次窗语义 + F1 两件 00 裁定式登记 + N2 浅克隆退化规格 · 红转绿双证据 · 闸语义对拍三实证 |

## 人工闸扫描（GATE_VERIFY · 30 改码前首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | GO 评论 `6684073257`「四闸全 approved」 | Y | Y | ✅ |
| HG-AUDIT-R1 | approved（签录 `0870fb4` · 依据 review `5799605736`） | 同上 | Y | Y | ✅ |
| HG-GRAPH-MODULES | approved（`none` 口径 · comment `6683541162`） | 同上 | Y | — | ✅ |
| HG-DIFF-WHITELIST-DIAGNOSIS | approved（签录全文在册 · **status 单元格修复** · 见下） | 同上 | Y | Y | ✅ |

- **status 单元格修复（开工前置 · 非自签）**：签录 commit `0870fb4` 已录 HG-DIFF-WHITELIST-DIAGNOSIS 正式签认全文入闸表行说明，但**漏翻 status 单元格**（机读 VERIFY 报 pending 拒 30）——依 GO 评论 `6684073257`「闸签回执：四闸全 approved——HG-DIFF-WHITELIST-DIAGNOSIS 随 20-R1 PR #358 正式签（review `5799605736` · merge `172a780` · 签录 `0870fb4`）」补翻 approved（commit `7748dfe` · 修复记录写入闸表行说明 · 签认本体 = 行内「正式签认」全文）。
- 机械辅助：`npx spec-wave@3.5.0 verify --target . --task docs/tasks/active/task_diff_whitelist_anchor_drift.md` → **VERIFY: PASS**（修复后实跑 · 收尾再跑一致）。

**结论：可进入读码/改码**（首输出于改码前完成 · 本 invoke 为过程留痕）

## 落地三件套（签认形态② · 30 只执行签认分支 FP-5）

| # | 件 | 落点 | 说明 |
|---|----|------|------|
| ① | **F1 两件 00 裁定式登记** | `tests/test_lg_rag_write_replay_guard.py::_TREE_ALLOWED_FILES` | `backups/local_qdrant_orphan_cleanup_20261018T005320Z/…snapshot` + `docs/harness/reviews/task_query_coref_rewrite_review40_20261019.md`（前波次归属注明 · 20-R1 N1）——限定语引据 CLOSE commit `920c8e5` [00] · 仅 CLOSE 落盘面禁承载其他改动 |
| ② | **固定波次窗语义** | 两枚闸新增 `_changed_faces` 助手 | committed 面 = `_BASE.._WAVE_TIP` **闭窗**（不随 master 增长 · whitelist 过期型漂移的结构性修复）；未提交面 = 工作区/暂存 vs HEAD；外加 untracked；banned 前置（O2）作用并集面**原样** |
| ③ | **N2 浅克隆退化规格** | `_changed_faces` 内 | `_WAVE_TIP` 未钉/不可解析 → **带审计输出跳过 committed 面**（`[TC8] committed 面跳过：…N2 规格：不退化为 vs HEAD 增长窗`）· 绝不退化 vs HEAD 增长窗（否则浅克隆复现结构性常态红） |

- 四态语义 / O2 banned 前置 / 回归牙（`_touched_in_wave`）**零改动原样保留**；态④（锚缺失兜底）原样。
- `_WAVE_TIP` 钉锚值与 `_BASE` 不变（`d337486`/`c17e63b` · `a1591e9`/`63bad3d`）——修窗不修史（FP-7）。

## 红测取证（A1 语义一 · 证据先于裁决）

**红证据（`7748dfe` 干净树 · 修复前）**：

```
$ .venv/bin/python -m pytest \
    tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist \
    tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire
E  AssertionError: 禁改面（scripts/ alembic/ 及其余 app/）出现改动: ['alembic/versions/20261105_capability_notes.py',
   'app/db/models.py', …（共 22 件）…, 'scripts/graph-compile.sh']
tests/test_lg_rag_write_replay_guard.py:450: AssertionError
E  AssertionError: 禁改面（scripts/ alembic/）出现改动: ['alembic/versions/20261105_capability_notes.py',
   'scripts/graph-compile.sh']
tests/test_strategy_scenario.py:554: AssertionError
FAILED tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist
FAILED tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire
========= 2 failed in 0.19s =========
```

（与 10/20 档登记逐字一致 · 题面缺陷现状无漂移）

**绿证据（`f4d9c9c` 干净树 · 修复后同命令）**：

```
$ .venv/bin/python -m pytest \
    tests/test_lg_rag_write_replay_guard.py::test_tc8_diff_whitelist \
    tests/test_strategy_scenario.py::test_diff_whitelist_scenario_stage_rewire
========================= 2 passed, 1 warning in 0.14s =========================
```

（两闸 committed 闭窗求值：wave1 窗 15 文件经 F1 登记全白名单 · wave2 窗 13 文件全白名单 → 态① pass ×2）

## 闸语义对拍三实证（验收「防恒绿失效」条）

| 实证 | 构造 | 结果 |
|------|------|------|
| **回归牙** | 临时摘除 F1 登记之一（query-coref 审查文 · sed 摘除→还原） | `AssertionError: diff 越白名单且属本波次窗内文件（回归牙）: ['docs/harness/reviews/task_query_coref_rewrite40_20261019.md']` → **1 failed** ✅ 牙原样咬 |
| **banned 在途（O2）** | `touch scripts/.tc8_banned_probe`（untracked 探针 · 用后删除） | `AssertionError: 禁改面（scripts/ alembic/ 及其余 app/）出现改动: ['scripts/.tc8_banned_probe']` → **1 failed** ✅ O2 前置原样咬 |
| **N2 浅克隆退化** | `_WAVE_TIP` 临时置 bogus（sed 置→还原） | `[TC8] committed 面跳过：_WAVE_TIP deadbeef0 不可解析（浅克隆? · N2 规格：不退化为 vs HEAD 增长窗）` → **1 passed**（干净语义）✅ 审计输出 + 不崩 + 不退化 |
| 偏差登记 | 脏树 + tip 不可解析组合（演示副产物） | scenario 闸 workspace 面越界文件经 `_touched_in_wave` 保守 True（锚不可解析 → 保牙 · 既有契约）→ fail-closed——**真实浅克隆 CI 为干净树 → pass**；保守语义如实登记不修正（fail-closed 是既有裁定） |

## 验证

| 命令 | 结果 |
|------|------|
| `.venv/bin/python -m pytest tests -q` | **2103 passed · 2 failed** = 既有 env 依赖红（`test_embedder_failure_degrades_with_marker` / `test_hitl_cross_instance_resume` · 基线同形）· **diff-whitelist ×2 转绿 · 零新增红**（基线 4 failed → 2 failed） |
| `.venv/bin/ruff check tests/test_lg_rag_write_replay_guard.py tests/test_strategy_scenario.py` | All checks passed!（零新增） |
| `./scripts/graph-compile.sh` | done（EXIT=0 · 无图谱面改动） |
| `git diff origin/master...HEAD --name-only \| grep -v '^docs/'` | `tests/test_lg_rag_write_replay_guard.py` / `tests/test_strategy_scenario.py` **两枚**——红线对拍零命中（`app/` `scripts/` `alembic/` SSE/freeze 零 diff） |
| `npx spec-wave@3.5.0 task lint --file <本档>` | LINT: PASS（零 warn） |
| `npx spec-wave@3.5.0 task lint-wiki-delta --target .` | LINT-WIKI-DELTA: PASS（213/0） |
| `npx spec-wave@3.5.0 verify --target . --task <本档>` | VERIFY: PASS（四闸 approved） |

## 红线对拍

- **改码面收敛**：`tests/` 两枚闸文件 + task 档验收回填 + invoke 档；`app/` `alembic/` `scripts/` SSE/freeze **零 diff**（git 对拍实证）。
- **禁拆闸**：banned 前置 / 四态 / 回归牙零改动（三实证反证恒绿失效不存在）。
- **不修史**：`scripts/graph-compile.sh` / `alembic/versions/20261105_capability_notes.py` 他人合法合入零回退；`_BASE`/`_WAVE_TIP` 钉锚值不变。
- **闸表契约**：HG-DIFF-WHITELIST-DIAGNOSIS status 修复为**记录修复**（引据 GO 评论 + 签录 commit · 非自签）。

## 出货

- PR 待 lead 终审验收（issue #337 令）· 合并由维护者执行。
- 下一棒：40 复跑（worktree @ 30 出货 commit 独立复跑：两枚用例 2 passed + 全量零新增红 + 红线对拍 + 闸语义对拍复核）→ PR+CI 绿+merge → CLOSE（active→done 归档 · 四字段）。

## 环境注记

- 本机 venv 补装 `ruff`（requirements.txt 无 ruff · pyproject 已声明 · 承 30 档先例）。
- 演示三实证全部 sed 摘除→还原（零残留 · 还原后 grep 验证在册）。
